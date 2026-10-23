"""Versioned development-only S2 stress; native annotations select donors, never score tissue."""
from collections import deque
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from .artifacts import Slide, check_compatible, write_json
from .experiments import file_sha256
from .injection import connected_fragment, grid_neighbors, verify_oracle
from .panda_review_run import load_sources
from .panda_stress import foreign_count
from .scoring import POOLING, pool, tile_scores

CLASSES = ('low_grade', 'high_grade')
CONDITIONS = ('high_gp45', 'same_grade_gp3_only', 'high_gp4_only', 'high_gp5_positive')


def predictions(slide, text):
    values = tile_scores(slide, text)[:, [text.classes.index(c) for c in CLASSES]]
    result = {}
    for rule in POOLING:
        scores = pool(values, rule)
        result[rule] = dict(prediction=CLASSES[int(np.argmax(scores))], scores=dict(zip(CLASSES, scores.tolist())),
                            high_minus_low_margin=float(scores[1]-scores[0]))
    return result


def pattern_components(slide, rows, condition, minimum=.1):
    if condition not in CONDITIONS or not 0 < minimum <= 1:
        raise ValueError('Known condition and positive fraction required')
    if [r['tile_id'] for r in rows] != slide.tile_ids.tolist():
        raise ValueError('Native label rows must align with embedding tile IDs')
    if not slide.metadata['panda']['mask_available']:
        return []
    a = np.array([[float(r[f'gleason{g}_fraction']) for g in (3,4,5)] for r in rows])
    if not np.isfinite(a).all() or (a<0).any() or (a.sum(axis=1)>1+1e-10).any():
        raise ValueError('Invalid native Gleason fractions')
    grade = slide.metadata['isup_grade']
    allowed = ((a[:,1]+a[:,2]>=minimum) if condition=='high_gp45' else
               ((a[:,0]>=minimum)&(a[:,1]==0)&(a[:,2]==0)) if condition=='same_grade_gp3_only' else
               ((a[:,1]>=minimum)&(a[:,2]==0)) if condition=='high_gp4_only' else (a[:,2]>=minimum))
    if (condition=='same_grade_gp3_only' and grade!=1) or (condition!='same_grade_gp3_only' and grade not in (4,5)):
        return []
    neighbors=grid_neighbors(slide); remaining=set(np.flatnonzero(allowed).tolist()); parts=[]
    while remaining:
        start=min(remaining);remaining.remove(start);queue=deque([start]);members=[]
        while queue:
            i=queue.popleft();members.append(i)
            for j in neighbors[i]:
                if j in remaining:remaining.remove(j);queue.append(j)
        parts.append(np.array(sorted(members), dtype=int))
    return sorted(parts,key=lambda p:(-len(p),int(p[0])))


def eligible_pair(host, donor):
    h,d=host.metadata,donor.metadata
    return (h['slide_id']!=d['slide_id'] and h['cohort_split']==d['cohort_split'] and
            not (h.get('patient_id_known') and d.get('patient_id_known') and h['patient_id']==d['patient_id']) and
            all(h.get(k) is not None and h.get(k)==d.get(k) for k in ('coordinate_units','microns_per_unit','tile_step','tile_size')))


def inject(host, donor, indices, percent, seed, condition):
    check_compatible(host, donor)
    h,d=host.metadata,donor.metadata
    if (condition not in CONDITIONS or type(seed) is not int or seed<0 or not eligible_pair(host,donor) or
        any(m['project']!='PANDA' or m['data_provider']!='radboud' or m['cohort_split'] not in ('train','calibration') for m in (h,d)) or
        h['isup_grade']!=1 or (d['isup_grade']!=1 if condition=='same_grade_gp3_only' else d['isup_grade'] not in (4,5))):
        raise ValueError('S2 requires eligible distinct Radboud low-grade host and condition-specific donor in same development split')
    if any(s.foreign_mask.any() or 'injection' in s.metadata for s in (host,donor)):
        raise ValueError('Original unmodified inputs required')
    count=foreign_count(percent,len(host.feats));indices=np.asarray(indices)
    if (indices.ndim!=1 or indices.dtype.kind not in 'iu' or len(indices)!=count or len(set(indices.tolist()))!=count or
        (indices<0).any() or (indices>=len(donor.feats)).any()):
        raise ValueError('Unique donor indices must match requested dose')
    if count:
        selected=set(indices.tolist());seen={int(indices[0])};queue=deque(seen);neighbors=grid_neighbors(donor)
        while queue:
            for j in neighbors[queue.popleft()]:
                if j in selected and j not in seen:seen.add(j);queue.append(j)
        if seen!=selected:raise ValueError('Donor fragment must be four-connected')
    grid_neighbors(host); coords=donor.coords[indices].copy();translation=np.zeros(2);step=np.asarray(h['tile_step'])
    if count:
        origin=host.coords[:,1].min(); y=origin+np.rint((np.median(host.coords[:,1])-origin)/step[1])*step[1]
        translation=np.array([host.coords[:,0].max()+3*step[0],y])-coords.min(axis=0);coords+=translation
    metadata=deepcopy(h)
    metadata['injection']=dict(kind='synthetic_PANDA_S2_embedding_contamination',condition=condition,seed=seed,
        requested_percent=float(percent),realized_percent=100*count/len(host.feats),foreign_count=count,
        original_host_count=len(host.feats),rounding='ceil(percent * original_host_count / 100)',donor_slide_id=d['slide_id'],
        donor_patient_id=d['patient_id'],patient_independence_verified=False,donor_indices=indices.tolist(),
        donor_tile_ids=donor.tile_ids[indices].tolist(),translation_um=translation.tolist(),
        placement='three x-grid steps beyond host right edge; y rounded to host grid',host_metadata=deepcopy(h))
    return Slide(np.concatenate([host.feats,donor.feats[indices]]),np.concatenate([host.coords,coords]),
        np.concatenate([host.tile_ids,np.array([f"{d['slide_id']}::{t}" for t in donor.tile_ids[indices]],dtype=str)]),
        metadata,np.concatenate([host.foreign_mask,np.ones(count,dtype=bool)]))


def visual_distance(query, reference):
    """Same median top-five nearest-neighbor distance, without labels or donor identity as features."""
    if not len(query) or not len(reference):return None
    distances=1-np.einsum('id,jd->ij',query,reference,optimize=False)
    k=min(5,len(reference))
    return float(np.median(np.partition(distances,k-1,axis=1)[:,:k].mean(axis=1)))


def summarize(trials):
    result=[]
    for split in ('train','calibration'):
        for condition in CONDITIONS:
            for percent in (0,.5,1,2,5,10):
                subset=[r for r in trials if (r['split'],r['condition'],r['requested_percent'])==(split,condition,percent)]
                for pooling in POOLING:
                    correct=[r for r in subset if r['baseline'][pooling]['prediction']=='low_grade']
                    initially_wrong=len(subset)-len(correct)
                    induced=sum(r['contaminated'][pooling]['prediction']=='high_grade' for r in correct)
                    result.append(dict(split=split,condition=condition,requested_percent=percent,pooling=pooling,
                        hosts=len(subset),originally_correct_low_hosts=len(correct),initially_high_hosts=initially_wrong,
                        newly_induced_low_to_high_errors=induced,new_error_rate=induced/len(correct) if correct else None,
                        prediction_changes=sum(r['baseline'][pooling]['prediction']!=r['contaminated'][pooling]['prediction'] for r in subset),
                        high_to_low_reversals=sum(r['baseline'][pooling]['prediction']=='high_grade' and r['contaminated'][pooling]['prediction']=='low_grade' for r in subset),
                        mean_high_minus_low_margin_change=float(np.mean([r['contaminated'][pooling]['high_minus_low_margin']-r['baseline'][pooling]['high_minus_low_margin'] for r in subset])) if subset else None,
                        oracle_exact_passes=sum(r['oracle_exact_recovery'] for r in subset)))
    return result


def run(manifest, directories, encoded, verification, protocol, baseline_path, output):
    if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('S2 requires bounded CPU Slurm, no GPU')
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve previous experiments; fresh output required')
    config=json.loads(Path(protocol).read_text())
    if config['splits']!=['train','calibration'] or config['primary_pooling']!='mean' or config['conditions']!=list(CONDITIONS) or config['percentages']!=[0,.5,1,2,5,10]:
        raise ValueError('Fixed S2 development protocol required')
    sources,receipt=load_sources(manifest,directories,encoded,verification,('train','calibration'))
    sources={k:v for k,v in sources.items() if v['slide'].metadata['isup_grade'] in (1,4,5)}
    existing=json.loads(Path(baseline_path).read_text())
    existing={(r['image_id'],r['pooling']):r for r in existing if r['task']=='low_high'}
    clean={};components={};audit=[];input_sha={}
    for sid,source in sources.items():
        slide=source['slide'];clean[sid]=predictions(slide,source['text'])
        for pooling,pred in clean[sid].items():
            prior=existing[(sid,pooling)]
            if pred['prediction']!=prior['prediction'] or pred['scores']!=prior['scores']:
                raise RuntimeError('Existing frozen low/high baseline does not recover exactly')
        input_sha[sid]=dict(completion_sha256=file_sha256(Path(encoded)/sid/'completion.json'),tile_manifest_sha256=file_sha256(source['directory']/'tiles.csv'))
        for condition in CONDITIONS:
            parts=pattern_components(slide,source['rows'],condition,config['minimum_pattern_fraction'])
            components[(sid,condition)]=parts
            audit.append(dict(image_id=sid,split=source['split'],isup_grade=slide.metadata['isup_grade'],condition=condition,
                mask_available=slide.metadata['panda']['mask_available'],eligible_tiles=sum(map(len,parts)),
                four_connected_components=len(parts),largest_capacity=len(parts[0]) if parts else 0))
    # This file is persisted before the first contaminated prediction, with the already selected scorer.
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'clean_audit.json',dict(primary_pooling='mean',selected_before_contaminated_predictions=True,
        clean=clean,protocol_sha256=file_sha256(protocol),prior_predictions_sha256=file_sha256(baseline_path),
        test_slides_scored=False))
    trials=[];pairings=[];exclusions=[];seed=config['seed']
    for sid,source in sources.items():
        host=source['slide']
        if host.metadata['isup_grade']!=1:continue
        needed=foreign_count(10,len(host.feats));split=source['split']
        for condition in CONDITIONS:
            candidates=[]
            for did,ds in sources.items():
                parts=components[(did,condition)]
                if not parts or not eligible_pair(host,ds['slide']):continue
                capacity=len(parts[0]);order=hashlib.sha256(f'{seed}/{sid}/{condition}/{did}'.encode()).hexdigest()
                candidates.append((capacity<needed,0 if capacity>=needed else -capacity,order,did))
            if not candidates:
                exclusions.append(dict(host_id=sid,split=split,condition=condition,reason='No eligible same-split verified native-pattern donor component'));continue
            did=min(candidates)[3];donor=sources[did]['slide'];part=components[(did,condition)][0]
            order=part[connected_fragment(donor.subset(part),min(needed,len(part)),seed)]
            pairings.append(dict(host_id=sid,donor_id=did,split=split,condition=condition,donor_component_capacity=len(part),required_for_ten_percent=needed))
            for percent in config['percentages']:
                count=foreign_count(percent,len(host.feats))
                if count>len(order):
                    exclusions.append(dict(host_id=sid,donor_id=did,split=split,condition=condition,requested_percent=percent,requested_count=count,capacity=len(order),reason='Fixed donor lacks unique four-connected capacity'));continue
                indices=order[:count];mixed=inject(host,donor,indices,percent,seed,condition)
                restored=verify_oracle(host,mixed,source['text']);oracle=predictions(restored,source['text'])
                if oracle!=clean[sid]:raise RuntimeError('S2 exact low/high oracle failure; stop experiment')
                rows=[sources[did]['rows'][i] for i in indices]
                fractions={str(g):[float(r[f'gleason{g}_fraction']) for r in rows] for g in (3,4,5)}
                outside=np.ones(len(donor.feats),bool);outside[indices]=False
                trials.append(dict(host_id=sid,donor_id=did,split=split,condition=condition,requested_percent=percent,
                    realized_percent=100*count/len(host.feats),host_tiles=len(host.feats),foreign_tiles=count,
                    donor_indices=indices.tolist(),donor_tile_ids=donor.tile_ids[indices].tolist(),native_pattern_fractions=fractions,
                    foreign_footprint_area_mm2=float(count*np.prod(donor.metadata['tile_size'])/1e6),
                    annotated_pattern_area_mm2={str(g):sum(float(r['area_mm2'])*float(r[f'gleason{g}_fraction']) for r in rows) for g in (3,4,5)},
                    baseline=clean[sid],contaminated=predictions(mixed,source['text']),oracle=oracle,oracle_exact_recovery=True,
                    visual_distance_to_host=visual_distance(donor.feats[indices],host.feats),
                    visual_distance_to_native_donor_context=visual_distance(donor.feats[indices],donor.feats[outside]),
                    synthetic_injection={k:v for k,v in mixed.metadata['injection'].items() if k!='host_metadata'}))
    native=[]
    for sid,source in sources.items():
        slide=source['slide']
        if slide.metadata['isup_grade'] not in (4,5):continue
        for number,part in enumerate(components[(sid,'high_gp45')]):
            keep=np.ones(len(slide.feats),bool);keep[part]=False
            counter=predictions(slide.subset(keep),source['text']) if keep.any() else None
            native.append(dict(image_id=sid,split=source['split'],component=number,tile_indices=part.tolist(),tiles=len(part),
                footprint_area_mm2=float(len(part)*np.prod(slide.metadata['tile_size'])/1e6),baseline=clean[sid],counterfactual=counter,
                visual_distance_to_native_context=visual_distance(slide.feats[part],slide.feats[keep]),
                genuine_annotated_tissue=True,foreignness_claim=False,empty_counterfactual=not bool(keep.any())))
    write_json(output/'trials.json',trials);write_json(output/'donor_audit.json',audit)
    write_json(output/'pairings.json',pairings);write_json(output/'exclusions.json',exclusions)
    write_json(output/'native_safety.json',native)
    summary=dict(source_kind='real',category=config['category'],protocol=config,protocol_sha256=file_sha256(protocol),
        source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'),slurm_job_id=os.environ['SLURM_JOB_ID'],
        manifest_sha256=file_sha256(manifest),verification_sha256=file_sha256(verification),input_sha256=input_sha,
        text_fingerprint=receipt['text_fingerprint'],trials=len(trials),positive_mixtures=sum(r['requested_percent']>0 for r in trials),
        exclusions=len(exclusions),distinct_host_slides=len({r['host_id'] for r in trials}),distinct_donor_slides=len({r['donor_id'] for r in trials}),
        patient_independence_verified=False,test_slides_scored=False,clinical_validity_verified=False,primary_pooling='mean',
        oracle_exact_passes=sum(r['oracle_exact_recovery'] for r in trials),metrics=summarize(trials))
    write_json(output/'summary.json',summary)
    write_json(output/'completion.json',dict(source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'),files={p.name:file_sha256(p) for p in output.iterdir() if p.is_file()}))
    return dict(trials=len(trials),exclusions=len(exclusions),oracle_exact_passes=summary['oracle_exact_passes'])
