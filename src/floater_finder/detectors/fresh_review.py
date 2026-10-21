"""Fixed visual-rule transfer on saved S1 bags; review only, never tissue removal."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np

from ..experiments import file_sha256
from ..predictors.fresh import load_fresh, read_rows
from ..panda_final import clustered_ratio_interval
from ..research.contracts import FollowupCohort, ExperimentRun, InterventionSpec, canonical, slide_identity
from ..research.engine import apply_intervention
from ..research.fresh_stress import preflight as s1_preflight, annotation_area, same_prediction
from ..research.registry import Registry
from .contextual_similarity import anomaly_features
from .placement import evaluate

POLICIES = ('visual', 'dependence', 'combined', 'random_matched')


def transfer_threshold(report, study_ids):
    """Unanimous old clean-fold thresholds; no fresh outcomes select this rule."""
    folds = [r for r in report['folds'] if r['method']=='robust_nn5']
    if (report['primary_prototype']!='robust_nn5' or len(folds)!=5 or
            {r['fold'] for r in folds}!=set(range(5))):
        raise ValueError('Exactly five original robust-NN5 folds required')
    held = [sid for r in folds for sid in r['held_ids']]
    if len(held)!=72 or len(set(held))!=72 or set(held)&set(study_ids):
        raise ValueError('Original training/fresh slide separation required')
    for row in folds:
        if (set(row['fit_ids'])!=set(held)-set(row['held_ids']) or
                row['threshold'] is not None and not np.isfinite(row['threshold'])):
            raise ValueError('Invalid frozen threshold provenance')
    # A fold abstention cannot be converted to unanimous agreement.
    return max(r['threshold'] for r in folds) if all(r['threshold'] is not None for r in folds) else None


def preflight(config_path, expected_sha256, project, check_inputs=False):
    """Source/model/receipt metadata only, without slide arrays or predictions."""
    project = Path(project)
    if file_sha256(config_path)!=expected_sha256:
        raise ValueError('Frozen review protocol changed')
    c = json.loads(Path(config_path).read_text())
    if (c['schema_version']!=1 or c['experiment_id']!='panda_fresh_review_transfer_v1' or
            c['policies']!=list(POLICIES) or c['random_draws']!=32 or c['random_seed']!=20261025 or
            c['visual_method']!='robust_nn5' or c['primary_policy']!='combined' or
            c['automatic_tissue_action']!='none' or c['original_final_test_predictions_authorized'] is not False or
            c['maximum_bags']!=140 or c['maximum_filtered_predictions']!=9800 or
            c['resources']!=dict(cpus=2, memory_gb=8, maximum_minutes=20, gpu=0) or
            c['fit_thresholds'] or c['change_component_rule']):
        raise ValueError('Fixed bounded review-transfer scope required')
    for name, digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name)!=digest:
            raise ValueError('Frozen review source differs: '+name)
    required = {'src/floater_finder/detectors/'+n for n in ('fresh_review.py','contextual_similarity.py','placement.py')}
    required |= {'scripts/panda_fresh_review.py','scripts/slurm/panda_fresh_review.sbatch'}
    if not required.issubset(c['source_files']):
        raise ValueError('Incomplete review source freeze')
    s1, protocol, rows, models = s1_preflight(project/c['s1_protocol'], c['s1_protocol_sha256'], project)
    path = project/c['threshold_report']
    if file_sha256(path)!=c['threshold_report_sha256']:
        raise ValueError('Original threshold report changed')
    threshold = transfer_threshold(json.loads(path.read_text()), [r['image_id'] for r in rows])
    if threshold!=c['visual_threshold']:
        raise ValueError('Unanimous original threshold differs')
    if check_inputs:
        root = Path(s1['output'])
        for name, digest in c['s1_files'].items():
            if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(root/name)!=digest:
                raise ValueError('Sealed S1 receipt differs')
        for name, digest in s1['inputs']['sha256'].items():
            if file_sha256(Path(s1['inputs']['root'])/name)!=digest:
                raise ValueError('Original baseline receipt differs')
        if Path(c['output']).exists():
            raise FileExistsError('Preserve prior review outputs')
    return c, s1, protocol, rows, models


def review_parts(slide, report):
    """Validate saved membership; only truth-free geometry enters visual scores."""
    if (report['tile_count']!=len(slide.feats) or report['piece_count']!=len(report['pieces']) or
            report['geometry']['connectivity']!=8 or report['geometry']['max_gap_tiles']!=0 or
            report['geometry']['tile_size']!=slide.metadata['tile_size'] or
            report['geometry']['tile_step']!=slide.metadata['tile_step'] or
            report['geometry']['coordinate_units']!='microns' or slide.metadata['microns_per_unit']!=1):
        raise ValueError('Saved sampled-component geometry differs')
    parts = []
    for p in report['pieces']:
        raw = p['tile_indices']
        if not raw or any(type(i) is not int or not 0<=i<len(slide.feats) for i in raw):
            raise ValueError('Invalid saved component indices')
        ix = np.array(raw, int)
        expected_area = len(ix)*np.prod(slide.metadata['tile_size'])/1e6
        if (p['tile_ids']!=slide.tile_ids[ix].tolist() or p['tile_count']!=len(ix) or
                not np.isclose(p['area_mm2'],expected_area,rtol=1e-9,atol=1e-12) or
                p['isolation_mm'] is not None and (not np.isfinite(p['isolation_mm']) or p['isolation_mm']<0)):
            raise ValueError('Saved tile identity or physical geometry differs')
        empty = len(ix)==len(slide.feats)
        if ((p['decision_changing'] is None)!=empty or
                p['counterfactual']['remaining_tile_count']!=len(slide.feats)-len(ix) or
                p['counterfactual']['status']!=('not_evaluable_empty_slide' if empty else 'scored') or
                not empty and type(p['decision_changing']) is not bool):
            raise ValueError('Invalid saved empty-exclusion state')
        parts.append(dict(indices=raw, piece_id=p['piece_id'], area_mm2=p['area_mm2'],
            isolation_mm=p['isolation_mm'], decision_change=p['decision_changing'],
            counterfactual=p['counterfactual']['result']))
    flat = [i for p in parts for i in p['indices']]
    if sorted(flat)!=list(range(len(slide.feats))):
        raise ValueError('Saved pieces must partition all sampled tiles exactly')
    visual = anomaly_features(slide.feats,slide.coords,parts)
    return [dict(p,visual_score=v['scores']['robust_nn5'],visual_status=v['status']) for p,v in zip(parts,visual)]


def flags(parts, threshold, seed):
    """No source IDs, annotations, grades, altered indices or foreign truth."""
    evaluable = [i for i,p in enumerate(parts) if p['decision_change'] is not None]
    visual = [i for i in evaluable if threshold is not None and parts[i]['visual_score'] is not None and parts[i]['visual_score']>threshold]
    decisive = [i for i in evaluable if parts[i]['decision_change']]
    combined = sorted(set(visual)&set(decisive))
    random = sorted(np.random.default_rng(seed).choice(evaluable,len(combined),replace=False).tolist())
    return dict(visual=visual,dependence=decisive,combined=combined,random_matched=random)


def assess(slide, parts, selected, areas, scorer, clean, before, truth):
    """Evaluation-only truth join; all filtering is hypothetical on copied arrays."""
    selected = list(selected)
    if any(type(i) is not int or not 0<=i<len(parts) for i in selected) or len(set(selected))!=len(selected):
        raise ValueError('Unique valid flagged components required')
    # Cached baselines and one-piece counterfactuals avoid repeating completed scores.
    def filtered(feats):
        if not selected:
            return before
        if len(selected)==1 and parts[selected[0]]['counterfactual'] is not None:
            return parts[selected[0]]['counterfactual']
        return scorer(feats)
    result = evaluate(slide.feats,parts,selected,slide.foreign_mask,np.ones(len(slide.feats),bool),areas>0,
        filtered,clean,before,truth,1.)
    result.update(topology_abstained=all(p['decision_change'] is None for p in parts),
        complete_biopsy_topology_verified=False,automatic_tissue_action='none',
        flagged_occupied_area_mm2=sum(parts[i]['area_mm2'] for i in selected))
    return result


def measure_bag(slide, byrole, models, areas, clean, truth, config, case_id):
    """Shared fixture/real core; reuse saved predictions and components."""
    p = byrole['primary']['followup_provenance']
    parts = review_parts(slide,byrole['primary']);records = [];explanations = {}
    for role,model in models.items():
        report = byrole[role]
        if any(report['followup_provenance'][k]!=p[k] for k in ('case_id','host_id','kind','mode')):
            raise ValueError('Paired report provenance differs')
        if [r['tile_indices'] for r in report['pieces']]!=[r['indices'] for r in parts]:
            raise ValueError('Scorer-specific component topology differs')
        role_parts = [dict(part,decision_change=saved_part['decision_changing'],counterfactual=saved_part['counterfactual']['result'])
            for part,saved_part in zip(parts,report['pieces'])]
        explanations[role] = [dict(piece_id=part['piece_id'],visual_score=part['visual_score'],
            decision_change=part['decision_change'],area_mm2=part['area_mm2'],isolation_mm=part['isolation_mm'],
            signed_cancer_influence=None if part['counterfactual'] is None else report['baseline']['margin']-part['counterfactual']['margin'],
            foreignness='not_established',tissue_action='preserve_all_tissue') for part in role_parts]
        for draw in range(config['random_draws']):
            seed = int.from_bytes(hashlib.sha256(canonical([config['random_seed'],case_id,draw]).encode()).digest()[:8],'big')
            choices = flags(role_parts,config['visual_threshold'],seed)
            for policy in POLICIES if draw==0 else ('random_matched',):
                metric = assess(slide,role_parts,choices[policy],areas,model,clean[role],report['baseline'],truth)
                records.append(dict(metric,case_id=case_id,host_id=p['host_id'],role=role,policy=policy,kind=p['kind'],mode=p['mode'],
                    random_draw=draw if policy=='random_matched' else None,
                    component_geometry_role=report['component_geometry_role']))
    return dict(parts=parts,explanations=explanations,metrics=records)


def summarize(records):
    """Keep independent slide counts, repeated mixtures and random draws distinct."""
    result = []
    fields = ('role','policy','kind','mode')
    for key in sorted({tuple(r[k] for k in fields) for r in records}):
        group = [r for r in records if tuple(r[k] for k in fields)==key]
        native = [r for r in group if not r['foreign_tiles']]
        foreign = [r for r in group if r['foreign_tiles']]
        induced = [r for r in foreign if r['newly_induced_error']]
        clean_correct = [r for r in native if r['unmodified_correct']]
        observations = [dict(r,one=1) for r in group]
        result.append(dict(zip(fields,key),observations=len(group),unique_bags=len({r['case_id'] for r in group}),
            unique_host_slides=len({r['host_id'] for r in group}),
            unique_foreign_donor_slides=len({r['donor_id'] for r in foreign if r.get('donor_id')}),
            alert_rate=sum(r['alerted'] for r in group)/len(group),
            alert_rate_host_bootstrap=clustered_ratio_interval(observations,'alerted','one',seed=20261025),
            mean_flagged_components=sum(r['alerts'] for r in group)/len(group),
            abstentions=sum(r['topology_abstained'] for r in group),
            foreign_bag_observations=len(foreign),fragment_hits=sum(r['fragment_hit'] for r in foreign),
            complete_fragment_hits=sum(r['complete_fragment'] for r in foreign),
            fragment_recall_host_bootstrap=clustered_ratio_interval([dict(r,one=1) for r in foreign],'fragment_hit','one',seed=20261025),
            foreign_tiles=sum(r['foreign_tiles'] for r in foreign),foreign_tiles_flagged=sum(r['foreign_flagged'] for r in foreign),
            native_tiles_flagged=sum(r['host_tiles_flagged'] for r in group),
            genuine_cancer_components=sum(r['genuine_cancer_components'] for r in group),
            genuine_cancer_components_flagged=sum(r['genuine_cancer_components_flagged'] for r in group),
            originally_correct_clean=len(clean_correct),hypothetical_clean_damage=sum(r['hypothetical_clean_damage'] for r in clean_correct),
            induced_host_label_errors=len(induced),recovered_host_label_errors=sum(r['recovered_new_error'] for r in induced),
            recovery_host_bootstrap=clustered_ratio_interval(group,'recovered_new_error','newly_induced_error',seed=20261025),
            empty_after_filter=sum(r['empty_after_hypothetical_filter'] for r in group),
            random_draws_are_not_independent_slides=key[1]=='random_matched'))
    return result


def run(config_path, expected_sha256, project, output, source_commit, execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Explicit approved CPU Slurm execution required')
    c,s1,protocol,rows,models = preflight(config_path,expected_sha256,project,check_inputs=True)
    if Path(output).resolve()!=Path(c['output']).resolve():
        raise ValueError('Exact new review output required')
    root = Path(s1['inputs']['root']); oldroot = Path(s1['output'])
    old_meta = json.loads((oldroot/'run.json').read_text()); old = Registry(oldroot,ExperimentRun(**old_meta['run']))
    if old.report()['status']!='verified':
        raise ValueError('Verified sealed S1 registry required')
    loaded = load_fresh(protocol,rows,(Path(project)/s1['baseline_protocol']).with_name('manifest.csv'),
        root/'tiling-directories.json',root/'embeddings',root/'embeddings-verified-v1.json')
    dirs = {Path(d).name:Path(d) for d in json.loads((root/'tiling-directories.json').read_text())}
    sources = {s['image_id']:dict(s,rows=read_rows(dirs[s['image_id']]/'tiles.csv')) for s in loaded}
    members = tuple((sid,slide_identity(s['slide'])) for sid,s in sorted(sources.items()))
    if canonical(members)!=canonical(json.loads(old.run.config_json)['input_identities']):
        raise ValueError('Original S1 source identities changed')
    scope = FollowupCohort(s1['manifest_sha256'],s1['baseline_protocol_sha256'],members,tuple(s1['excluded_ids']))
    areas = {sid:annotation_area(s) for sid,s in sources.items()}
    saved = old.load_checkpoint('summary'); anchors = {(r['host_id'],r['role']):r['baseline'] for r in saved['clean_anchors']}
    reports = {}
    for event in old.events():
        if event['kind']=='checkpoint' and event['key'].startswith('cf-'):
            report = old.load_checkpoint(event['key']); p = report['followup_provenance']
            byrole = reports.setdefault(p['case_id'],{})
            if p['role'] in byrole:
                raise ValueError('Duplicate saved counterfactual role')
            byrole[p['role']] = report
    if len(reports)!=c['maximum_bags'] or any(set(r)!=set(models) for r in reports.values()):
        raise ValueError('Exact 140 paired saved counterfactual bags required')
    registry = Registry(output,ExperimentRun(c['experiment_id'],c['hypothesis'],source_commit,
        canonical(dict(protocol=c,input_identities=members)),s1['manifest_sha256'],'fresh_followup',
        protocol['embedding_model']['checkpoint_sha256'],protocol['text_fingerprint'],canonical(c['resources'])))
    registry.status('planned');registry.status('running',slurm_job_id=os.environ['SLURM_JOB_ID'])
    records = []
    try:
        for case_id, byrole in sorted(reports.items()):
            p = byrole['primary']['followup_provenance'];sid = p['host_id']; source = sources[sid]; slide = source['slide']
            actual_areas = areas[sid]
            if p['kind']!='unmodified':
                trial = old.load_checkpoint('trial-'+case_id);case = trial['records'][0]
                values = trial['intervention_audit']['spec'].copy()
                for k in ('donor_indices','replacement_indices'):values[k] = tuple(values[k])
                if values['placement_anchor_um'] is not None:values['placement_anchor_um'] = tuple(values['placement_anchor_um'])
                spec = InterventionSpec(**values); donor = sources[case['donor_id']]['slide']
                edit = apply_intervention(slide,donor,spec,cohort=scope)
                if (edit.audit_json!=canonical(trial['intervention_audit']) or slide_identity(edit.restore())!=slide_identity(slide)):
                    raise RuntimeError('Saved intervention/restoration identity mismatch')
                slide = edit.slide;ix = np.array(spec.donor_indices,int)
                actual_areas = np.r_[areas[sid],areas[case['donor_id']][ix]] if p['mode']=='append_legacy' else areas[sid].copy()
                if p['mode']=='replacement':actual_areas[np.array(spec.replacement_indices,int)] = areas[case['donor_id']][ix]
            else:
                trial = None
            for role in models:
                report = byrole[role]
                expected = anchors[sid,role] if trial is None else next(r['contaminated'] for r in trial['records'] if r['role']==role)
                same_prediction(report['baseline'],expected)
            measured = measure_bag(slide,byrole,models,actual_areas,{role:anchors[sid,role] for role in models},
                'benign' if source['grade']==0 else 'cancer',c,case_id)
            for record in measured['metrics']:
                record['donor_id'] = trial['records'][0]['donor_id'] if trial is not None else None
            records.extend(measured['metrics']);registry.checkpoint('review-'+case_id,measured)
        for source in sources.values():scope.validate(source['slide'])
        summary = dict(groups=summarize(records),bags=len(reports),model_policy_records=len(records),
            visual_threshold=c['visual_threshold'],primary_policy=c['primary_policy'],thresholds_refit=False,models_refit=False,
            clinical_validity_verified=False,operating_point_supported=None,original_final_test_predictions_computed=False,
            patient_independence_verified=False,complete_biopsy_topology_verified=False,
            interpretation='Conservative frozen-rule transfer diagnostic on previously evaluated slides; no threshold calibration or final readiness')
        if len(records)>c['maximum_filtered_predictions']:
            raise RuntimeError('Frozen review workload exceeded')
        registry.checkpoint('summary',summary);registry.status('verified',validation=True,interpretation=summary['interpretation'])
        return summary
    except BaseException as exc:
        registry.status('failed',interpretation=type(exc).__name__+': '+str(exc));raise
