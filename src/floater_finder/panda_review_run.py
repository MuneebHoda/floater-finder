"""Bounded development analysis of new review signals, reusing committed predictions and S1 draws."""
import csv
import itertools
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
from .artifacts import Slide,TextEmbeddings,write_json
from .experiments import file_sha256
from .fragment_dependence import connected_pieces
from .panda import panda_readers
from .panda_stress import inject_development_s1
from .panda_topology import tissue_mask,overview_components,add_observed_tiles
from .panda_review import component_features,flagged_components,evaluate_flags,matched_draws,summarize,acceptable,wilson


def same_prediction(a,b):
    return a['prediction']==b['prediction'] and np.allclose([a['scores'][c] for c in ('benign','cancer')],[b['scores'][c] for c in ('benign','cancer')],atol=1e-7,rtol=1e-6)


def source_map(directories):
    result={}
    for d in map(Path,json.loads(Path(directories).read_text())):
        sid=json.loads((d/'metadata.json').read_text())['slide_id']
        if sid in result:raise ValueError('Duplicate tiling source')
        result[sid]=d
    return result


def load_sources(manifest,directories,encoded,verification,splits):
    receipt=json.loads(Path(verification).read_text())
    if file_sha256(manifest)!=receipt['manifest_sha256']:raise ValueError('Manifest hash differs')
    by_id={r['image_id']:r for r in receipt['records']};mapped=source_map(directories);sources={}
    with Path(manifest).open(newline='') as f:cohort=[r for r in csv.DictReader(f) if r['split'] in splits]
    for row in cohort:
        sid=row['image_id'];root=Path(encoded)/sid;d=mapped[sid]
        if file_sha256(root/'completion.json')!=by_id[sid]['completion_sha256']:raise ValueError('Changed embedding receipt')
        completion=json.loads((root/'completion.json').read_text())
        for name,digest in by_id[sid]['artifact_sha256'].items():
            if file_sha256(root/name)!=digest:raise ValueError('Changed embedding artifact')
        for name,key in [('tiles.csv','manifest_sha256'),('metadata.json','metadata_sha256')]:
            if file_sha256(d/name)!=completion['input_identity'][key]:raise ValueError('Changed tiling input')
        slide=Slide.load(root/'slide.npz');text=TextEmbeddings.load(root/'text.npz');m=slide.metadata
        if (m['source_kind']!='real' or m['project']!='PANDA' or m.get('data_provider')!='radboud' or m['slide_id']!=sid or
                m['cohort_split']!=row['split'] or m['isup_grade']!=int(row['isup_grade']) or
                m['extraction']['sampling_mode']!='representative' or m['extraction']['selection_uses_mask'] or
                text.fingerprint()!=receipt['text_fingerprint']):raise ValueError('Ineligible saved source')
        with (d/'tiles.csv').open(newline='') as f:rows=list(csv.DictReader(f))
        if slide.tile_ids.tolist()!=[r['tile_id'] for r in rows]:raise ValueError('Tile IDs differ')
        all_scores=np.einsum('id,cd->ic',slide.feats,text.feats,optimize=False)
        scores=all_scores[:,[text.classes.index(c) for c in ('benign','cancer')]]
        known=m['panda']['mask_available']
        cancer=[sum(float(r[f'gleason{g}_fraction']) for g in (3,4,5))>0 for r in rows] if known else [False]*len(rows)
        sources[sid]=dict(slide=slide,text=text,rows=rows,directory=d,completion=completion,scores=scores,
            annotation_known=[known]*len(rows),annotated_cancer=cancer,split=row['split'],host_truth='benign' if int(row['isup_grade'])==0 else 'cancer')
    return sources,receipt


def read_overview(source,config,acquisition_receipts,output):
    slide=source['slide'];meta=slide.metadata;path=Path(meta['panda']['input_files']['image']['path'])
    acquisition=json.loads((Path(acquisition_receipts)/(path.name+'.json')).read_text())
    image_sha=file_sha256(path)
    if image_sha!=acquisition['sha256']:raise ValueError('WSI differs from acquisition identity')
    with panda_readers(path,recorded_mpp_xy=meta['measured_mpp_xy']) as (image,_,header):
        level=config['pyramid_level'];dims=image.level_dimensions[level]
        if np.prod(dims)>config['maximum_pixels']:raise ValueError('Overview exceeds bound')
        rgba=image.read_region((0,0),level,dims)
        background=Image.new('RGBA',rgba.size,'white');background.alpha_composite(rgba);rgb=np.asarray(background.convert('RGB'))
        scale=np.array(header['measured_mpp_xy'])*image.level_downsamples[level]
    mask=tissue_mask(rgb,config['rgb_maximum'],config['minimum_chroma'])
    parts,quality=overview_components(mask,slide.coords,meta['tile_size'],scale,config['tile_component_purity'])
    sensitivity=tissue_mask(rgb,config['sensitivity_rgb_maximum'],config['sensitivity_minimum_chroma'])
    sensitive_parts,sensitive_quality=overview_components(sensitivity,slide.coords,meta['tile_size'],scale,config['tile_component_purity'])
    # Compare observed memberships without using cancer labels or predictions.
    assignment={i:p['component_id'] for p in parts for i in p['indices']};other={i:p['component_id'] for p in sensitive_parts for i in p['indices']}
    common=sorted(set(assignment)&set(other));agree=total=0
    for i,a in enumerate(common):
        for b in common[i+1:]:agree+=(assignment[a]==assignment[b])==(other[a]==other[b]);total+=1
    record=dict(image_id=meta['slide_id'],split=source['split'],image_sha256=image_sha,pyramid_level=level,
        overview_dimensions=list(dims),pixel_um=scale.tolist(),component_rule='observed RGB pixels; 8-connectivity; no morphology',
        old_sampled_components=len(connected_pieces(slide.coords,meta['tile_step'],0)),
        new_observed_components=len(parts),mapping_fraction=quality['mapping_fraction'],mapped_tiles=quality['mapped_tiles'],tiles=len(slide.feats),
        sensitive_components=len(sensitive_parts),sensitive_mapping_fraction=sensitive_quality['mapping_fraction'],
        sensitivity_pairwise_membership_agreement=agree/total if total else None,
        selected_primary_before_outcomes=True,physical_boundary_validation='RGB/pyramid proxy; not pathologist-verified')
    dest=Path(output)/meta['slide_id'];dest.mkdir(parents=True,exist_ok=False)
    preview=Image.fromarray(rgb);preview.thumbnail((900,900));preview.save(dest/'overview.png')
    edges=mask.copy();edges[1:]&=~mask[:-1];edges[:-1]|=mask[:-1]&~mask[1:]
    overlay=rgb.copy();overlay[edges]=[0,160,230];view=Image.fromarray(overlay);view.thumbnail((900,900));view.save(dest/'tissue_edges.png')
    write_json(dest/'topology.json',dict(record=record,components=parts,quality=quality))
    source.update(mask=mask,pixel_um=scale,components=parts,quality=quality,overview_record=record)
    return record


def case_record(case_id,source,slide,scores,parts,quality,kind,percent,clean_prediction,foreign_known=None,annotation_known=None,cancer=None):
    baseline,features=component_features(slide.feats,scores,parts)
    return dict(case_id=case_id,host_id=slide.metadata['slide_id'],split=source['split'],kind=kind,
        requested_percent=percent,host_truth=source['host_truth'],baseline=baseline,clean_prediction=clean_prediction,
        mapping_fraction=quality['mapping_fraction'],components=features,tile_scores=scores.tolist(),
        foreign_mask=slide.foreign_mask.tolist(),annotation_known=annotation_known if annotation_known is not None else source['annotation_known'],
        annotated_cancer=cancer if cancer is not None else source['annotated_cancer'])


def evaluate_rule(cases,rule):
    rows=[]
    for case in cases:
        row=evaluate_flags(case,flagged_components(case,rule));row.update({k:case[k] for k in ('case_id','host_id','split','kind','requested_percent')})
        rows.append(row)
    return rows,summarize(rows)


def choose_and_validate(cases,config):
    if any(c['split'] not in ('train','calibration') for c in cases):raise ValueError('Test cases are forbidden in review-policy selection')
    train=[c for c in cases if c['split']=='train'];cal=[c for c in cases if c['split']=='calibration']
    visual=[p['visual'] for c in train if c['kind']=='unmodified' and c['mapping_fraction']>=.9 for p in c['components'] if p['status']=='evaluable']
    if not visual:raise ValueError('No training visual reference distribution')
    quantiles={str(q):float(np.quantile(visual,q,method='higher')) for q in config['grid']['training_visual_quantiles']}
    grid=[]
    for q,influence,area,isolation in itertools.product(config['grid']['training_visual_quantiles'],config['grid']['influence'],config['grid']['maximum_observed_area_mm2'],config['grid']['minimum_isolation_bbox_lower_bound_mm']):
        rule=dict(kind='combined',visual_threshold=quantiles[str(q)],visual_quantile=q,influence=influence,max_area_mm2=area,min_isolation_mm=isolation)
        _,metrics=evaluate_rule(train,rule);grid.append(dict(rule=rule,train=metrics,burden_and_harm_pass=acceptable(metrics,config['budgets'])))
    candidates=[r for r in grid if r['burden_and_harm_pass']]
    def rank(r):
        m=r['train'];return (m['fragment_recall'] or 0,m['new_error_recovery_rate'] or 0,-(m['genuine_cancer_slide_flag_rate'] or 0),
            -m['unmodified_alert_rate'],-m['mean_components_per_unmodified_slide'],r['rule']['visual_threshold'],-r['rule']['max_area_mm2'],r['rule']['min_isolation_mm'])
    best=max(candidates or grid,key=rank);selected=best['rule'];comparison={};raw={}
    visual_candidates=[]
    for q,threshold in quantiles.items():
        rule=dict(kind='visual',visual_threshold=threshold,visual_quantile=float(q));_,m=evaluate_rule(train,rule)
        visual_candidates.append(dict(rule=rule,train=m,burden_and_harm_pass=acceptable(m,config['budgets'])))
    eligible=[r for r in visual_candidates if r['burden_and_harm_pass']]
    visual_rule=max(eligible or visual_candidates,key=lambda r:((r['train']['fragment_recall'] or 0),-r['train']['unmodified_alert_rate']))['rule']
    rules=dict(combined=selected,visual_only=visual_rule,decision_only=dict(kind='decision'),spatial_only=dict(kind='spatial',max_area_mm2=selected['max_area_mm2'],min_isolation_mm=selected['min_isolation_mm']))
    for name,rule in rules.items():
        raw[name]=[];comparison[name]=dict(rule=rule)
        for split,subset in [('train',train),('calibration',cal)]:
            rows,m=evaluate_rule(subset,rule);raw[name].extend(rows);comparison[name][split]=m
    controls={};control_rows=[];forced=[]
    for split,subset in [('train',train),('calibration',cal)]:
        draws=[[] for _ in range(config['matched_random_draws'])]
        for c in subset:
            flags=flagged_components(c,selected)
            for draw,indices in enumerate(matched_draws(c,flags,config['matched_random_draws'],config['seed'])):
                row=evaluate_flags(c,indices);row.update({k:c[k] for k in ('case_id','host_id','split','kind','requested_percent')});row['draw']=draw
                draws[draw].append(row);control_rows.append(row)
            pools=[sum(p['status']=='evaluable' and np.searchsorted([.05,.25,1.],p['observed_tissue_area_mm2'])==np.searchsorted([.05,.25,1.],c['components'][i]['observed_tissue_area_mm2']) for p in c['components']) for i in flags]
            forced.extend(n==1 for n in pools)
        metrics=[summarize(r) for r in draws];means={k:float(np.mean([m[k] for m in metrics if m[k] is not None])) if any(m[k] is not None for m in metrics) else None for k in metrics[0]}
        controls[split]=dict(mean=means,draws=metrics,independent_unit='host slide; random draws are repeated controls, not patients')
    gates={}
    for split in ('train','calibration'):
        m=comparison['combined'][split]
        gates[split]=dict(burden_and_harm_pass=acceptable(m,config['budgets']),
            nontrivial_recall=(m['fragment_recall'] or 0)>=config['minimum_useful_fragment_recall'],
            nontrivial_error_recovery=(m['new_error_recovery_rate'] or 0)>=config['minimum_useful_induced_error_recovery'])
    supported=all(all(g.values()) for g in gates.values())
    return dict(selected_rule=selected,training_visual_thresholds=quantiles,grid=grid,comparison=comparison,
        matched_random=controls,matched_control_forced_size_matches=int(sum(forced)),matched_control_components=len(forced),
        gates=gates,operating_point_supported=supported,selection_uses='training only; calibration validates one selected point without retuning'),raw,control_rows


def develop(manifest,directories,encoded,verification,stress,acquisition_receipts,config_path,baseline_path,output):
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Real development review requires CPU Slurm')
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve existing experiments; use fresh output')
    config=json.loads(Path(config_path).read_text())
    if config['splits']!=['train','calibration']:raise ValueError('Development split guard')
    sources,receipt=load_sources(manifest,directories,encoded,verification,config['splits'])
    if len(sources)!=96:raise ValueError('Expected exactly 96 development sources')
    baseline={(r['image_id']):r for r in json.loads(Path(baseline_path).read_text()) if r['task']=='benign_cancer' and r['pooling']=='top5pct'}
    output.mkdir(parents=True,exist_ok=False);cases=[];topology=[]
    for sid,s in sources.items():
        topology.append(read_overview(s,config['topology'],acquisition_receipts,output/'topology'))
        c=case_record(sid,s,s['slide'],s['scores'],s['components'],s['quality'],'unmodified',0,baseline[sid]['prediction'])
        if not same_prediction(c['baseline'],baseline[sid]):raise RuntimeError('Frozen scorer differs from committed baseline')
        cases.append(c);print(json.dumps(dict(stage='topology',image_id=sid,mapping=s['quality']['mapping_fraction'])),flush=True)
    trials=json.loads((Path(stress)/'trials.json').read_text());png_cache={}
    for trial in trials:
        if trial['requested_percent']==0:continue
        host=sources[trial['host_id']];donor=sources[trial['donor_id']]
        mixed=inject_development_s1(host['slide'],donor['slide'],np.array(trial['donor_indices']),trial['requested_percent'],20261020)
        n=len(host['slide'].feats);tile_rgbs=[]
        for index in trial['donor_indices']:
            row=donor['rows'][index];key=(trial['donor_id'],row['tile_id'])
            if key not in png_cache:
                p=donor['directory']/row['path']
                if p.resolve().parent!=donor['directory'].resolve() or file_sha256(p)!=donor['completion']['input_identity']['png_sha256'][row['tile_id']]:raise ValueError('Changed donor RGB export')
                with Image.open(p) as image:png_cache[key]=np.asarray(image.convert('RGB'))
            tile_rgbs.append(png_cache[key])
        topo=config['topology'];mask=add_observed_tiles(host['mask'],mixed.coords[n:],mixed.metadata['tile_size'],host['pixel_um'],tile_rgbs,topo['rgb_maximum'],topo['minimum_chroma'])
        parts,quality=overview_components(mask,mixed.coords,mixed.metadata['tile_size'],host['pixel_um'],topo['tile_component_purity'])
        scores=np.concatenate([host['scores'],donor['scores'][trial['donor_indices']]])
        known=host['annotation_known']+[donor['annotation_known'][i] for i in trial['donor_indices']]
        cancer=host['annotated_cancer']+[donor['annotated_cancer'][i] for i in trial['donor_indices']]
        c=case_record(trial['host_id']+'-p'+str(trial['requested_percent']),host,mixed,scores,parts,quality,'synthetic',trial['requested_percent'],trial['baseline']['top5pct']['prediction'],annotation_known=known,cancer=cancer)
        c['donor_id']=trial['donor_id']
        if not same_prediction(c['baseline'],trial['contaminated']['top5pct']):raise RuntimeError('Existing S1 prediction differs; do not change draws')
        cases.append(c)
    if len(cases)!=256:raise ValueError('Expected 96 unmodified + 160 existing positive-dose mixtures')
    write_json(output/'component_cases.json',cases);write_json(output/'topology_audit.json',topology)
    selection,raw,controls=choose_and_validate(cases,config)
    selection.update(source_kind='real',slurm_job_id=os.environ['SLURM_JOB_ID'],config_sha256=file_sha256(config_path),
        manifest_sha256=receipt['manifest_sha256'],text_fingerprint=receipt['text_fingerprint'],
        source_baseline_sha256=file_sha256(baseline_path),source_stress_trials_sha256=file_sha256(Path(stress)/'trials.json'),
        cases=len(cases),test_slides_scored=False,patient_independence_verified=False,clinical_validity_verified=False,
        automatic_tissue_action='none; review only',component_cases_sha256=file_sha256(output/'component_cases.json'))
    write_json(output/'selection.json',selection);write_json(output/'metrics_by_case.json',raw);write_json(output/'matched_controls_by_case.json',controls)
    print(json.dumps(dict(operating_point_supported=selection['operating_point_supported'],gates=selection['gates'])),flush=True)
    return selection
