"""Training-only fixed-support anomaly candidate; preserve all historical rules."""
import json
import os
from pathlib import Path
import numpy as np

from ..experiments import file_sha256
from ..panda_review import prediction,evaluate_flags,summarize,acceptable,wilson
from ..panda_review_run import same_prediction
from ..predictors.data import load_development
from ..research.contracts import ExperimentRun,canonical,slide_identity
from ..research.engine import validate_pair,validate_indices
from ..research.registry import Registry
from ..research.topology_context import memberships
from .calibration import budget_threshold,shortlisted,explain_shortlist
from .contextual_similarity import anomaly_features
from .placement import annotation_arrays
from .training import fold_assignment,host_interval

METHODS=('stable32_min3','matched_full_context')
SEEDS=(20261026,20261027,20261028)


def stable_features(feats,coords,parts):
    """Only embeddings/coordinates/membership enter; masks, IDs and scores cannot."""
    feats=np.asarray(feats);coords=np.asarray(coords);n=len(feats);memberships(parts,n);result=[]
    if (feats.ndim!=2 or not n or coords.shape!=(n,2) or not np.isfinite(feats).all() or not np.isfinite(coords).all() or
            not np.allclose(np.linalg.norm(feats,axis=1),1,atol=1e-4)):raise ValueError('Finite normalized aligned source embeddings required')
    for number,p in enumerate(parts):
        ix=np.asarray(p['indices'],int);outside=np.array(sorted(set(range(n))-set(ix)),int)
        reasons=[]
        if len(outside)<32:reasons.append('fewer_than_32_comparison_tiles')
        if 2*len(ix)>n:reasons.append('candidate_is_majority_of_sampled_bag')
        samples=[]
        if not reasons:
            for seed in SEEDS:
                reference=np.sort(np.random.default_rng(seed).permutation(outside)[:32]);selected=np.r_[ix,reference]
                score=anomaly_features(feats[selected],coords[selected],[dict(indices=list(range(len(ix))))])[0]['scores']['robust_nn5']
                if score is None or not np.isfinite(score):raise ValueError('Finite fixed-support score required')
                samples.append(dict(seed=seed,reference_indices=reference.tolist(),score=score))
        result.append(dict(component_index=number,candidate_tiles=len(ix),remaining_tiles=len(outside),eligibility_reasons=reasons,
            context_samples=samples,stable_score=min(s['score'] for s in samples) if samples else None,
            distinct_reference_subsets=len({tuple(s['reference_indices']) for s in samples})))
    return result


def source_folds(ids,trials,folds=5,seed=20261022):
    """Host and every reused donor stay in one fold; source identity is design only."""
    ids=list(ids)
    if len(ids)!=len(set(ids)):raise ValueError('Unique original sources required')
    parent={sid:sid for sid in ids}
    def find(sid):
        while parent[sid]!=sid:sid=parent[sid]
        return sid
    for t in trials:
        h,d=t['host_id'],t['donor_id']
        if h not in parent or d not in parent or h==d:raise ValueError('Distinct original host/donor sources required')
        a,b=sorted((find(h),find(d)));parent[b]=a
    groups={sid:find(sid) for sid in ids};assignment=fold_assignment(sorted(set(groups.values())),folds,seed)
    return {sid:assignment[group] for sid,group in groups.items()},groups


def method_scores(features,cached,method):
    if method not in METHODS or len(features)!=len(cached):raise ValueError('Aligned fixed candidate methods required')
    return [None if f['eligibility_reasons'] else f['stable_score'] if method=='stable32_min3' else old['scores']['robust_nn5']
        for f,old in zip(features,cached)]


def metric_row(case,flags,group):
    row=evaluate_flags(case,flags)
    row.update({k:case[k] for k in ('case_id','host_id','kind','split','requested_percent')})
    row.update(donor_id=case.get('donor_id'),source_group=group,one=1,
        source_exact_error_recovery=bool(row['newly_induced_error'] and row['recovered_new_error'] and
            row['foreign_flagged']==row['foreign_tiles'] and row['host_tiles_flagged']==0),
        automatic_tissue_action='none')
    return row


def summarize_method(rows,budgets):
    m=summarize(rows);positive=[r for r in rows if r['kind']=='synthetic'];clean=[r for r in rows if r['kind']=='unmodified']
    m.update(fragment_hits=sum(r['fragment_hit'] for r in positive),source_exact_error_recoveries=sum(r['source_exact_error_recovery'] for r in positive),
        source_exact_error_recovery_rate=sum(r['source_exact_error_recovery'] for r in positive)/m['new_errors'] if m['new_errors'] else None,
        positive_unique_hosts=len({r['host_id'] for r in positive}),positive_unique_donors=len({r['donor_id'] for r in positive}),
        initially_incorrect_positive_hosts=sum(r['initially_incorrect'] for r in positive),
        prediction_changes=sum(r['prediction_changed'] for r in positive),unmodified_alert_wilson95=wilson(m['unmodified_alerts'],m['unmodified_slides']))
    for name,subset,numerator,denominator,key in (
            ('fragment_recall_donor_cluster',positive,'fragment_hit','one','donor_id'),
            ('source_exact_recovery_donor_cluster',positive,'source_exact_error_recovery','newly_induced_error','donor_id'),
            ('clean_alert_source_cluster',clean,'alerted','one','source_group')):
        m[name]=dict(clusters=len({r[key] for r in subset}),interval95=host_interval([dict(r,host_id=r[key]) for r in subset],numerator,denominator,2000,20261029))
    m['training_candidate_gate_passed']=bool(acceptable(m,budgets) and m['fragment_recall'] is not None and m['fragment_recall']>=.2 and
        m['source_exact_error_recovery_rate'] is not None and m['source_exact_error_recovery_rate']>=.25)
    return m


def preflight(config_path,expected_sha256,project,check_inputs=False):
    if file_sha256(config_path)!=expected_sha256:raise ValueError('Frozen stable-context protocol changed')
    c=json.loads(Path(config_path).read_text());project=Path(project)
    if (c['schema_version']!=1 or c['experiment_id']!='panda_stable_context_v1' or c['split']!='train' or c['slides']!=72 or
            c['positive_cases']!=24 or c['percent']!=5 or c['components']!=556 or c['reference_tiles']!=32 or c['seeds']!=list(SEEDS) or
            c['methods']!=list(METHODS) or c['folds']!=5 or c['fold_seed']!=20261022 or c['maximum_feature_estimates']!=1668 or
            c['primary']!='stable32_min3' or c['minimum_mapping_fraction']!=.9 or c['minimum_useful_fragment_recall']!=.2 or
            c['minimum_source_exact_error_recovery']!=.25 or c['new_model_inference'] is not False or c['new_contamination_draws'] is not False or
            c['hypothetical_pooling_uses_saved_class_scores'] is not True or
            c['budgets']!=dict(unmodified_alert_rate=.1,components_per_slide=.5,genuine_cancer_slide_flag_rate=.1,clean_damage_rate=.05) or
            c['resources']!=dict(cpus=2,memory_gb=8,maximum_minutes=10,gpu=0) or c['original_final_test_predictions_authorized'] is not False):
        raise ValueError('Fixed bounded original-training candidate scope required')
    required={'src/floater_finder/'+n for n in ('detectors/stable_context.py','detectors/contextual_similarity.py','detectors/training.py',
        'detectors/calibration.py','detectors/placement.py','research/engine.py','research/contracts.py','research/registry.py',
        'research/topology_context.py','predictors/data.py','panda_review.py','panda_review_run.py')}
    required|={'scripts/panda_stable_context.py','scripts/slurm/panda_stable_context.sbatch','reports/panda_s1_trials_23065666.json'}
    if not required.issubset(c['source_files']):raise ValueError('Complete stable-context source freeze required')
    for name,digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name)!=digest:raise ValueError('Frozen candidate source differs')
    if c['inputs']['trials']['sha256']!=c['source_files']['reports/panda_s1_trials_23065666.json']:raise ValueError('Original stress receipt identity required')
    if check_inputs:
        if any(file_sha256(e['path'])!=e['sha256'] for e in c['inputs'].values()):raise ValueError('Original training input receipt changed')
        if Path(c['output']).exists():raise FileExistsError('Preserve all prior/partial outputs')
        if not Path(c['output']).parent.is_dir() or not Path(c['encoded_root']).is_dir():raise ValueError('Verified source/output roots required')
    return c


def run(config_path,expected_sha256,project,output,source_commit,execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):raise RuntimeError('Explicit CPU Slurm execution required')
    c=preflight(config_path,expected_sha256,project,check_inputs=True)
    if Path(output).resolve()!=Path(c['output']).resolve():raise ValueError('Exact new candidate output required')
    inp={k:v['path'] for k,v in c['inputs'].items()}
    loaded,receipt=load_development(inp['manifest'],inp['directories'],c['encoded_root'],inp['verification'],'train')
    sources={s['slide'].metadata['slide_id']:s for s in loaded}
    catalog=json.loads(Path(inp['cases']).read_text())
    if any(r['split']=='test' for r in catalog):raise ValueError('No final-test case records permitted')
    clean={r['host_id']:r for r in catalog if r['split']=='train' and r['kind']=='unmodified'}
    positives=sorted((r for r in catalog if r['split']=='train' and r['kind']=='synthetic' and float(r['requested_percent'])==5),key=lambda r:r['host_id'])
    trials=[r for r in json.loads(Path(inp['trials']).read_text()) if r['split']=='train' and float(r['requested_percent'])==5];byhost={r['host_id']:r for r in trials}
    if (len(sources)!=72 or set(sources)!=set(clean) or len(positives)!=24 or len(byhost)!=len(trials) or len(byhost)!=24 or
            {r['host_id'] for r in positives}!=set(byhost) or len({r['donor_id'] for r in positives})!=16):raise ValueError('Exact frozen original-training membership required')
    cache=json.loads(Path(inp['features']).read_text());completion=json.loads(Path(inp['feature_completion']).read_text())
    if (cache['source_kind']!='real' or cache['config_sha256']!=c['old_feature_config_sha256'] or completion['status']!='verified' or
            completion['artifacts']['feature_checkpoint.json']!=c['inputs']['features']['sha256']):raise ValueError('Verified cached full-context features required')
    identities={sid:slide_identity(s['slide']) for sid,s in sources.items()};assignment,groups=source_folds(sorted(sources),trials)
    registry=Registry(output,ExperimentRun(c['experiment_id'],c['hypothesis'],source_commit,canonical(c),c['inputs']['manifest']['sha256'],
        'train',loaded[0]['slide'].metadata['model']['checkpoint_sha256'],receipt['text_fingerprint'],canonical(c['resources'])))
    registry.status('planned');registry.status('running',slurm_job_id=os.environ['SLURM_JOB_ID']);features={};cases=list(clean.values())+positives
    try:
        for case in cases:
            sid=case['host_id'];host=sources[sid]['slide'];feats=host.feats;coords=host.coords
            if case['kind']=='synthetic':
                t=byhost[sid];donor=sources[case['donor_id']]['slide']
                if t['oracle_exact_recovery'] is not True or t['oracle']!=t['baseline']:raise RuntimeError('Saved oracle receipt failed; stop')
                validate_pair(host,donor,'s1','cancer');ix,count=validate_indices(host,donor,t['donor_indices'],5)
                if (t['donor_id']!=case['donor_id'] or t['donor_tile_ids']!=donor.tile_ids[ix].tolist() or
                        t['host_tiles']!=len(host.feats) or t['foreign_tiles']!=count or case['foreign_mask']!=[False]*len(host.feats)+[True]*count or
                        case['tile_scores']!=clean[sid]['tile_scores']+[clean[case['donor_id']]['tile_scores'][i] for i in ix] or
                        any(case[key]!=clean[sid][key]+[clean[case['donor_id']][key][i] for i in ix] for key in ('annotation_known','annotated_cancer'))):raise ValueError('Saved mixture identity differs')
                feats=np.concatenate([host.feats,donor.feats[ix]]);coords=np.concatenate([host.coords,donor.coords[ix]+np.asarray(t['synthetic_injection']['translation_um'])])
            elif any(case['foreign_mask']):raise ValueError('Clean case contains foreign truth')
            if len(feats)!=len(case['tile_scores']) or not same_prediction(prediction(case['tile_scores']),case['baseline']):raise ValueError('Cached original scorer provenance differs')
            known,cancer=annotation_arrays(sources[sid]['annotations'],sources[sid]['annotations'],[],[],len(host.feats))
            if not np.array_equal(known,clean[sid]['annotation_known']) or not np.array_equal(cancer,clean[sid]['annotated_cancer']):raise ValueError('Native annotation provenance differs')
            measured=stable_features(feats,coords,[dict(indices=p['indices']) for p in case['components']])
            old=cache['features'][case['case_id']]
            if len(old)!=len(measured):raise ValueError('Old component/cache order differs')
            for f in measured:
                if not f['eligibility_reasons'] and (old[f['component_index']]['scores']['robust_nn5'] is None or not np.isfinite(old[f['component_index']]['scores']['robust_nn5'])):
                    raise ValueError('Finite matched full-context score required')
            features[case['case_id']]=measured;registry.checkpoint('case-'+str(len(features)).zfill(3),dict(case_id=case['case_id'],host_id=sid,
                kind=case['kind'],donor_id=case.get('donor_id'),source_identity=identities[sid],features=measured))
        if sum(len(v) for v in features.values())!=556 or sum(len(f['context_samples']) for v in features.values() for f in v)>1668:raise RuntimeError('Frozen feature workload changed')
        results={};fold_records=[]
        for method in METHODS:
            rows=[]
            scores={case['case_id']:method_scores(features[case['case_id']],cache['features'][case['case_id']],method) for case in cases}
            for fold in range(5):
                fit=[case for case in clean.values() if assignment[case['host_id']]!=fold];held=[case for case in cases if assignment[case['host_id']]==fold]
                fitting=[scores[case['case_id']] if case['mapping_fraction']>=.9 else [] for case in fit]
                threshold=budget_threshold(fitting,.1,.5)
                fold_records.append(dict(method=method,fold=fold,threshold=threshold,fit_clean_slides=len(fit),fit_ids=[r['host_id'] for r in fit],held_ids=sorted({r['host_id'] for r in held}),
                    held_donor_ids=sorted({r['donor_id'] for r in held if r['kind']=='synthetic'}),fit_alerts=sum(any(s is not None and threshold is not None and s>threshold for s in values) for values in fitting)))
                for case in held:
                    if case['kind']=='synthetic' and assignment[case['donor_id']]!=fold:raise RuntimeError('Donor-source fold leakage')
                    flags=shortlisted(scores[case['case_id']],threshold,case['mapping_fraction'])
                    row=metric_row(case,flags,groups[case['host_id']]);row.update(fold=fold,threshold=threshold,scores=scores[case['case_id']],
                        explanations=explain_shortlist(case['components'],flags));rows.append(row)
            results[method]=dict(metrics=summarize_method(rows,c['budgets']),cases=rows)
        if any(slide_identity(s['slide'])!=identities[sid] for sid,s in sources.items()) or any(file_sha256(e['path'])!=e['sha256'] for e in c['inputs'].values()):raise RuntimeError('Original inputs mutated')
        summary=dict(source_kind='real',clean_slides=72,positive_cases=24,unique_positive_donors=16,source_groups=len(set(groups.values())),components=556,
            feature_estimates=sum(len(f['context_samples']) for v in features.values() for f in v),
            ineligible_components=sum(bool(f['eligibility_reasons']) for v in features.values() for f in v),
            methods=results,folds=fold_records,primary='stable32_min3',saved_oracle_receipts_verified=24,new_oracle_executions=0,
            new_model_inference=False,hypothetical_pooling_uses_saved_class_scores=True,new_contamination_draws=False,
            independent_validation=False,final_test_ready=False,automatic_tissue_action='none',
            interpretation='Training-only fixed-support review candidate; no independent or clinical validation, no tissue action')
        registry.checkpoint('summary',summary);registry.status('verified',validation=True,interpretation=summary['interpretation']);return summary
    except BaseException as exc:
        registry.status('failed',interpretation=type(exc).__name__+': '+str(exc));raise
