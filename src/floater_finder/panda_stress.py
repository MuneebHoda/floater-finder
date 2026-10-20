"""Development-only PANDA S1 stress tests using already verified, saved embeddings."""
from collections import deque
from copy import deepcopy
from decimal import Decimal, ROUND_CEILING
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from .artifacts import Slide, TextEmbeddings, check_compatible, write_json
from .experiments import file_sha256
from .injection import connected_fragment, grid_neighbors, verify_oracle
from .scoring import POOLING, pool, tile_scores


def foreign_count(percent, host_tiles):
    if not np.isfinite(percent) or not 0 <= percent <= 10 or host_tiles < 1:
        raise ValueError('Bounded percent and original host size required')
    return int((Decimal(str(percent))*host_tiles/100).to_integral_value(rounding=ROUND_CEILING))


def cancer_components(slide, rows, minimum_fraction):
    if not 0 < minimum_fraction <= 1 or len(rows)!=len(slide.feats):
        raise ValueError('Aligned tile rows and a positive cancer-fraction cutoff required')
    if [r['tile_id'] for r in rows]!=slide.tile_ids.tolist():
        raise ValueError('Tile labels must align with saved embedding IDs')
    if not slide.metadata['panda']['mask_available']:
        return []
    fractions=np.array([[float(r[f'gleason{g}_fraction']) for g in (3,4,5)] for r in rows])
    if not np.isfinite(fractions).all() or (fractions<0).any() or (fractions.sum(axis=1)>1+1e-10).any():
        raise ValueError('Invalid native-mask cancer fractions')
    neighbors=grid_neighbors(slide);remaining=set(np.flatnonzero(fractions.sum(axis=1)>=minimum_fraction).tolist())
    components=[]
    while remaining:
        start=min(remaining);remaining.remove(start);queue=deque([start]);members=[]
        while queue:
            node=queue.popleft();members.append(node)
            for other in neighbors[node]:
                if other in remaining:remaining.remove(other);queue.append(other)
        components.append(np.array(sorted(members),dtype=int))
    return sorted(components,key=lambda a:(-len(a),a[0]))


def inject_development_s1(host, donor, indices, percent, seed):
    if type(seed) is not int or seed<0:raise ValueError('Nonnegative integer seed required')
    check_compatible(host,donor)
    h,d=host.metadata,donor.metadata
    if (h['project']!='PANDA' or d['project']!='PANDA' or h['data_provider']!='radboud' or d['data_provider']!='radboud' or
            h['slide_id']==d['slide_id'] or h['cohort_split'] not in ('train','calibration') or
            h['cohort_split']!=d['cohort_split'] or h['isup_grade']!=0 or d['isup_grade'] not in (1,4,5)):
        raise ValueError('S1 requires distinct Radboud benign/cancer slides in the same development split')
    if (h.get('patient_id_known') and d.get('patient_id_known') and h['patient_id']==d['patient_id']):
        raise ValueError('Known same-patient pairs are ineligible')
    if any(s.foreign_mask.any() or 'injection' in s.metadata for s in (host,donor)):
        raise ValueError('Original unmodified inputs required')
    for key in ('coordinate_units','microns_per_unit','tile_step','tile_size'):
        if h.get(key) is None or h.get(key)!=d.get(key):raise ValueError('Host/donor physical geometry differs')
    count=foreign_count(percent,len(host.feats));indices=np.asarray(indices)
    if (indices.ndim!=1 or indices.dtype.kind not in 'iu' or len(indices)!=count or len(set(indices.tolist()))!=count or
            (indices<0).any() or (indices>=len(donor.feats)).any()):
        raise ValueError('Distinct donor indices must match the requested count')
    if count:
        selected=set(indices.tolist());neighbors=grid_neighbors(donor);seen={int(indices[0])};queue=deque(seen)
        while queue:
            for other in neighbors[queue.popleft()]:
                if other in selected and other not in seen:seen.add(other);queue.append(other)
        if seen!=selected:raise ValueError('Donor fragment is not four-connected')
    grid_neighbors(host)
    metadata=deepcopy(h)
    step=np.asarray(h['tile_step']);coords=donor.coords[indices].copy();translation=np.zeros(2)
    if count:
        y=h_origin=host.coords[:,1].min()
        y+=np.rint((np.median(host.coords[:,1])-h_origin)/step[1])*step[1]
        anchor=np.array([host.coords[:,0].max()+3*step[0],y])
        translation=anchor-coords.min(axis=0);coords+=translation
    metadata['injection']=dict(kind='synthetic_PANDA_S1_embedding_contamination',seed=seed,
        requested_percent=float(percent),realized_percent=100*count/len(host.feats),foreign_count=count,
        original_host_count=len(host.feats),rounding='ceil(percent * original_host_count / 100)',
        donor_slide_id=d['slide_id'],donor_patient_id=d['patient_id'],patient_independence_verified=False,
        donor_indices=indices.tolist(),donor_tile_ids=donor.tile_ids[indices].tolist(),translation_um=translation.tolist(),
        placement='three x-grid steps beyond host right edge; y rounded to host grid',host_metadata=deepcopy(h))
    return Slide(np.concatenate([host.feats,donor.feats[indices]]),np.concatenate([host.coords,coords]),
        np.concatenate([host.tile_ids,np.array([f"{d['slide_id']}::{t}" for t in donor.tile_ids[indices]])]),metadata,
        np.concatenate([host.foreign_mask,np.ones(count,dtype=bool)]))


def binary_predictions(slide,text):
    classes=('benign','cancer');scores=tile_scores(slide,text)[:,[text.classes.index(c) for c in classes]]
    result={}
    for rule in POOLING:
        values=pool(scores,rule)
        result[rule]=dict(prediction=classes[int(np.argmax(values))],scores=dict(zip(classes,values.tolist())))
    return result


def run(manifest,directories,encoded_root,verification,protocol,output):
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Real PANDA stress tests require bounded CPU Slurm')
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve previous results; choose a fresh output')
    config=json.loads(Path(protocol).read_text());verified=json.loads(Path(verification).read_text())
    if config['splits']!=['train','calibration'] or verified['manifest_sha256']!=file_sha256(manifest):
        raise ValueError('Frozen development protocol and verified manifest required')
    with Path(manifest).open(newline='') as f:cohort=list(csv.DictReader(f))
    if len(cohort) not in (60,120) or len({r['image_id'] for r in cohort})!=len(cohort):raise ValueError('Fixed cohort required')
    by_id={r['image_id']:r for r in cohort};receipts={r['image_id']:r for r in verified['records']}
    mapped={}
    for directory in map(Path,json.loads(Path(directories).read_text())):
        sid=json.loads((directory/'metadata.json').read_text())['slide_id']
        if sid in mapped:raise ValueError('Duplicate tiling source')
        mapped[sid]=directory
    if set(mapped)!=set(by_id) or set(receipts)!=set(by_id):raise ValueError('Exact verified cohort membership required')
    slides={};labels={};components={};audit=[];text=None;inputs={}
    for row in cohort:
        if row['split'] not in config['splits']:continue
        sid=row['image_id'];root=Path(encoded_root)/sid;directory=mapped[sid]
        if file_sha256(root/'completion.json')!=receipts[sid]['completion_sha256']:raise ValueError('Changed embedding receipt')
        completion=json.loads((root/'completion.json').read_text())
        for name,digest in receipts[sid]['artifact_sha256'].items():
            if file_sha256(root/name)!=digest:raise ValueError('Changed verified embedding artifact')
        for name,key in [('tiles.csv','manifest_sha256'),('metadata.json','metadata_sha256')]:
            if file_sha256(directory/name)!=completion['input_identity'][key]:raise ValueError('Changed tiling label provenance')
        slide=Slide.load(root/'slide.npz');current=TextEmbeddings.load(root/'text.npz');m=slide.metadata
        if (m['source_kind']!='real' or m['project']!='PANDA' or m['data_provider']!='radboud' or
                m['slide_id']!=sid or m['cohort_split']!=row['split'] or m['isup_grade']!=int(row['isup_grade']) or
                m['extraction']['sampling_mode']!='representative' or m['extraction']['selection_uses_mask'] or
                current.fingerprint()!=verified['text_fingerprint']):raise ValueError('Ineligible clean artifact/split/model')
        check_compatible(slide,current);text=current
        with (directory/'tiles.csv').open(newline='') as f:rows=list(csv.DictReader(f))
        if len(rows)!=len(slide.feats) or not np.array_equal(slide.coords,[[float(r['x']),float(r['y'])] for r in rows]):
            raise ValueError('Saved coordinates differ from mask-labelled tile rows')
        slides[sid]=slide;labels[sid]=rows
        inputs[sid]=dict(completion_sha256=receipts[sid]['completion_sha256'],tile_manifest_sha256=file_sha256(directory/'tiles.csv'))
        if m['isup_grade']>0:
            components[sid]=cancer_components(slide,rows,config['minimum_total_cancer_fraction'])
            audit.append(dict(image_id=sid,split=row['split'],mask_available=m['panda']['mask_available'],
                eligible_tiles=sum(map(len,components[sid])),largest_four_connected_component=len(components[sid][0]) if components[sid] else 0))
    trials=[];exclusions=[];pairings=[];seed=config['seed']
    for sid,host in slides.items():
        if host.metadata['isup_grade']!=0:continue
        split=host.metadata['cohort_split'];needed=foreign_count(max(config['percentages']),len(host.feats))
        candidates=[]
        for did,parts in components.items():
            if not parts or slides[did].metadata['cohort_split']!=split:continue
            if any(host.metadata[k]!=slides[did].metadata[k] for k in ('coordinate_units','microns_per_unit','tile_step','tile_size')):continue
            capacity=len(parts[0]);order=hashlib.sha256(f'{seed}/{sid}/{did}'.encode()).hexdigest()
            candidates.append((capacity<needed,0 if capacity>=needed else -capacity,order,did))
        if not candidates:
            exclusions.append(dict(host_id=sid,split=split,reason='No eligible same-split annotated cancer-rich donor component'));continue
        did=min(candidates)[3];donor=slides[did];component=components[did][0]
        order=component[connected_fragment(donor.subset(component),min(needed,len(component)),seed)]
        baseline=binary_predictions(host,text)
        pairings.append(dict(host_id=sid,donor_id=did,split=split,donor_component_capacity=len(component),required_for_ten_percent=needed))
        for percent in config['percentages']:
            count=foreign_count(percent,len(host.feats))
            if count>len(order):
                exclusions.append(dict(host_id=sid,donor_id=did,split=split,requested_percent=percent,
                    requested_count=count,capacity=len(order),reason='Fixed connected donor has insufficient unique tiles'));continue
            indices=order[:count];mixed=inject_development_s1(host,donor,indices,percent,seed)
            restored=verify_oracle(host,mixed,text);oracle=binary_predictions(restored,text)
            if oracle!=baseline:raise RuntimeError('Oracle failed binary score/prediction recovery; stop experiment')
            cancer_area=sum(float(labels[did][i]['area_mm2'])*sum(float(labels[did][i][f'gleason{g}_fraction']) for g in (3,4,5)) for i in indices)
            trials.append(dict(host_id=sid,donor_id=did,split=split,requested_percent=percent,
                realized_percent=100*count/len(host.feats),host_tiles=len(host.feats),foreign_tiles=count,
                donor_indices=indices.tolist(),donor_tile_ids=donor.tile_ids[indices].tolist(),
                foreign_footprint_area_mm2=float(count*np.prod(donor.metadata['tile_size'])/1e6),
                annotated_cancer_area_mm2=cancer_area,baseline=baseline,contaminated=binary_predictions(mixed,text),
                oracle=oracle,oracle_exact_recovery=True,
                synthetic_injection={k:v for k,v in mixed.metadata['injection'].items() if k!='host_metadata'}))
    summary=[]
    for split in config['splits']:
        for percent in config['percentages']:
            subset=[r for r in trials if r['split']==split and r['requested_percent']==percent]
            for rule in POOLING:
                n=len(subset)
                summary.append(dict(split=split,requested_percent=percent,pooling=rule,hosts=n,
                    clean_benign_correct=sum(r['baseline'][rule]['prediction']=='benign' for r in subset),
                    clean_host_accuracy=sum(r['baseline'][rule]['prediction']=='benign' for r in subset)/n if n else None,
                    contaminated_host_accuracy=sum(r['contaminated'][rule]['prediction']=='benign' for r in subset)/n if n else None,
                    prediction_changes=sum(r['baseline'][rule]['prediction']!=r['contaminated'][rule]['prediction'] for r in subset),
                    mixture_cancer_response=sum(r['contaminated'][rule]['prediction']=='cancer' for r in subset)/n if n and percent else None,
                    oracle_passes=sum(r['oracle_exact_recovery'] for r in subset)))
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'donor_audit.json',audit);write_json(output/'pairings.json',pairings)
    write_json(output/'trials.json',trials);write_json(output/'exclusions.json',exclusions)
    write_json(output/'summary.json',dict(source_kind='real',category='PANDA S1 development synthetic embedding stress; no detector',
        slurm_job_id=os.environ['SLURM_JOB_ID'],protocol=config,protocol_sha256=file_sha256(protocol),
        manifest_sha256=file_sha256(manifest),verification_sha256=file_sha256(verification),input_sha256=inputs,
        text_fingerprint=verified['text_fingerprint'],trials=len(trials),excluded=len(exclusions),
        distinct_host_slides=len({r['host_id'] for r in trials}),distinct_donor_slides=len({r['donor_id'] for r in trials}),
        planned_host_slides=sum(s.metadata['isup_grade']==0 for s in slides.values()),
        patient_independence_verified=False,test_slides_scored=False,clinical_validity_verified=False,
        full_biopsy_piece_topology_verified=False,detector_evaluated=False,alert_rate_evaluated=False,metrics=summary))
    return dict(trials=len(trials),exclusions=len(exclusions),hosts=len(pairings),oracle_passes=sum(r['oracle_exact_recovery'] for r in trials))
