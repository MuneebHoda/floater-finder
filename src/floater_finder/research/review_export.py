"""Frozen training-only report export from saved evidence, without model calls."""
import csv
import json
import os
from pathlib import Path
import re

from ..experiments import file_sha256
from ..review_report import evidence_from_case, build_report, render_html, render_index
from .context_safety import read_sealed
from .contracts import ExperimentRun, canonical
from .registry import Registry


def preflight(config_path, expected_sha256, project, check_inputs=False):
    if file_sha256(config_path) != expected_sha256:
        raise ValueError('Frozen dependence-export protocol changed')
    c = json.loads(Path(config_path).read_text()); project = Path(project)
    if (c['schema_version'] != 1 or c['experiment_id'] != 'panda_dependence_export_v1' or
            c['split'] != 'train' or c['slides'] != 72 or c['components'] != 389 or
            c['topology'] != 'rgb_cached' or c['scorer']['name'] != 'legacy_conch_v1_zero_shot_top5pct' or
            c['scorer']['classes'] != ['benign', 'cancer'] or c['scorer']['pooling'] != 'top5pct' or
            c['new_predictions'] or c['fit_thresholds'] or c['automatic_tissue_action'] != 'none' or
            c['resources'] != dict(cpus=2, memory_gb=4, maximum_minutes=5, gpu=0)):
        raise ValueError('Fixed training-only saved dependence scope required')
    required = {'src/floater_finder/'+p for p in ('review_report.py', 'research/review_export.py',
        'research/context_safety.py', 'detectors/context_eligibility.py', 'research/contracts.py', 'research/registry.py')}
    required |= {'scripts/panda_dependence_export.py', 'scripts/slurm/panda_dependence_export.sbatch',
        'configs/panda_morphology_v1.yaml', 'configs/panda_review_development_v1.json'}
    if not required.issubset(c['source_files']):
        raise ValueError('Incomplete dependence-export source freeze')
    for name, digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name) != digest:
            raise ValueError('Frozen dependence-export source differs: '+name)
    for prefix in ('topology', 'safety'):
        for suffix, relative in [('run', 'run.json'), ('seal', 'seal.json'), ('summary', 'checkpoints/summary.json')]:
            if Path(c['inputs'][prefix+'_'+suffix]['path']) != Path(c[prefix+'_root'])/relative:
                raise ValueError('Pinned registry receipt paths differ')
    if check_inputs:
        for e in c['inputs'].values():
            if file_sha256(e['path']) != e['sha256']:
                raise ValueError('Saved dependence input differs')
        if Path(c['output']).exists():
            raise FileExistsError('Preserve existing dependence reports')
        if not Path(c['output']).parent.is_dir():
            raise ValueError('Verified report output parent required')
    return c


def summarize(records):
    parts = [dict(p, host_id=r['report']['host_id']) for r in records for p in r['report']['components']]
    controls = [dict(p, host_id=r['report']['host_id']) for r in records for p in r['evaluation_only_controls']]
    changing = [p for p in parts if p['decision_change'] is True]
    return dict(slides=len(records), components=len(parts), decision_evaluable_components=sum(p['decision_change'] is not None for p in parts),
        decision_changing_components=len(changing), slides_with_decision_dependence=len({p['host_id'] for p in changing}),
        decision_changing_supported=sum(p['context']['eligible_for_numeric_comparison'] for p in changing),
        decision_changing_abstained=sum(not p['context']['eligible_for_numeric_comparison'] for p in changing),
        annotation_positive_decisive_components=sum(p['annotation_positive'] and p['decision_change'] is True for p in controls),
        annotation_positive_decisive_slides=len({p['host_id'] for p in controls if p['annotation_positive'] and p['decision_change'] is True}),
        annotation_unknown_components=sum(p['annotation_unknown'] for p in controls),
        new_predictions_computed=False, thresholds_fitted=False, review_alert_rate=None, foreign_fragment_recall=None,
        automatic_tissue_action='none', final_test_ready=False,
        interpretation='Saved original-training dependence display and native-control accounting; no new performance evaluation or review policy')


def run(config_path, expected_sha256, project, output, source_commit, execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Explicit bounded CPU Slurm execution required')
    c = preflight(config_path, expected_sha256, project, check_inputs=True); output = Path(output)
    if output.resolve() != Path(c['output']).resolve():
        raise ValueError('Exact new dependence-report output required')
    prior = {name:read_sealed(c[name+'_root']) for name in ('topology', 'safety')}
    old, old_artifacts = prior['topology']; safety_run, safety_artifacts = prior['safety']
    for name, (saved, _) in prior.items():
        if (saved['split'] != 'train' or saved['source_commit'] != c[name+'_source_commit'] or
                saved['dataset_identity'] != c['inputs']['manifest']['sha256'] or
                saved['experiment_id'] != c[name+'_experiment_id']):
            raise ValueError('Original frozen training registry provenance required')
    if any(old[k] != safety_run[k] for k in ('dataset_identity', 'checkpoint_fingerprint', 'embedding_fingerprint')):
        raise ValueError('Saved report evidence model identities differ')
    with Path(c['inputs']['manifest']['path']).open(newline='') as f:
        ids = [r['image_id'] for r in csv.DictReader(f) if r['split'] == 'train']
    expected = {'checkpoints/slide-'+sid+'.json' for sid in ids} | {'checkpoints/summary.json'}
    if (len(ids) != 72 or len(set(ids)) != 72 or any(not re.fullmatch('[a-f0-9]{32}', sid) for sid in ids) or
            set(old_artifacts) != expected or set(safety_artifacts) != expected):
        raise ValueError('Exactly 72 original training checkpoints required')
    all_cases = json.loads(Path(c['inputs']['cases']['path']).read_text())
    if any(r['split'] == 'test' for r in all_cases):
        raise ValueError('Final test cases forbidden')
    selected = [r for r in all_cases if r['split'] == 'train' and r['kind'] == 'unmodified']
    cases = {r['host_id']:r for r in selected}
    if len(cases) != len(selected) or set(cases) != set(ids) or any(any(r['foreign_mask']) for r in selected):
        raise ValueError('Exact original unmodified training evidence required')
    registry = Registry(output, ExperimentRun(c['experiment_id'], c['hypothesis'], source_commit, canonical(c),
        old['dataset_identity'], 'train', old['checkpoint_fingerprint'], old['embedding_fingerprint'], canonical(c['resources'])))
    registry.status('planned'); registry.status('running', slurm_job_id=os.environ['SLURM_JOB_ID'])
    records = []; rendered = {}; (output/'reports').mkdir()
    provenance = dict(source_kind='real', source_commit=source_commit, protocol_sha256=expected_sha256,
        cases_sha256=c['inputs']['cases']['sha256'], manifest_sha256=old['dataset_identity'],
        checkpoint_sha256=old['checkpoint_fingerprint'], text_fingerprint=old['embedding_fingerprint'],
        scorer=c['scorer'], final_test_predictions_computed=False)
    try:
        for sid in ids:
            relative = 'checkpoints/slide-'+sid+'.json'
            topology = json.loads((Path(c['topology_root'])/relative).read_text())
            safety = json.loads((Path(c['safety_root'])/relative).read_text())
            report = build_report(evidence_from_case(cases[sid]), topology, safety, provenance)
            # Truth joins only after the complete reviewer-facing report is built.
            controls = [dict(component_index=p['component_index'], decision_change=p['decision_change'],
                annotation_positive=s['evaluation_native_annotation_positive_tiles'] > 0,
                annotation_unknown=s['evaluation_annotation_unknown_tiles'] > 0)
                for p, s in zip(report['components'], safety['components']['rgb_cached'])]
            record = dict(report=report, evaluation_only_controls=controls); records.append(record)
            for extension, content in [('json', canonical(report)+'\n'), ('html', render_html(report))]:
                name = 'reports/'+sid+'.'+extension
                with (output/name).open('x') as handle: handle.write(content)
                rendered[name] = file_sha256(output/name)
            registry.checkpoint('slide-'+sid, record)
        with (output/'index.html').open('x') as handle: handle.write(render_index([r['report'] for r in records]))
        rendered['index.html'] = file_sha256(output/'index.html')
        summary = summarize(records)
        if summary['components'] != c['components']:
            raise ValueError('Frozen RGB component workload changed')
        summary['rendered_file_sha256'] = rendered; registry.checkpoint('summary', summary)
        if (any(file_sha256(output/name) != digest for name, digest in rendered.items()) or
                any(read_sealed(c[name+'_root']) != value for name, value in prior.items()) or
                any(file_sha256(e['path']) != e['sha256'] for e in c['inputs'].values())):
            raise ValueError('Source or rendered evidence mutated during export')
        registry.status('verified', validation=True, interpretation=summary['interpretation']); return summary
    except BaseException as exc:
        registry.status('failed', interpretation=type(exc).__name__+': '+str(exc)); raise
