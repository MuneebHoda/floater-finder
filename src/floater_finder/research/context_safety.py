"""Original-training safety accounting from sealed JSON; no new image/model reads."""
import csv
import json
import math
import os
from pathlib import Path

from ..detectors.context_eligibility import assess_context
from ..experiments import file_sha256
from .contracts import ExperimentRun, canonical, fingerprint
from .registry import Registry
from .topology_context import context_support, crosswalk


def read_sealed(root):
    """Read without constructing Registry, which would open its writer lock."""
    root = Path(root); metadata = json.loads((root/'run.json').read_text())
    identity = fingerprint(metadata['run'])
    if identity != metadata['identity']:
        raise ValueError('Input registry identity changed')
    previous = identity; artifacts = {}; statuses = []
    paths = sorted((root/'events').glob('*.json'))
    for sequence, path in enumerate(paths):
        row = json.loads(path.read_text()); digest = row.pop('event_sha256')
        if (path.name != f'{sequence:06d}.json' or row['sequence'] != sequence or
                row['previous_sha256'] != previous or fingerprint(row) != digest):
            raise ValueError('Input registry event chain changed')
        previous = digest
        if row['kind'] == 'status':
            statuses.append(row['status'])
        for entry in row.get('artifacts', []):
            target = root/entry['path']
            if (root.resolve() not in target.resolve().parents or entry['path'] in artifacts or
                    file_sha256(target) != entry['sha256']):
                raise ValueError('Input registry checkpoint changed')
            artifacts[entry['path']] = entry['sha256']
    expected = dict(events=len(paths), last_sha256=previous, run_identity=identity)
    if (json.loads((root/'seal.json').read_text()) != expected or
            statuses != ['planned', 'running', 'verified']):
        raise ValueError('Verified sealed input registry required')
    return metadata['run'], artifacts


def audit_checkpoint(row):
    """Apply truth-free gates first; attach native annotation controls afterward."""
    n = row['tiles']; components = row['components']
    if type(n) is not int or n < 1 or set(components) != {'rgb_cached', 'sampled'}:
        raise ValueError('Positive saved tile count and both frozen topologies required')
    expected = crosswalk(components['rgb_cached'], components['sampled'], n)
    if (expected != row['crosswalk'] or row['classification_predictions_computed'] is not False or
            row['complete_physical_piece_boundaries_verified'] is not False or
            not math.isclose(row['mapping_fraction'], expected['mapped_tiles']/n, abs_tol=1e-12, rel_tol=0)):
        raise ValueError('Frozen checkpoint topology/provenance differs')
    unmapped = set(range(n)) - {i for p in components['rgb_cached'] for i in p['indices']}
    result = {}
    for kind, parts in components.items():
        measured = []
        for number, part in enumerate(parts):
            support = context_support(len(part['indices']), n)
            inside_unknown = len(set(part['indices']) & unmapped)
            if (part['component_index'] != number or any(part[k] != v for k, v in support.items()) or
                    part['unassigned_rgb_tiles_in_candidate'] != inside_unknown or
                    part['unassigned_rgb_tiles_in_remaining_context'] != len(unmapped)-inside_unknown or
                    not math.isfinite(part['occupied_area_mm2']) or part['occupied_area_mm2'] <= 0):
                raise ValueError('Saved component geometry/context differs')
            gate = assess_context(part['tile_count'], n, part['score'])
            measured.append(dict(component_index=number, eligibility=gate,
                occupied_area_mm2=part['occupied_area_mm2'],
                observed_rgb_tissue_area_mm2=part['observed_rgb_tissue_area_mm2'],
                unassigned_rgb_tiles_in_candidate=inside_unknown,
                unassigned_rgb_tiles_in_comparison=len(unmapped)-inside_unknown))
        # Annotation fields cannot affect gate construction or eligibility.
        for measured_part, part in zip(measured, parts):
            known = part['evaluation_annotation_known_tiles']
            cancer = part['evaluation_native_annotation_positive_tiles']
            if (type(known) is not int or type(cancer) is not int or
                    not 0 <= cancer <= known <= part['tile_count']):
                raise ValueError('Valid evaluation-only native annotation counts required')
            measured_part.update(evaluation_annotation_known_tiles=known,
                evaluation_native_annotation_positive_tiles=cancer,
                evaluation_annotation_unknown_tiles=part['tile_count']-known)
        result[kind] = measured
    return dict(host_id=row['host_id'], source_identity=row['source_identity'], components=result,
        review_alert=None, foreignness=None, automatic_tissue_action='none')


def summarize(rows):
    summaries = []
    for kind in ('rgb_cached', 'sampled'):
        groups = [dict(p, host_id=r['host_id']) for r in rows for p in r['components'][kind]]
        strata = []
        for name, selected in (
                ('all_components', groups),
                ('nn5_support_only', [p for p in groups if p['eligibility']['comparison_tiles'] >= 6]),
                ('conservative_eligible', [p for p in groups if p['eligibility']['eligible_for_numeric_comparison']]),
                ('conservative_abstained', [p for p in groups if not p['eligibility']['eligible_for_numeric_comparison']])):
            scores = [p['eligibility']['diagnostic_score'] for p in selected if p['eligibility']['diagnostic_score'] is not None]
            strata.append(dict(stratum=name, components=len(selected), unique_slides=len({p['host_id'] for p in selected}),
                native_annotation_positive_components=sum(p['evaluation_native_annotation_positive_tiles'] > 0 for p in selected),
                native_annotation_positive_slides=len({p['host_id'] for p in selected if p['evaluation_native_annotation_positive_tiles'] > 0}),
                annotation_unknown_components=sum(p['evaluation_annotation_unknown_tiles'] > 0 for p in selected),
                with_unassigned_comparison_tiles=sum(p['unassigned_rgb_tiles_in_comparison'] > 0 for p in selected),
                diagnostic_score_range=[min(scores), max(scores)] if scores else None))
        reasons = {reason:sum(reason in p['eligibility']['reasons'] for p in groups)
            for reason in ('fewer_than_six_comparison_tiles', 'candidate_is_majority_of_sampled_bag')}
        summaries.append(dict(topology=kind, strata=strata, abstention_reasons_overlapping=reasons,
            slides_without_eligible_comparison=sum(not any(p['eligibility']['eligible_for_numeric_comparison']
                for p in r['components'][kind]) for r in rows)))
    return dict(slides=len(rows), topologies=summaries, classification_predictions_computed=False,
        thresholds_fitted=False, review_alert_rate=None, foreign_fragment_recall=None,
        genuine_tissue_prediction_harm=None, final_test_ready=False, automatic_tissue_action='none',
        interpretation='Training-only numeric eligibility coverage and native controls; not a review policy or foreignness validation')


def preflight(config_path, expected_sha256, project, check_inputs=False):
    if file_sha256(config_path) != expected_sha256:
        raise ValueError('Frozen context-safety protocol changed')
    c = json.loads(Path(config_path).read_text()); project = Path(project)
    if (c['schema_version'] != 1 or c['experiment_id'] != 'panda_context_safety_v1' or
            c['split'] != 'train' or c['slides'] != 72 or c['minimum_comparison_tiles'] != 6 or
            c['majority_veto'] is not True or c['classification_predictions'] or c['fit_thresholds'] or
            c['resources'] != dict(cpus=2, memory_gb=4, maximum_minutes=5, gpu=0)):
        raise ValueError('Fixed training-only context-safety scope required')
    required = {'src/floater_finder/'+n for n in ('detectors/context_eligibility.py', 'research/context_safety.py',
        'research/topology_context.py', 'research/registry.py', 'research/contracts.py')}
    required |= {'scripts/panda_context_safety.py', 'scripts/slurm/panda_context_safety.sbatch'}
    if not required.issubset(c['source_files']):
        raise ValueError('Incomplete context-safety source freeze')
    if (Path(c['audit_protocol']).is_absolute() or '..' in Path(c['audit_protocol']).parts or
            file_sha256(project/c['audit_protocol']) != c['audit_protocol_sha256']):
        raise ValueError('Original topology protocol differs')
    root = Path(c['audit_root'])
    for name, relative in [('audit_run', 'run.json'), ('audit_seal', 'seal.json'), ('audit_summary', 'checkpoints/summary.json')]:
        if Path(c['inputs'][name]['path']) != root/relative:
            raise ValueError('Pinned audit receipt paths differ')
    for name, digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name) != digest:
            raise ValueError('Frozen context-safety source differs: '+name)
    if check_inputs:
        for entry in c['inputs'].values():
            if file_sha256(entry['path']) != entry['sha256']:
                raise ValueError('Pinned context-safety input differs')
        if Path(c['output']).exists():
            raise FileExistsError('Preserve existing context-safety outputs')
        if not Path(c['output']).parent.is_dir():
            raise ValueError('Verified output parent required')
    return c


def run(config_path, expected_sha256, project, output, source_commit, execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Explicit bounded CPU Slurm execution required')
    c = preflight(config_path, expected_sha256, project, check_inputs=True)
    if Path(output).resolve() != Path(c['output']).resolve():
        raise ValueError('Exact new context-safety output required')
    old, artifacts = read_sealed(c['audit_root'])
    audit_config = json.loads((Path(project)/c['audit_protocol']).read_text())
    if (old['experiment_id'] != 'panda_topology_context_v1' or old['split'] != 'train' or
            old['source_commit'] != c['audit_source_commit'] or json.loads(old['config_json']) != audit_config or
            old['dataset_identity'] != c['inputs']['manifest']['sha256']):
        raise ValueError('Original frozen training audit required')
    with Path(c['inputs']['manifest']['path']).open(newline='') as handle:
        ids = [r['image_id'] for r in csv.DictReader(handle) if r['split'] == 'train']
    expected = {'checkpoints/slide-'+sid+'.json' for sid in ids} | {'checkpoints/summary.json'}
    if len(ids) != 72 or len(set(ids)) != 72 or set(artifacts) != expected:
        raise ValueError('Exactly the original 72 training checkpoints required')
    registry = Registry(output, ExperimentRun(c['experiment_id'], c['hypothesis'], source_commit, canonical(c),
        old['dataset_identity'], 'train', old['checkpoint_fingerprint'], old['embedding_fingerprint'], canonical(c['resources'])))
    registry.status('planned'); registry.status('running', slurm_job_id=os.environ['SLURM_JOB_ID']); rows = []
    try:
        for sid in ids:
            original = json.loads((Path(c['audit_root'])/'checkpoints'/('slide-'+sid+'.json')).read_text())
            if original['host_id'] != sid:
                raise ValueError('Training checkpoint identity differs')
            row = audit_checkpoint(original); rows.append(row); registry.checkpoint('slide-'+sid, row)
        summary = summarize(rows); registry.checkpoint('summary', summary)
        # Reverify the sealed input after all reads; never modify it or its lock.
        if read_sealed(c['audit_root']) != (old, artifacts):
            raise ValueError('Original audit changed during context-safety accounting')
        registry.status('verified', validation=True, interpretation=summary['interpretation'])
        return summary
    except BaseException as exc:
        registry.status('failed', interpretation=type(exc).__name__+': '+str(exc)); raise
