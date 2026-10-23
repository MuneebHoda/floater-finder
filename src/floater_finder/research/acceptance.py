"""Real-input CPU acceptance/placement ablation, not a new encoder or held-out test."""
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import numpy as np
from ..artifacts import write_json
from ..injection import connected_fragment
from ..panda_review_run import read_overview
from ..panda_stress import inject_development_s1, binary_predictions, foreign_count
from ..panda_s2 import inject as legacy_grade_inject, predictions as grade_predictions
from .contracts import canonical, slide_identity, ExperimentRun, DonorSelection, InterventionSpec
from .engine import apply_intervention, select_donors, placement_anchor, VerifiedOccupancy, tile_components
from .registry import Registry, file_hash


def _load_training(manifest, directories, encoded, verification):
    from ..predictors.data import load_development
    records, receipt = load_development(manifest, directories, encoded, verification, 'train')
    sources = {r['slide'].metadata['slide_id']: dict(r, rows=r['annotations'], split='train') for r in records}
    return sources, receipt


def _same_slide(a, b):
    if a.metadata != b.metadata or any(not np.array_equal(getattr(a, k), getattr(b, k)) or
            getattr(a, k).dtype != getattr(b, k).dtype for k in ('feats', 'coords', 'tile_ids', 'foreign_mask')):
        raise RuntimeError('Shared engine diverged from exact historical output; stop')


def _occupancy(source, registry, receipt_root, output):
    sid = source['slide'].metadata['slide_id']
    key = 'geometry-'+sid
    prior = registry.load_checkpoint(key)
    if prior is None:
        cfg = dict(pyramid_level=2, maximum_pixels=4_000_000, rgb_maximum=220, minimum_chroma=10,
            tile_component_purity=.8, sensitivity_rgb_maximum=235, sensitivity_minimum_chroma=5)
        record = read_overview(source, cfg, receipt_root, Path(output)/'topology')
        prior = dict(record=record, packed_mask_hex=np.packbits(source['mask']).tobytes().hex(),
            mask_shape=list(source['mask'].shape), pixel_um=source['pixel_um'].tolist(), source_identity=slide_identity(source['slide']))
        registry.checkpoint(key, prior)
    if prior['source_identity'] != slide_identity(source['slide']):
        raise ValueError('Host changed since geometry checkpoint')
    shape = tuple(prior['mask_shape'])
    mask = np.unpackbits(np.frombuffer(bytes.fromhex(prior['packed_mask_hex']), dtype=np.uint8), count=int(np.prod(shape))).reshape(shape).astype(bool)
    return VerifiedOccupancy.from_mask(mask, prior['pixel_um'], prior['record']['image_sha256'],
        'pyramid level2 minRGB<220 and chroma>10; complete bounded overview, no morphology'), prior['record']


def _summary(trials, exclusions):
    rows = []
    dimensions = ('task', 'condition', 'mode', 'requested_percent', 'control')
    grouped_exclusions = [r for r in exclusions if all(k in r for k in dimensions)]
    groups = sorted({tuple(r[k] for k in dimensions) for r in trials+grouped_exclusions})
    for task, condition, mode, percent, control in groups:
        group = [r for r in trials if (r['task'], r['condition'], r['mode'], r['requested_percent'], r['control']) == (task, condition, mode, percent, control)]
        excluded = [r for r in grouped_exclusions if tuple(r[k] for k in dimensions) == (task, condition, mode, percent, control)]
        correct = [r for r in group if r['baseline']['prediction'] == r['host_truth']]
        induced = sum(r['contaminated']['prediction'] != r['host_truth'] for r in correct)
        rows.append(dict(task=task, condition=condition, mode=mode, requested_percent=percent, control=control,
            attempted_trial_instances=len(group)+len(excluded), excluded_trial_instances=len(excluded),
            trial_instances=len(group), unique_host_slides=len({r['host_id'] for r in group}),
            unique_donor_slides=len({r['donor_id'] for r in group}), unique_seeds=len({r['seed'] for r in group}),
            originally_correct_trial_instances=len(correct), initially_incorrect_trial_instances=len(group)-len(correct),
            induced_error_instances=induced, induced_error_fraction=induced/len(correct) if correct else None,
            prediction_change_instances=sum(r['baseline']['prediction'] != r['contaminated']['prediction'] for r in group),
            mean_margin_shift=float(np.mean([r['margin_shift'] for r in group])) if group else None,
            oracle_exact_passes=sum(r['oracle_exact_recovery'] for r in group),
            denominator_unit='host/donor/seed trials; repeated measurements, not independent patients'))
    return dict(metrics=rows, trial_instances=len(trials), exclusion_records=len(exclusions),
        unique_host_slides=len({r['host_id'] for r in trials}), unique_donor_slides=len({r['donor_id'] for r in trials}),
        unique_foreign_donor_slides=len({r['donor_id'] for r in trials if r['control'] != 'same_source_sham'}),
        exact_oracle_passes=sum(r['oracle_exact_recovery'] for r in trials),
        exact_legacy_comparisons=sum(r['legacy_exact_match'] for r in trials),
        coordinate_only_invariance_checks=sum(r['coordinate_only_bag_invariant'] is True for r in trials),
        patient_independence_verified=False, test_slides_scored=False, clinical_validity_verified=False,
        independent_validation=False, intended_interpretation='Real-input engineering acceptance and bounded placement ablation')


def _primary(result, task):
    return result['top5pct'] if task == 's1' else result['mean']


def _margin(prediction, labels):
    return float(prediction['scores'][labels[1]]-prediction['scores'][labels[0]])


def run(manifest, directories, encoded, verification, receipts, protocol, source_commit, output, predictor_path=None):
    if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Real shared-engine acceptance requires bounded CPU Slurm; no GPU')
    config = json.loads(Path(protocol).read_text())
    if (config['schema_version'] not in (1, 2, 3) or config['splits'] != ['train'] or config['host_limit_per_task'] != 2 or
            config['seeds'] != [20261020, 20261021, 20261022] or config['percentages'] != [0, .25, .5, 1, 2, 5, 10] or
            config['modes'] != ['append_legacy', 'near_tissue', 'replacement', 'within_region_context']):
        raise ValueError('Preregistered bounded training-only acceptance configuration required')
    if config['schema_version'] in (2, 3) and (not predictor_path or config['tasks'] != {'s1': ['cancer'], 's2': ['high_gp45', 'same_grade_gp3_only']}):
        raise ValueError('S2 v2 requires the frozen improved predictor and predeclared same-grade controls')
    sources, receipt = _load_training(manifest, directories, encoded, verification)
    identity = dict(manifest_sha256=file_hash(manifest), directories_sha256=file_hash(directories),
        verification_sha256=file_hash(verification), text_fingerprint=receipt['text_fingerprint'],
        input_identities={sid: slide_identity(s['slide']) for sid, s in sources.items()})
    improved = None
    if predictor_path:
        from ..predictors import load_predictor
        improved = load_predictor(predictor_path)
        identity['predictor_files'] = {n: file_hash(Path(predictor_path)/n) for n in ('predictor.json', 'parameters.npz')}
        selection_path = Path(predictor_path).parents[2]/'selection_frozen.json'
        if config.get('predictor_selection_sha256') and file_hash(selection_path) != config['predictor_selection_sha256']:
            raise ValueError('Frozen training-only predictor selection changed')
        if config.get('predictor_selection_sha256'):
            selection = json.loads(selection_path.read_text())
            selected = selection['tasks']['low_high']
            if (selected['primary'] != improved.spec['model_id'] or not selected['s2_engineering_readiness'] or
                    selection['calibration_opened_for_selection'] or selection['test_slides_scored'] or
                    improved.spec['classes'] != ['low_grade', 'high_grade']):
                raise ValueError('Training-only low/high predictor readiness/identity gate failed')
            identity['predictor_selection_sha256'] = file_hash(selection_path)
    frozen = dict(protocol=config, protocol_sha256=file_hash(protocol), input_identity=identity,
                  predictor_selected_before_contaminated_predictions=True)
    registry = Registry(output, ExperimentRun(config['experiment_id'], config['hypothesis'], source_commit,
        canonical(frozen), identity['manifest_sha256'], 'train', next(iter(sources.values()))['slide'].metadata['model']['checkpoint_sha256'],
        receipt['text_fingerprint'], canonical(dict(cpus=2, memory_gb=4, maximum_minutes=15, gpu=0))))
    state = registry.report()['status']
    if state == 'verified':
        return registry.load_checkpoint('summary')
    if state is None:
        registry.status('planned')
    registry.status('running', slurm_job_id=os.environ['SLURM_JOB_ID'])
    trials, exclusions, selected_hosts, geometry = [], [], {}, {}
    try:
        reused = 0
        if config.get('resume_prior_run'):
            previous = config['resume_prior_run']
            prior_root = Path(previous['path'])
            if file_hash(prior_root/'run.json') != previous['run_sha256']:
                raise ValueError('Prior checkpoint registry identity changed')
            prior_metadata = json.loads((prior_root/'run.json').read_text())
            prior_run = ExperimentRun(**prior_metadata['run'])
            prior_frozen = json.loads(prior_run.config_json)
            if prior_frozen['input_identity'] != identity:
                raise ValueError('Cannot reuse checkpoints with different inputs/predictor')
            if any(prior_frozen['protocol'][k] != config[k] for k in ('tasks', 'seeds', 'percentages', 'host_limit_per_task', 'donors_per_host')):
                raise ValueError('Cannot reuse checkpoints with different intervention selection')
            prior_registry = Registry(prior_root, prior_run)
            if prior_registry.report()['status'] != 'failed':
                raise ValueError('Only the explicitly documented failed run may supply retry checkpoints')
            for event in prior_registry.events():
                if event['kind'] == 'checkpoint':
                    registry.checkpoint(event['key'], prior_registry.load_checkpoint(event['key']))
                    reused += 1
        tasks = [(task, condition) for task, values in config['tasks'].items() for condition in ([values] if isinstance(values, str) else values)]
        for task, condition in tasks:
            grade = 0 if task == 's1' else 1
            hosts = sorted(sid for sid, s in sources.items() if s['slide'].metadata['isup_grade'] == grade)[:config['host_limit_per_task']]
            selected_hosts[task] = hosts
            selection = DonorSelection(condition, config['minimum_native_pattern_fraction'], tuple(config['seeds']), config['donors_per_host'])
            labels = ('benign', 'cancer') if task == 's1' else ('low_grade', 'high_grade')
            for sid in hosts:
                source, host = sources[sid], sources[sid]['slide']
                if sid not in geometry:
                    geometry[sid] = _occupancy(source, registry, receipts, output)
                occupancy, overview = geometry[sid]
                scorer = (lambda s: _primary(binary_predictions(s, source['text']), task)) if task == 's1' else (
                    improved.score_slide if improved else lambda s: _primary(grade_predictions(s, source['text']), task))
                baseline = scorer(host)
                for seed in config['seeds']:
                    donors = select_donors(host, sources, selection, task, 10, seed)
                    if not donors:
                        exclusions.append(dict(task=task, condition=condition, host_id=sid, seed=seed, reason='No eligible same-split annotated connected donor'))
                    # Same-source sham uses the native host, and cannot be labelled foreign tissue.
                    native_part = tile_components(host)[0]
                    native_count = min(foreign_count(10, len(host.feats)), len(native_part))
                    native_order = native_part[connected_fragment(host.subset(native_part), native_count, seed)]
                    first_condition = config['tasks'][task] if isinstance(config['tasks'][task], str) else config['tasks'][task][0]
                    if condition == first_condition:
                        donors.append(dict(donor_id=sid, indices=native_order.tolist(), component_capacity=len(native_order), sham=True))
                    for pairing in donors:
                        did, order = pairing['donor_id'], np.array(pairing['indices'], dtype=int)
                        donor, sham = sources[did]['slide'], pairing.get('sham', False)
                        pair_condition = 'same_source_sham' if sham else condition
                        anchors, placement_failures = {}, {}
                        for mode, placement_seed in [('near_tissue', seed), ('within_region_context', seed+1_000_003)]:
                            try:
                                anchors[mode] = placement_anchor(host, donor, order, occupancy, placement_seed)-donor.coords[order].min(axis=0)
                            except ValueError as error:
                                placement_failures[mode] = str(error)
                        # Native connected target region is sampled without annotations.
                        target_part = tile_components(host)[0]
                        target_count = min(len(order), len(target_part))
                        target_order = target_part[connected_fragment(host.subset(target_part), target_count, seed+37)]
                        for percent in config['percentages']:
                            count = foreign_count(percent, len(host.feats))
                            control = 'same_source_sham' if sham else ('same_grade_donor' if condition == 'same_grade_gp3_only' else 'annotated_donor')
                            if count > len(order):
                                for mode in config['modes']:
                                    key = f'{task}-{condition}-{sid}-{did}-{seed}-{percent:g}-{mode}'
                                    exclusion = dict(excluded=True, task=task, condition=condition, host_id=sid, donor_id=did, seed=seed,
                                        requested_percent=percent, mode=mode, control=control, reason='Fixed donor lacks unique connected capacity',
                                        requested_count=count, capacity=len(order))
                                    registry.checkpoint(key, exclusion); exclusions.append(exclusion)
                                continue
                            indices = order[:count]
                            append_spec = InterventionSpec(task, pair_condition, 'append_legacy', percent, seed, tuple(indices))
                            appended = apply_intervention(host, donor, append_spec)
                            append_prediction = scorer(appended.slide)
                            for mode in config['modes']:
                                key = f'{task}-{condition}-{sid}-{did}-{seed}-{percent:g}-{mode}'
                                cached = registry.load_checkpoint(key)
                                if cached is not None:
                                    (exclusions if cached.get('excluded') else trials).append(cached)
                                    continue
                                if mode == 'replacement' and count > len(target_order):
                                    placement_failures['replacement'] = 'Host lacks connected replacement-region capacity'
                                if count and mode in placement_failures:
                                    exclusion = dict(excluded=True, task=task, condition=condition, host_id=sid, donor_id=did, seed=seed,
                                        requested_percent=percent, mode=mode, control=control, reason=placement_failures[mode])
                                    registry.checkpoint(key, exclusion); exclusions.append(exclusion)
                                    continue
                                anchor = tuple((donor.coords[indices].min(axis=0)+anchors[mode]).tolist()) if count and mode in anchors else None
                                spec = replace(append_spec, mode=mode, placement_anchor_um=anchor,
                                    replacement_indices=tuple(target_order[:count]) if mode == 'replacement' else (),
                                    context='alternative observed tissue-boundary context; no histological compartment asserted' if mode == 'within_region_context' else None)
                                if mode in ('near_tissue', 'within_region_context'):
                                    # A maximal fragment may be near tissue while a smaller nested prefix is not.
                                    try:
                                        placement_anchor(host, donor, indices, occupancy, seed, spec.placement_anchor_um)
                                    except ValueError as error:
                                        exclusion = dict(excluded=True, task=task, condition=condition, host_id=sid, donor_id=did, seed=seed,
                                            requested_percent=percent, mode=mode, control=control, reason='Fixed nested placement ineligible at this dose: '+str(error))
                                        registry.checkpoint(key, exclusion); exclusions.append(exclusion)
                                        continue
                                result = apply_intervention(host, donor, spec, occupancy=occupancy)
                                restored = result.verify(scorer)
                                _same_slide(host, restored)
                                prediction = scorer(result.slide)
                                legacy_exact = False
                                if mode == 'append_legacy' and not sham:
                                    old = inject_development_s1(host, donor, indices, percent, seed) if task == 's1' else legacy_grade_inject(host, donor, indices, percent, seed, condition)
                                    _same_slide(old, result.slide)
                                    if scorer(old) != prediction:
                                        raise RuntimeError('Exact legacy prediction disagreement')
                                    legacy_exact = True
                                invariant = None
                                if mode in ('near_tissue', 'within_region_context'):
                                    invariant = np.array_equal(result.slide.feats, appended.slide.feats) and prediction == append_prediction
                                    if not invariant:
                                        raise RuntimeError('Coordinate-only bag prediction changed; stop')
                                row = dict(task=task, condition=condition, mode=mode, control=control,
                                    host_id=sid, donor_id=did, seed=seed, requested_percent=percent, realized_percent=100*count/len(host.feats),
                                    host_tiles=len(host.feats), donor_tiles=count, donor_indices=indices.tolist(),
                                    donor_tile_ids=donor.tile_ids[indices].tolist(), host_truth=labels[0], baseline=baseline,
                                    contaminated=prediction, oracle=scorer(restored), oracle_exact_recovery=True,
                                    margin_shift=_margin(prediction, labels)-_margin(baseline, labels),
                                    legacy_exact_match=legacy_exact, coordinate_only_bag_invariant=invariant,
                                    intervention_audit=json.loads(result.audit_json), synthetic_injection={k: v for k, v in result.slide.metadata['injection'].items() if k != 'host_metadata'})
                                registry.checkpoint(key, row); trials.append(row)
        result = dict(_summary(trials, exclusions), source_commit=source_commit, slurm_job_id=os.environ['SLURM_JOB_ID'],
            selected_hosts=selected_hosts, selected_before_outcomes=True, input_identity=identity,
            s2_training_stress_is_resubstitution=bool(improved), reused_verified_prior_checkpoints=reused,
            s2_v2_full_cohort_completed=False, independent_validation_required=True,
            predictor_kind='training-selected improved S2' if improved else 'historical fixed S1 top5/S2 mean',
            clinical_interpretation='No clinical validity or foreignness diagnosis established; placement is representation-only',
            geometry={sid: record for sid, (_, record) in geometry.items()})
        registry.checkpoint('exclusions', exclusions)
        registry.checkpoint('summary', result)
        registry.status('verified', validation=True, interpretation='Exact legacy/oracle checks pass; spatial-only order-invariant predictions remain identical',
            limitations=['Four training hosts only; no independent validation', 'Mask is bounded observed RGB proxy, not histological tissue proof',
                         'Repeated seeds/donors are not independent patients', 'Coordinates do not affect an order-invariant bag scorer'], slurm_job_id=os.environ['SLURM_JOB_ID'])
        return result
    except BaseException as error:
        registry.status('failed', validation=False, interpretation=type(error).__name__+': '+str(error), slurm_job_id=os.environ['SLURM_JOB_ID'])
        raise
