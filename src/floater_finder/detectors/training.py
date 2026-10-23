"""Training-only cross-fit detector experiment on immutable saved S1 draws."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from ..artifacts import write_json
from ..experiments import file_sha256
from ..panda_review import evaluate_flags, summarize, wilson
from ..panda_review_run import load_sources, same_prediction
from ..panda_stress import inject_development_s1
from .contextual_similarity import METHODS, anomaly_features, cohort_distance, unit_mean
from .calibration import budget_threshold, shortlisted, explain_shortlist, weighted_pr


def fold_assignment(ids, folds, seed):
    if len(ids) != len(set(ids)) or folds < 2 or len(ids) < folds:
        raise ValueError('Distinct slide groups and at least two folds required')
    order=sorted(ids,key=lambda sid:hashlib.sha256(f'{seed}/{sid}'.encode()).hexdigest())
    return {sid:i % folds for i,sid in enumerate(order)}


def host_interval(rows, numerator, denominator, draws, seed):
    ids=sorted({r['host_id'] for r in rows})
    pairs=np.array([[sum(r[numerator] for r in rows if r['host_id']==sid),sum(r[denominator] for r in rows if r['host_id']==sid)] for sid in ids])
    if not len(ids) or not pairs[:,1].sum():return None
    rng=np.random.default_rng(seed);resamples=pairs[rng.integers(0,len(ids),size=(draws,len(ids)))].sum(axis=1)
    estimates=resamples[resamples[:,1]>0];values=estimates[:,0]/estimates[:,1]
    return [float(x) for x in np.quantile(values,[.025,.975])]


def train_cases(path, expected_sha):
    if file_sha256(path)!=expected_sha:raise ValueError('Saved component measurements changed')
    cases=[c for c in json.loads(Path(path).read_text()) if c['split']=='train']
    if any(c['split']!='train' for c in cases):raise ValueError('Training split guard')
    if len({c['host_id'] for c in cases if c['kind']=='unmodified'})!=72 or sum(c['kind']=='synthetic' for c in cases)!=120:
        raise ValueError('Expected 72 clean training slides and 120 existing positive mixtures')
    return cases


def _method_scores(case, features, method, reference):
    if method=='cohort_centroid5':
        return [cohort_distance(f['centroid'],reference) if f['status']=='evaluable' else None for f in features]
    return [f['scores'][method] for f in features]


def _metric_row(case, flags):
    row=evaluate_flags(case,flags)
    row.update({k:case[k] for k in ('case_id','host_id','split','kind','requested_percent')})
    return row


def _component_ranking(cases, records, method):
    observations=[]
    for case in cases:
        entry=records[case['case_id']]
        if case['mapping_fraction']<.9:continue
        truth=np.asarray(case['foreign_mask'],bool)
        native=np.asarray(case['annotated_cancer'],bool)&np.asarray(case['annotation_known'],bool)&~truth
        for i,(p,score) in enumerate(zip(case['components'],entry['scores'])):
            if score is None:continue
            ix=p['indices'];foreign=int(truth[ix].sum())
            observations.append(dict(host_id=case['host_id'],case_id=case['case_id'],component_index=i,score=score,
                any_foreign=bool(foreign),majority_foreign=foreign/len(ix)>=.5,
                genuine_native_cancer=bool(native[ix].any()),kind=case['kind'],tiles=len(ix)))
    counts={sid:sum(r['host_id']==sid for r in observations) for sid in {r['host_id'] for r in observations}}
    pr=weighted_pr([r['score'] for r in observations],[r['any_foreign'] for r in observations],
                   [1/counts[r['host_id']] for r in observations])
    native=[r['score'] for r in observations if r['kind']=='unmodified' and r['genuine_native_cancer']]
    foreign=[r['score'] for r in observations if r['majority_foreign']]
    def distribution(values):
        return dict(count=len(values),quantiles=[float(x) for x in np.quantile(values,[0,.1,.25,.5,.75,.9,1])]) if values else dict(count=0,quantiles=None)
    # Pairwise overlap is descriptive; repeated doses/donors are not independent.
    superiority=float(np.mean(np.asarray(foreign)[:,None]>np.asarray(native)[None,:])+.5*np.mean(np.asarray(foreign)[:,None]==np.asarray(native)[None,:])) if native and foreign else None
    return dict(method=method,component_observations=len(observations),positive_observations=sum(r['any_foreign'] for r in observations),
                unique_hosts=len(counts),host_equal_weight_pr=pr,native_cancer=distribution(native),majority_foreign=distribution(foreign),
                foreign_above_native_pair_fraction=superiority,interpretation='Descriptive out-of-fold training ranking; dependent doses and reused donors; no independent validation'),observations


def run(manifest,directories,encoded,verification,stress,cases_path,config_path,output):
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Real detector comparisons require CPU Slurm')
    if os.environ.get('SLURM_JOB_GPUS'):raise RuntimeError('CPU-only detector experiment')
    config=json.loads(Path(config_path).read_text())
    if config['permitted_split']!='train' or tuple(config['methods'])!=METHODS:raise ValueError('Frozen training configuration required')
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve successful and failed outputs')
    cases=train_cases(cases_path,config['component_case_sha256'])
    # The loader filters cohort rows before opening any NPZ: only training arrays.
    sources,receipt=load_sources(manifest,directories,encoded,verification,('train',))
    if len(sources)!=config['expected_clean_slides']:raise ValueError('Training source count differs')
    trials={(t['host_id'],t['requested_percent']):t for t in json.loads((Path(stress)/'trials.json').read_text()) if t['split']=='train' and t['requested_percent']>0}
    assignment=fold_assignment(sorted(sources),config['folds'],config['fold_seed'])
    centers={sid:unit_mean(s['slide'].feats) for sid,s in sources.items()}
    features={};oracle_checks=0
    output.mkdir(parents=True,exist_ok=False)
    for case in cases:
        source=sources[case['host_id']];slide=source['slide']
        if case['kind']=='synthetic':
            trial=trials[(case['host_id'],case['requested_percent'])];donor=sources[trial['donor_id']]
            slide=inject_development_s1(slide,donor['slide'],np.asarray(trial['donor_indices']),case['requested_percent'],20261020)
            n=len(source['slide'].feats)
            if not (np.array_equal(slide.feats[:n],source['slide'].feats) and np.array_equal(slide.coords[:n],source['slide'].coords)
                    and np.array_equal(slide.foreign_mask,np.asarray(case['foreign_mask'],bool))):
                raise RuntimeError('Exact saved S1 reconstruction/oracle failed')
            oracle_checks+=1
        if len(slide.feats)!=len(case['tile_scores']):raise ValueError('Saved components and embeddings differ')
        score_matrix=source['scores'] if case['kind']=='unmodified' else np.concatenate([source['scores'],donor['scores'][trial['donor_indices']]])
        from ..panda_review import prediction
        if not same_prediction(prediction(score_matrix),case['baseline']):raise RuntimeError('Frozen baseline differs')
        scale=slide.metadata.get('microns_per_unit')
        if scale is None:raise ValueError('Verified physical coordinate scale required')
        features[case['case_id']]=anomaly_features(slide.feats,slide.coords*scale,
            [dict(indices=p['indices']) for p in case['components']],distant_um=config['distant_context_um'])
        print(json.dumps(dict(stage='features',case_id=case['case_id'],components=len(case['components']))),flush=True)
    write_json(output/'feature_checkpoint.json',dict(schema_version=1,features=features,oracle_checks=oracle_checks,
        reference_fit='cohort scores populated separately per fold',source_kind='real',config_sha256=file_sha256(config_path)))
    clean=[c for c in cases if c['kind']=='unmodified'];summaries={};raw={};ranking={};observations={};fold_records=[]
    for method in METHODS:
        rows=[];and_rows=[];records={};sensitivity=[[] for _ in config['sensitivity_quantiles']]
        for fold in range(config['folds']):
            fit=[c for c in clean if assignment[c['host_id']]!=fold];held=[c for c in cases if assignment[c['host_id']]==fold]
            ref_ids=[c['host_id'] for c in fit]
            def get_scores(c):
                refs=[centers[sid] for sid in ref_ids if sid!=c['host_id'] and centers[sid] is not None]
                return _method_scores(c,features[c['case_id']],method,refs)
            fit_scores=[get_scores(c) if c['mapping_fraction']>=config['minimum_mapping_fraction'] else [] for c in fit]
            threshold=budget_threshold(fit_scores,config['budgets']['unmodified_alert_rate'],config['budgets']['components_per_slide'])
            flat=[s for row in fit_scores for s in row if s is not None]
            quantiles=[float(np.quantile(flat,q,method='higher')) if flat else None for q in config['sensitivity_quantiles']]
            fit_counts=[len(shortlisted(s,threshold,1.)) for s in fit_scores]
            fold_records.append(dict(method=method,fold=fold,fit_ids=ref_ids,held_ids=sorted({c['host_id'] for c in held}),threshold=threshold,
                fit_clean_alert_rate=float(np.mean(np.asarray(fit_counts)>0)),fit_mean_components=float(np.mean(fit_counts)),
                reference_slides=len(ref_ids),reference_contains_exact_donor_slides=sum(c['kind']=='synthetic' and c.get('donor_id') in ref_ids for c in held)))
            for case in held:
                scores=get_scores(case);flags=shortlisted(scores,threshold,case['mapping_fraction'],config['minimum_mapping_fraction'])
                row=_metric_row(case,flags);row.update(fold=fold,threshold=threshold,explanations=explain_shortlist(case['components'],flags));rows.append(row)
                # Separate AND comparator: influence never changes the two-stage flags.
                and_flags=[i for i in flags if case['components'][i].get('influence') is not None and case['components'][i]['influence']>=config['influence_and_comparator']]
                and_rows.append(_metric_row(case,and_flags));records[case['case_id']]=dict(scores=scores,threshold=threshold,fold=fold)
                for j,cutoff in enumerate(quantiles):
                    sensitivity[j].append(_metric_row(case,shortlisted(scores,cutoff,case['mapping_fraction'])))
        metrics=summarize(rows);clean_rows=[dict(r,one=1) for r in rows if r['kind']=='unmodified']
        positive_rows=[dict(r,one=1) for r in rows if r['foreign_tiles']>0]
        metrics['unmodified_alert_wilson95']=wilson(metrics['unmodified_alerts'],metrics['unmodified_slides'])
        metrics['fragment_recall_host_bootstrap95']=host_interval(positive_rows,'fragment_hit','one',config['bootstrap_draws'],config['bootstrap_seed'])
        metrics['clean_burden_host_bootstrap95']=host_interval(clean_rows,'alerts','one',config['bootstrap_draws'],config['bootstrap_seed'])
        metrics['burden_pass']=metrics['unmodified_alert_rate']<=config['budgets']['unmodified_alert_rate'] and metrics['mean_components_per_unmodified_slide']<=config['budgets']['components_per_slide']
        metrics['useful_fragment_recall']=metrics['fragment_recall']>=config['minimum_useful_fragment_recall']
        summaries[method]=dict(two_stage=metrics,and_influence_comparator=summarize(and_rows),
            sensitivity=[dict(training_clean_quantile=q,metrics=summarize(r)) for q,r in zip(config['sensitivity_quantiles'],sensitivity)])
        raw[method]=rows;ranking[method],observations[method]=_component_ranking(cases,records,method)
    identities=dict(manifest_sha256=file_sha256(manifest),directories_sha256=file_sha256(directories),verification_sha256=file_sha256(verification),
        cases_sha256=file_sha256(cases_path),stress_trials_sha256=file_sha256(Path(stress)/'trials.json'),config_sha256=file_sha256(config_path),
        checkpoint_sha256=next(iter(sources.values()))['slide'].metadata['model']['checkpoint_sha256'],text_fingerprint=receipt['text_fingerprint'])
    report=dict(schema_version=1,source_kind='real',slurm_job_id=os.environ['SLURM_JOB_ID'],source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'),
        primary_prototype=config['primary_prototype'],primary=summaries[config['primary_prototype']],methods=summaries,ranking=ranking,
        folds=fold_records,identities=identities,counts=dict(unique_training_slides=len(sources),positive_cases=sum(c['kind']=='synthetic' for c in cases),
            unique_hosts=len({c['host_id'] for c in cases if c['kind']=='synthetic'}),unique_donors=len({c['donor_id'] for c in cases if c['kind']=='synthetic'}),
            clean_cases=len(clean),oracle_checks=oracle_checks,unknown_mask_clean_slides=sum(not any(c['annotation_known']) for c in clean),
            unmapped_clean_abstentions=sum(c['mapping_fraction']<.9 for c in clean),
            empty_component_exclusions=sum(p['status']!='evaluable' for c in cases for p in c['components'])),
        limitations=config['limitations'],final_test_predictions_computed=False,calibration_predictions_computed=False,
        scientific_gate='Training-only prototypes, not independently validated; no automatic tissue action; no post-outcome primary switch')
    write_json(output/'metrics_by_case.json',raw);write_json(output/'ranking_observations.json',observations);write_json(output/'report.json',report)
    write_json(output/'completion.json',dict(status='verified',artifacts={p.name:file_sha256(p) for p in output.glob('*.json')}))
    return report
