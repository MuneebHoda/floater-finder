"""Frozen S1 follow-up on evaluated Radboud60; no detector or clinical claims."""
import json
import os
from pathlib import Path
import numpy as np

from ..experiments import file_sha256
from ..fragment_dependence import analyze_fragment_dependence
from ..injection import connected_fragment
from ..panda_final import clustered_ratio_interval
from ..panda_stress import foreign_count
from ..predictors.fresh import frozen_inputs, load_fresh, read_rows
from .contracts import FollowupCohort, ExperimentRun, DonorSelection, InterventionSpec, canonical, slide_identity
from .engine import apply_intervention, select_donors, tile_components
from .registry import Registry


def preflight(config_path, expected_sha256, project):
    """Metadata/model checks only: never open real slide arrays or call a scorer."""
    project = Path(project)
    if file_sha256(config_path) != expected_sha256:
        raise ValueError('Frozen follow-up protocol changed')
    c = json.loads(Path(config_path).read_text())
    if (c['schema_version'] != 1 or c['experiment_id'] != 'panda_fresh_s1_v1' or
            c['seeds'] != [20261020, 20261021, 20261022] or c['percentages'] != [.5, 1, 2, 5, 10] or
            c['modes'] != ['append_legacy', 'replacement'] or c['donors_per_host'] != 1 or
            c['minimum_cancer_fraction'] != .1 or c['counterfactual_percent'] != 5 or
            c['counterfactual_seed'] != c['seeds'][0] or c['alert_policy'] is not None or
            c['maximum_interventions'] != 1200 or c['maximum_counterfactual_bags'] != 140 or
            set(c['inputs']['sha256']) != {'embeddings-verified-v1.json','clean-baseline-v1/completion.json','tiling-directories.json'} or
            c['resources'] != dict(cpus=2, memory_gb=8, maximum_minutes=20, gpu=0)):
        raise ValueError('Fixed bounded S1 follow-up scope required')
    for name, digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Project-relative frozen source paths required')
        if file_sha256(project/name) != digest:
            raise ValueError('Follow-up source changed: '+name)
    protocol, rows, all_models = frozen_inputs(project/c['baseline_protocol'], c['baseline_protocol_sha256'], project)
    if (c['manifest_sha256']!=protocol['manifest_sha256'] or c['excluded_ids']!=protocol['excluded_slide_ids'] or
            c['text_fingerprint']!=protocol['text_fingerprint']):
        raise ValueError('Follow-up membership/provenance differs from frozen baseline')
    required = {'src/floater_finder/research/'+name for name in ('fresh_stress.py','contracts.py','engine.py','registry.py')}
    required |= {'src/floater_finder/'+name for name in ('fragment_dependence.py','injection.py','panda_stress.py')}
    required |= {'scripts/panda_fresh_s1.py','scripts/slurm/panda_fresh_s1.sbatch'}
    if not required.issubset(c['source_files']):
        raise ValueError('Incomplete follow-up source freeze')
    return c, protocol, rows, {role: all_models['benign_cancer', role] for role in ('primary', 'historical')}


def same_prediction(actual, saved):
    if actual['prediction'] != saved['prediction'] or actual['model_id'] != saved['model_id']:
        raise RuntimeError('Frozen clean decision differs from saved baseline')
    for key in ('scores', 'margin', 'positive_probability'):
        a, b = actual[key], saved[key]
        if isinstance(a, dict):
            if set(a) != set(b):
                raise RuntimeError('Saved score labels differ')
            keys = list(a)
            a, b = [a[k] for k in keys], [b[k] for k in keys]
        if (a is None) != (b is None) or (a is not None and not np.allclose(a, b, rtol=0, atol=1e-12)):
            raise RuntimeError('Frozen clean scores differ from saved baseline')


def annotation_area(source):
    slide, rows = source['slide'], source['rows']
    if not slide.metadata['panda']['mask_available']:
        raise ValueError('Verified annotation masks required for this follow-up')
    if len(rows) != len(slide.feats) or [r['tile_id'] for r in rows] != slide.tile_ids.tolist():
        raise ValueError('Annotation rows must align with saved vectors')
    a = np.array([[float(r[f'gleason{g}_fraction']) for g in (3, 4, 5)] for r in rows])
    area = np.array([float(r['area_mm2']) for r in rows])
    expected = np.prod(slide.metadata['tile_size'])/1e6
    if (not np.isfinite(a).all() or (a < 0).any() or (a.sum(axis=1) > 1+1e-10).any() or
            not np.isfinite(area).all() or not np.allclose(area, expected, rtol=1e-9, atol=1e-12)):
        raise ValueError('Invalid annotation fractions or physical area')
    return area*a.sum(axis=1)


def counterfactual(slide, model, areas, provenance):
    report = analyze_fragment_dependence(slide.feats, slide.coords, lambda f, xy: model(f),
        tile_step=slide.metadata['tile_step'], tile_size=slide.metadata['tile_size'],
        coordinate_units=slide.metadata['coordinate_units'], microns_per_unit=slide.metadata['microns_per_unit'],
        source_kind=slide.metadata['source_kind'], scorer_id=model.spec['model_id'],
        tile_ids=slide.tile_ids, max_gap_tiles=0, alert_policy=None)
    if report['baseline']!=model.score_slide(slide):
        raise RuntimeError('Counterfactual baseline drift')
    for piece in report['pieces']:
        indices = np.array(piece['tile_indices'], dtype=int)
        foreign = slide.foreign_mask[indices]
        piece.update(evaluation_only_foreign_tiles=int(foreign.sum()),
            evaluation_only_genuine_cancer_area_mm2=float(areas[indices][~foreign].sum()),
            evaluation_only_foreign_cancer_area_mm2=float(areas[indices][foreign].sum()))
    report.update(followup_provenance=provenance, complete_biopsy_topology_verified=False,
        component_geometry_role='native_carrier' if provenance['mode']=='replacement' else 'sampled_occupied_cells')
    return report


def summarize(trials, exclusions, clean, cf_counts, config):
    metrics = []
    for role in ('primary', 'historical'):
        for control in ('foreign_cancer', 'same_source_sham'):
            for mode in config['modes']:
                for percent in config['percentages']:
                    group = [r for r in trials if (r['role'], r['control'], r['mode'], r['requested_percent']) == (role, control, mode, percent)]
                    excluded = [r for r in exclusions if (r['control'], r['mode'], r['requested_percent']) == (control, mode, percent)]
                    correct = [r for r in group if r['originally_correct']]
                    metrics.append(dict(role=role, control=control, mode=mode, requested_percent=percent,
                        planned_instances=len(group)+len(excluded), eligible_instances=len(group), excluded_instances=len(excluded),
                        unique_host_slides=len({r['host_id'] for r in group}), unique_donor_slides=len({r['donor_id'] for r in group}),
                        originally_correct_planned=sum(r['originally_correct'][role] for r in excluded)+len(correct),
                        originally_correct_eligible=len(correct), initially_incorrect_eligible=len(group)-len(correct),
                        prediction_changes=sum(r['prediction_changed'] for r in group),
                        new_original_host_label_errors=sum(r['new_original_host_error'] for r in group),
                        induced_error_interval=clustered_ratio_interval(group, 'new_original_host_error', 'originally_correct',
                            seed=config['bootstrap_seed'], repetitions=2000),
                        mixture_cancer_predictions=sum(r['contaminated']['prediction']=='cancer' for r in group),
                        mean_margin_shift=float(np.mean([r['margin_shift'] for r in group])) if group else None,
                        oracle_exact_passes=sum(r['oracle_exact'] for r in group),
                        target='Original benign host label; included cancer response is a separate target'))
    paired = []
    keys = {(r['role'], r['control'], r['host_id'], r['seed'], r['requested_percent']) for r in trials}
    for key in sorted(keys):
        rows = [r for r in trials if tuple(r[k] for k in ('role','control','host_id','seed','requested_percent'))==key]
        paired.append(dict(zip(('role','control','host_id','seed','requested_percent'),key),
            common_eligible=set(r['mode'] for r in rows)==set(config['modes'])))
    dependence = []
    for role in ('primary','historical'):
        native = [r for r in cf_counts if r['kind']=='unmodified' and r['role']==role]
        evaluable = [r for r in native if r['evaluable_components']>0]
        decisive = sum(r['decision_changing_components']>0 for r in evaluable)
        dependence.append(dict(role=role, unmodified_slides=len(native), evaluable_slides=len(evaluable),
            unevaluable_slides=len(native)-len(evaluable), slides_with_decisive_components=decisive,
            dependence_fraction_among_evaluable=decisive/len(evaluable) if evaluable else None,
            genuine_cancer_components=sum(r['genuine_cancer_components'] for r in native),
            decisive_genuine_cancer_components=sum(r['decisive_genuine_cancer_components'] for r in native),
            review_alert_rate=None, foreignness_inferred=False))
    return dict(metrics=metrics, paired_mode_eligibility=paired, clean_anchors=clean, unmodified_dependence=dependence,
        counterfactual_counts=cf_counts, eligible_model_trial_records=len(trials),
        exclusions=len(exclusions), unique_hosts=len({r['host_id'] for r in trials}),
        unique_foreign_donors=len({r['donor_id'] for r in trials if r['control']=='foreign_cancer'}),
        review_alert_rate=None, alerts_evaluated=False, models_refit=False,
        original_final_test_predictions_computed=False, patient_independence_verified=False,
        clinical_validity_verified=False, independent_model_validation=False,
        interpretation='Prospective representation stress and sampled-component diagnostics on evaluated slides')


def experiment(sources, models, config, source_commit, output):
    """Shared core also supports explicitly labelled artificial unit-test fixtures."""
    if Path(output).exists():
        raise FileExistsError('Preserve prior follow-up outputs')
    kinds = {s['slide'].metadata['source_kind'] for s in sources.values()}
    if kinds not in ({'fixture'}, {'real'}):
        raise ValueError('Homogeneous fixture or real sources required')
    if kinds=={'real'} and (not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS')):
        raise RuntimeError('Real follow-up processing requires approved CPU Slurm')
    hosts = sum(s['grade']==0 for s in sources.values())
    if (set(models)!={'primary','historical'} or
            hosts*len(config['seeds'])*len(config['percentages'])*2*len(config['modes'])>config['maximum_interventions'] or
            len(sources)+hosts*2*len(config['modes'])>config['maximum_counterfactual_bags']):
        raise ValueError('Predeclared workload bound exceeded before scoring')
    members = tuple((sid, slide_identity(s['slide'])) for sid, s in sorted(sources.items()))
    scope = FollowupCohort(config['manifest_sha256'], config['baseline_protocol_sha256'], members, tuple(config['excluded_ids']))
    for source in sources.values():
        scope.validate(source['slide'])
    areas = {sid: annotation_area(s) for sid, s in sources.items()}
    baseline = {role: {sid: model.score_slide(s['slide']) for sid, s in sources.items()} for role, model in models.items()}
    registry = Registry(output, ExperimentRun(config['experiment_id'], config['hypothesis'], source_commit,
        canonical(dict(protocol=config, input_identities=members)), config['manifest_sha256'], 'fresh_followup',
        next(iter(sources.values()))['slide'].metadata['model']['checkpoint_sha256'], config['text_fingerprint'], canonical(config['resources'])))
    registry.status('planned')
    registry.status('running', slurm_job_id=os.environ.get('SLURM_JOB_ID','fixture-only'))
    trials, exclusions, clean, cf_counts = [], [], [], []

    def analyze(slide, sid, case_id, kind, mode, actual_areas):
        for role, model in models.items():
            report = counterfactual(slide, model, actual_areas, dict(host_id=sid, case_id=case_id, kind=kind, mode=mode, role=role))
            registry.checkpoint('cf-'+case_id+'-'+role, report)
            pieces = report['pieces'];evaluable = [p for p in pieces if p['decision_changing'] is not None]
            cf_counts.append(dict(case_id=case_id, host_id=sid, role=role, kind=kind, mode=mode,
                baseline_prediction=report['baseline']['prediction'], components=len(pieces), evaluable_components=len(evaluable),
                genuine_cancer_components=sum(p['evaluation_only_genuine_cancer_area_mm2']>0 for p in pieces),
                decision_changing_components=sum(bool(p['decision_changing']) for p in evaluable),
                decisive_genuine_cancer_components=sum(bool(p['decision_changing']) and p['evaluation_only_genuine_cancer_area_mm2']>0 for p in evaluable)))

    try:
        for sid, source in sorted(sources.items()):
            for role in models:
                clean.append(dict(host_id=sid, role=role, grade=source['grade'], baseline=baseline[role][sid]))
            analyze(source['slide'], sid, sid+'-clean', 'unmodified', 'clean', areas[sid])
        for sid, source in sorted(sources.items()):
            host = source['slide']
            if source['grade'] != 0:
                continue
            for seed in config['seeds']:
                needed = foreign_count(max(config['percentages']), len(host.feats))
                selection = DonorSelection('cancer', config['minimum_cancer_fraction'], (seed,), config['donors_per_host'])
                selected = select_donors(host, sources, selection, 's1', max(config['percentages']), seed, cohort=scope)
                native = tile_components(host)[0]
                native_order = native[connected_fragment(host.subset(native), min(needed,len(native)), seed)]
                for control in ('foreign_cancer', 'same_source_sham'):
                    donor_id, order = None, np.array([], int)
                    if control=='same_source_sham':
                        donor_id, order = sid, native_order
                    elif selected:
                        donor_id, order = selected[0]['donor_id'], np.array(selected[0]['indices'], int)
                    for mode in config['modes']:
                        for number, percent in enumerate(config['percentages']):
                            count = foreign_count(percent, len(host.feats))
                            case_id = f'{sid}-{seed}-{control}-{mode}-{number}'
                            case = dict(case_id=case_id, host_id=sid, donor_id=donor_id, seed=seed, control=control,
                                mode=mode, requested_percent=percent, requested_count=count,
                                originally_correct={r: baseline[r][sid]['prediction']=='benign' for r in models})
                            reason = None
                            if donor_id is None:
                                reason = 'No eligible donor'
                            elif count>len(order):
                                reason = 'Insufficient connected donor capacity'
                            elif mode=='replacement' and count>len(native_order):
                                reason = 'Insufficient connected host replacement capacity'
                            if reason:
                                excluded = dict(case, reason=reason, realized_count=None, realized_percent=None)
                                registry.checkpoint('excluded-'+case_id, excluded);exclusions.append(excluded)
                                continue
                            donor = sources[donor_id]['slide'];indices = order[:count]
                            condition = 'same_source_sham' if control=='same_source_sham' else 'cancer'
                            spec = InterventionSpec('s1', condition, mode, percent, seed, tuple(indices),
                                replacement_indices=tuple(native_order[:count]) if mode=='replacement' else ())
                            result = apply_intervention(host, donor, spec, cohort=scope)
                            if control=='same_source_sham' and mode=='replacement' and not np.array_equal(result.slide.feats,host.feats):
                                raise RuntimeError('Same-source replacement must be an exact feature null')
                            audit = json.loads(result.audit_json)
                            actual_areas = np.r_[areas[sid], areas[donor_id][indices]] if mode=='append_legacy' else areas[sid].copy()
                            if mode=='replacement':
                                actual_areas[np.array(spec.replacement_indices,int)] = areas[donor_id][indices]
                            records = []
                            for role, model in models.items():
                                result.verify(model.score_slide)
                                before, after = baseline[role][sid], model.score_slide(result.slide)
                                record = dict(case, role=role, baseline=before, contaminated=after,
                                    originally_correct=case['originally_correct'][role],
                                    prediction_changed=before['prediction']!=after['prediction'],
                                    new_original_host_error=case['originally_correct'][role] and after['prediction']!='benign',
                                    margin_shift=float(after['margin']-before['margin']),
                                    margin_units='logit' if model.spec['kind']=='linear_probe' else 'cosine_difference',
                                    realized_count=count, realized_percent=100*count/len(host.feats),
                                    altered_fraction_of_final_bag=count/len(result.slide.feats), oracle_exact=True)
                                records.append(record);trials.append(record)
                            registry.checkpoint('trial-'+case_id, dict(records=records, intervention_audit=audit,
                                donor_tile_ids=donor.tile_ids[indices].tolist(), translation_um=result.slide.metadata['injection']['translation_um'],
                                selected_component_capacity=len(order), source_annotation_area_mm2=float(areas[donor_id][indices].sum())))
                            if seed==config['counterfactual_seed'] and percent==config['counterfactual_percent']:
                                analyze(result.slide, sid, case_id, 'synthetic_foreign' if control=='foreign_cancer' else 'native_sham', mode, actual_areas)
            print(json.dumps(dict(stage='host_verified', host_id=sid)),flush=True)
        if len(trials)//len(models)+len(exclusions)>config['maximum_interventions'] or len(cf_counts)//len(models)>config['maximum_counterfactual_bags']:
            raise RuntimeError('Predeclared workload bound exceeded')
        for source in sources.values():
            scope.validate(source['slide'])
        summary = summarize(trials, exclusions, clean, cf_counts, config)
        summary.update(source_commit=source_commit, source_kind=next(iter(sources.values()))['slide'].metadata['source_kind'],
            slurm_job_id=os.environ.get('SLURM_JOB_ID','fixture-only'), protocol=config)
        registry.checkpoint('summary',summary)
        registry.status('verified', validation=True, interpretation=summary['interpretation'])
        return summary
    except BaseException as exc:
        registry.status('failed',interpretation=type(exc).__name__+': '+str(exc))
        raise


def run(config_path, expected_sha256, project, output, source_commit, execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Explicit execution through approved CPU Slurm required')
    if Path(output).exists():
        raise FileExistsError('Preserve prior follow-up outputs')
    config, protocol, rows, models = preflight(config_path, expected_sha256, project)
    if Path(output).resolve()!=Path(config['output']).resolve():
        raise ValueError('Use the exact new output directory from the reviewed protocol')
    root = Path(config['inputs']['root'])
    for name, digest in config['inputs']['sha256'].items():
        if file_sha256(root/name)!=digest:
            raise ValueError('Verified baseline input changed: '+name)
    completion = json.loads((root/'clean-baseline-v1/completion.json').read_text())
    for name, digest in completion['artifacts'].items():
        if file_sha256(root/'clean-baseline-v1'/name)!=digest:
            raise ValueError('Saved baseline outcome changed')
    loaded = load_fresh(protocol, rows, (Path(project)/config['baseline_protocol']).with_name('manifest.csv'),
        root/'tiling-directories.json', root/'embeddings', root/'embeddings-verified-v1.json')
    directories = {Path(d).name: Path(d) for d in json.loads((root/'tiling-directories.json').read_text())}
    sources = {s['image_id']: dict(s, rows=read_rows(directories[s['image_id']]/'tiles.csv')) for s in loaded}
    saved = json.loads((root/'clean-baseline-v1/predictions.json').read_text())
    for role, model in models.items():
        outcomes = {r['image_id']:r for r in saved['benign_cancer/'+role]}
        if len(outcomes)!=60 or set(outcomes)!=set(sources):
            raise ValueError('Exact saved clean baseline membership required')
        for sid, source in sources.items():
            same_prediction(model.score_slide(source['slide']), outcomes[sid])
    return experiment(sources, models, config, source_commit, output)
