"""Single, explicitly gated held-out CPU evaluation. Never called by development or preflight."""
import csv
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
from .artifacts import write_json
from .experiments import file_sha256
from .injection import connected_fragment,verify_oracle
from .panda_stress import _inject_s1,cancer_components,foreign_count
from .panda_topology import add_observed_tiles,overview_components
from .panda_review import flagged_components,evaluate_flags,matched_draws,summarize,wilson
from .panda_review_run import load_sources,read_overview,case_record
from .panda_final import preflight,require_execution,classification_summary,clustered_ratio_interval


def evaluate_final(protocol_path,expected_sha256,source_root,execute_final=False):
    if file_sha256(protocol_path)!=expected_sha256:raise ValueError('Frozen protocol checksum differs')
    protocol=json.loads(Path(protocol_path).read_text());require_execution(protocol,execute_final)
    if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):raise RuntimeError('Explicit CPU-only Slurm allocation required')
    checked=preflight(protocol_path,expected_sha256,source_root)
    if not checked['ready_for_final_predictions']:raise RuntimeError('Final readiness gate failed')
    data=protocol['data'];target=Path(protocol['execution']['output'])
    target.mkdir(exist_ok=False)  # Atomic single-execution lock, before held-out labels/arrays are loaded.
    write_json(target/'execution_lock.json',dict(protocol_sha256=expected_sha256,source_commit=protocol['source']['commit'],slurm_job_id=os.environ['SLURM_JOB_ID'],single_execution=True))
    config=protocol['development_config'];sources,receipt=load_sources(data['manifest'],data['directories'],data['encoded_root'],data['verification'],['test'])
    if set(sources)!=set(protocol['test_ids']):raise ValueError('Frozen 24-slide membership differs')
    cases=[];clean={};topology=[];classifier=[]
    for sid,s in sorted(sources.items()):
        topology.append(read_overview(s,config['topology'],data['acquisition_receipts'],target/'topology'))
        from .panda_review import prediction
        baseline=prediction(s['scores'])
        c=case_record(sid,s,s['slide'],s['scores'],s['components'],s['quality'],'unmodified',0,baseline['prediction'])
        c['split']='test';cases.append(c);clean[sid]=c
        classifier.append(dict(image_id=sid,truth=s['host_truth'],prediction=baseline['prediction'],scores=baseline['scores']))
    donor_parts={sid:cancer_components(s['slide'],s['rows'],protocol['contamination']['minimum_total_cancer_fraction']) for sid,s in sources.items() if s['host_truth']=='cancer'}
    trials=[];exclusions=[];oracle_passes=0;png_cache={};seed=protocol['contamination']['seed']
    for sid,host in sorted(sources.items()):
        if host['host_truth']!='benign':continue
        needed=foreign_count(max(protocol['contamination']['percentages']),len(host['slide'].feats));candidates=[]
        for did,parts in donor_parts.items():
            if not parts or did==sid:continue
            if any(host['slide'].metadata[k]!=sources[did]['slide'].metadata[k] for k in ('coordinate_units','microns_per_unit','tile_step','tile_size')):continue
            capacity=len(parts[0]);order=hashlib.sha256(f'{seed}/{sid}/{did}'.encode()).hexdigest()
            candidates.append((capacity<needed,0 if capacity>=needed else -capacity,order,did))
        if not candidates:
            exclusions.append(dict(host_id=sid,reason='No eligible distinct-slide same-provider donor component'));continue
        did=min(candidates)[3];donor=sources[did];component=donor_parts[did][0]
        order=component[connected_fragment(donor['slide'].subset(component),min(needed,len(component)),seed)]
        for percent in protocol['contamination']['percentages']:
            count=foreign_count(percent,len(host['slide'].feats))
            if count>len(order):
                exclusions.append(dict(host_id=sid,donor_id=did,requested_percent=percent,requested_count=count,capacity=len(order),reason='Insufficient fixed connected donor capacity'));continue
            if not count:
                trials.append(dict(host_id=sid,donor_id=did,requested_percent=0,realized_percent=0,foreign_tiles=0,baseline=clean[sid]['baseline'],contaminated=clean[sid]['baseline'],oracle=clean[sid]['baseline']));continue
            indices=order[:count];mixed=_inject_s1(host['slide'],donor['slide'],indices,percent,seed,allowed_splits=('test',))
            verify_oracle(host['slide'],mixed,host['text']);oracle_passes+=1;n=len(host['slide'].feats);rgbs=[]
            for index in indices:
                row=donor['rows'][index];key=(did,row['tile_id'])
                if key not in png_cache:
                    path=donor['directory']/row['path']
                    if path.resolve().parent!=donor['directory'].resolve() or file_sha256(path)!=donor['completion']['input_identity']['png_sha256'][row['tile_id']]:raise ValueError('Changed donor RGB export')
                    with Image.open(path) as image:png_cache[key]=np.asarray(image.convert('RGB'))
                rgbs.append(png_cache[key])
            topo=config['topology'];mask=add_observed_tiles(host['mask'],mixed.coords[n:],mixed.metadata['tile_size'],host['pixel_um'],rgbs,topo['rgb_maximum'],topo['minimum_chroma'])
            parts,quality=overview_components(mask,mixed.coords,mixed.metadata['tile_size'],host['pixel_um'],topo['tile_component_purity'])
            scores=np.concatenate([host['scores'],donor['scores'][indices]])
            known=host['annotation_known']+[donor['annotation_known'][i] for i in indices]
            cancer=host['annotated_cancer']+[donor['annotated_cancer'][i] for i in indices]
            c=case_record(sid+'-p'+str(percent),host,mixed,scores,parts,quality,'synthetic',percent,clean[sid]['baseline']['prediction'],annotation_known=known,cancer=cancer)
            c['donor_id']=did;cases.append(c)
            trials.append(dict(host_id=sid,donor_id=did,requested_percent=percent,realized_percent=100*count/n,host_tiles=n,foreign_tiles=count,
                donor_indices=indices.tolist(),donor_tile_ids=donor['slide'].tile_ids[indices].tolist(),baseline=clean[sid]['baseline'],contaminated=c['baseline'],oracle=clean[sid]['baseline'],oracle_exact_recovery=True))
    comparisons={};rows_by_rule={}
    for name,rule in protocol['review_policy']['rules'].items():
        rows=[]
        for c in cases:
            row=evaluate_flags(c,flagged_components(c,rule));row.update({k:c[k] for k in ('case_id','host_id','split','kind','requested_percent')});rows.append(row)
        rows_by_rule[name]=rows;metrics=summarize(rows);unmodified=[r for r in rows if r['kind']=='unmodified'];positive=[r for r in rows if r['foreign_tiles']]
        dose=[]
        for percent in protocol['contamination']['percentages']:
            group=[r for r in positive if r['requested_percent']==percent] if percent else [r for r in unmodified if sources[r['host_id']]['host_truth']=='benign']
            n=len(group);correct=sum(r['originally_correct'] for r in group);induced=sum(r['newly_induced_error'] for r in group);hits=sum(bool(r['fragment_hit']) for r in group);recovered=sum(r['recovered_new_error'] for r in group)
            dose.append(dict(requested_percent=percent,unique_hosts=n,originally_correct=correct,initially_incorrect=n-correct,new_errors=induced,
                new_error_rate_originally_correct=induced/correct if correct else None,new_error_rate_wilson95=wilson(induced,correct),
                fragment_hits=hits,fragment_recall=hits/n if n and percent else None,fragment_hit_wilson95=wilson(hits,n) if percent else None,
                new_error_recoveries=recovered,new_error_recovery_rate=recovered/induced if induced else None,new_error_recovery_wilson95=wilson(recovered,induced)))
        metrics.update(unmodified_alert_wilson95=wilson(metrics['unmodified_alerts'],metrics['unmodified_slides']),
            clean_damage_wilson95=wilson(metrics['clean_hypothetical_damage'],metrics['clean_originally_correct']),by_dose=dose,
            clustered_foreign_tile_recall=clustered_ratio_interval(positive,'foreign_flagged','foreign_tiles'),
            clustered_fragment_recall=clustered_ratio_interval([r|{'trial':1} for r in positive],'fragment_hit','trial'),
            clustered_new_error_recovery=clustered_ratio_interval(positive,'recovered_new_error','newly_induced_error'))
        comparisons[name]=metrics
    controls=[];draw_metrics=[]
    matched_by_case={c['case_id']:matched_draws(c,flagged_components(c,protocol['review_policy']['rules']['combined']),config['matched_random_draws'],config['seed']) for c in cases}
    for draw in range(config['matched_random_draws']):
        rows=[]
        for c in cases:
            matched=matched_by_case[c['case_id']][draw]
            row=evaluate_flags(c,matched);row.update({k:c[k] for k in ('case_id','host_id','split','kind','requested_percent')});row['draw']=draw;rows.append(row)
        controls.extend(rows);draw_metrics.append(summarize(rows))
    mean_control={k:float(np.mean([r[k] for r in draw_metrics if r[k] is not None])) if any(r[k] is not None for r in draw_metrics) else None for k in draw_metrics[0]}
    classification=classification_summary([r['truth']=='cancer' for r in classifier],[r['prediction']=='cancer' for r in classifier])
    summary=dict(source_kind='real',category='Single frozen PANDA held-out evaluation',protocol_sha256=expected_sha256,source_commit=protocol['source']['commit'],
        slurm_job_id=os.environ['SLURM_JOB_ID'],test_slides_scored=24,patient_independence_verified=False,clinical_validity_verified=False,
        classification=classification,comparisons=comparisons,matched_random_mean=mean_control,matched_control_draws=config['matched_random_draws'],
        oracle_exact_recoveries=oracle_passes,positive_mixtures=sum(r['foreign_tiles']>0 for r in trials),
        distinct_host_slides=len({r['host_id'] for r in trials}),distinct_donor_slides=len({r['donor_id'] for r in trials}),
        exclusions=len(exclusions),automatic_tissue_action='none; filtering calculations are hypothetical',
        uncertainty='95% Wilson intervals for per-dose distinct-slide binary outcomes; stratified unique-slide bootstrap for balanced accuracy; host-cluster bootstrap preserving doses for aggregate recall/recovery, conditional on fixed donors. Patient overlap is unverified and donor reuse limits unconditional population inference. No p-values or parameter revision.')
    for name,value in [('classifier_predictions',classifier),('component_cases',cases),('topology_audit',topology),('trials',trials),('exclusions',exclusions),('metrics_by_case',rows_by_rule),('matched_controls',controls),('summary',summary)]:write_json(target/(name+'.json'),value)
    write_json(target/'completion.json',dict(protocol_sha256=expected_sha256,source_commit=protocol['source']['commit'],artifact_sha256={p.name:file_sha256(p) for p in target.glob('*.json')}))
    return summary
