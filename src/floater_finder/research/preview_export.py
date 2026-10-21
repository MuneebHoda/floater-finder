"""Bounded Delta-only training PNG galleries on top of sealed dependence reports."""
import csv
import json
import os
from pathlib import Path
import re

from ..experiments import file_sha256
from ..review_previews import attach_previews, render_preview_html
from ..review_report import render_index
from .context_safety import read_sealed
from .contracts import ExperimentRun, canonical
from .registry import Registry


def preflight(config_path, expected_sha256, project, check_inputs=False):
    if file_sha256(config_path) != expected_sha256:
        raise ValueError('Frozen preview-export protocol changed')
    c = json.loads(Path(config_path).read_text()); project = Path(project)
    if (c['schema_version'] != 1 or c['experiment_id'] != 'panda_preview_export_v1' or
            c['split'] != 'train' or c['slides'] != 72 or c['components'] != 389 or
            c['examples_per_panel'] != 4 or c['maximum_tile_references'] != 3112 or
            c['maximum_copied_png_bytes'] != 512*1024*1024 or c['new_predictions'] or c['fit_thresholds'] or
            c['resources'] != dict(cpus=2, memory_gb=4, maximum_minutes=5, gpu=0)):
        raise ValueError('Fixed training-only bounded preview scope required')
    required = {'src/floater_finder/'+p for p in ('review_previews.py','research/preview_export.py','review_report.py',
        'research/context_safety.py','research/contracts.py','research/registry.py')}
    required |= {'scripts/panda_preview_export.py','scripts/slurm/panda_preview_export.sbatch'}
    if not required.issubset(c['source_files']): raise ValueError('Incomplete preview source freeze')
    for name,digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name) != digest:
            raise ValueError('Frozen preview source differs: '+name)
    for key,relative in [('report_run','run.json'),('report_seal','seal.json'),('report_summary','checkpoints/summary.json')]:
        if Path(c['inputs'][key]['path']) != Path(c['report_root'])/relative:
            raise ValueError('Pinned report receipt paths differ')
    if check_inputs:
        for e in c['inputs'].values():
            if file_sha256(e['path']) != e['sha256']: raise ValueError('Pinned preview input differs')
        if Path(c['output']).exists(): raise FileExistsError('Preserve all prior preview/report outputs')
        if not Path(c['output']).parent.is_dir(): raise ValueError('Verified output parent required')
    return c


def tile_source(sid, directory, encoded_root, verified, report):
    """Metadata/order verification only; never open NPZs, WSIs or annotation masks."""
    completion_path = Path(encoded_root)/sid/'completion.json'
    if file_sha256(completion_path) != verified['completion_sha256']:
        raise ValueError('Original embedding completion receipt differs')
    completion = json.loads(completion_path.read_text()); identity = completion['input_identity']
    for name,key in [('tiles.csv','manifest_sha256'),('metadata.json','metadata_sha256')]:
        if file_sha256(directory/name) != identity[key]: raise ValueError('Original tiling input identity differs')
    with (directory/'tiles.csv').open(newline='') as handle: rows = list(csv.DictReader(handle))
    metadata = json.loads((directory/'metadata.json').read_text())
    if (len(rows) != report['tile_count'] or metadata['project'] != 'PANDA' or metadata['data_provider'] != 'radboud' or
            metadata['cohort_split'] != 'train' or metadata['source_kind'] != 'real' or
            metadata['extraction']['sampling_mode'] != 'representative' or metadata['extraction']['selection_uses_mask'] or
            identity['checkpoint_sha256'] != report['provenance']['checkpoint_sha256'] or
            completion['cohort_split'] != 'train'):
        raise ValueError('Only original unbiased training exports with matching CONCH identity required')
    receipt = dict(completion_path=str(completion_path),completion_sha256=verified['completion_sha256'],
        directory=str(directory),manifest_sha256=identity['manifest_sha256'],metadata_sha256=identity['metadata_sha256'])
    return rows,metadata,identity['png_sha256'],receipt


def run(config_path, expected_sha256, project, output, source_commit, execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Explicit bounded CPU Slurm execution required')
    c = preflight(config_path,expected_sha256,project,check_inputs=True); output = Path(output)
    if output.resolve() != Path(c['output']).resolve(): raise ValueError('Exact new preview output required')
    old,artifacts = read_sealed(c['report_root'])
    if (old['experiment_id'] != 'panda_dependence_export_v1' or old['split'] != 'train' or
            old['source_commit'] != c['report_source_commit'] or old['dataset_identity'] != c['inputs']['manifest']['sha256']):
        raise ValueError('Exact original sealed training reports required')
    with Path(c['inputs']['manifest']['path']).open(newline='') as handle:
        ids = [r['image_id'] for r in csv.DictReader(handle) if r['split']=='train']
    expected = {'checkpoints/slide-'+sid+'.json' for sid in ids} | {'checkpoints/summary.json'}
    if len(ids) != 72 or len(set(ids)) != 72 or any(not re.fullmatch('[a-f0-9]{32}',sid) for sid in ids) or set(artifacts) != expected:
        raise ValueError('Exactly original 72 training reports required')
    saved = json.loads((Path(c['report_root'])/'checkpoints/summary.json').read_text())
    if saved['components'] != c['components']: raise ValueError('Frozen report component workload differs')
    receipt = json.loads(Path(c['inputs']['verification']['path']).read_text())
    if receipt['manifest_sha256'] != c['inputs']['manifest']['sha256']: raise ValueError('Manifest/verification identity differs')
    verified = {r['image_id']:r for r in receipt['records'] if r['image_id'] in ids}
    paths = [Path(p) for p in json.loads(Path(c['inputs']['directories']['path']).read_text())]
    registry = Registry(output,ExperimentRun(c['experiment_id'],c['hypothesis'],source_commit,canonical(c),
        old['dataset_identity'],'train',old['checkpoint_fingerprint'],old['embedding_fingerprint'],canonical(c['resources'])))
    registry.status('planned'); registry.status('running',slurm_job_id=os.environ['SLURM_JOB_ID'])
    (output/'reports').mkdir(); (output/'tiles').mkdir(); records=[]; rendered={}; sources=[]; total_bytes=0; references=0
    try:
        for sid in ids:
            matches = [p for p in paths if sid in p.parts]
            if len(matches) != 1 or sid not in verified: raise ValueError('Unique verified training tiling directory required')
            original = json.loads((Path(c['report_root'])/'checkpoints'/('slide-'+sid+'.json')).read_text())
            report = original['report']; public = 'reports/'+sid+'.json'
            if (report['host_id'] != sid or file_sha256(Path(c['report_root'])/public) != saved['rendered_file_sha256'][public] or
                    json.loads((Path(c['report_root'])/public).read_text()) != report):
                raise ValueError('Old reviewer JSON differs from sealed report')
            rows,metadata,hashes,source = tile_source(sid,matches[0],c['encoded_root'],verified[sid],report)
            upgraded,assets = attach_previews(report,rows,metadata,hashes,matches[0],output/'tiles',c['maximum_copied_png_bytes']-total_bytes)
            upgraded['preview_provenance'] = dict(source_commit=source_commit,protocol_sha256=expected_sha256,
                saved_report_sha256=saved['rendered_file_sha256'][public],tiling_manifest_sha256=source['manifest_sha256'],
                tiling_metadata_sha256=source['metadata_sha256'],embedding_completion_sha256=source['completion_sha256'])
            total_bytes += sum(a['bytes'] for a in assets.values())
            references += sum(len(p['previews'][role]) for p in upgraded['components'] for role in ('component','outside'))
            if references > c['maximum_tile_references']: raise ValueError('Frozen preview reference bound exceeded')
            record = dict(report=upgraded,evaluation_only_controls=original['evaluation_only_controls'],source=source,png_assets=assets)
            records.append(record);sources.append(source)
            for name,value in assets.items(): rendered[name] = value['sha256']
            for extension,content in [('json',canonical(upgraded)+'\n'),('html',render_preview_html(upgraded))]:
                name = 'reports/'+sid+'.'+extension
                with (output/name).open('x') as handle: handle.write(content)
                rendered[name] = file_sha256(output/name)
            registry.checkpoint('slide-'+sid,record)
        with (output/'index.html').open('x') as handle: handle.write(render_index([r['report'] for r in records]))
        rendered['index.html'] = file_sha256(output/'index.html')
        for source in sources:
            if (file_sha256(source['completion_path']) != source['completion_sha256'] or
                    file_sha256(Path(source['directory'])/'tiles.csv') != source['manifest_sha256'] or
                    file_sha256(Path(source['directory'])/'metadata.json') != source['metadata_sha256']):
                raise ValueError('Source tile metadata changed during preview export')
        if (any(file_sha256(a['source_path']) != a['sha256'] for r in records for a in r['png_assets'].values()) or
                any(file_sha256(output/name) != digest for name,digest in rendered.items()) or
                read_sealed(c['report_root']) != (old,artifacts) or any(file_sha256(e['path']) != e['sha256'] for e in c['inputs'].values())):
            raise ValueError('Source or output content changed during preview export')
        summary = dict(slides=72,components=sum(len(r['report']['components']) for r in records),
            tile_references=references,unique_png_assets=sum(len(r['png_assets']) for r in records),copied_png_bytes=total_bytes,
            original_dependence_counts={k:saved[k] for k in ('decision_changing_components','decision_changing_supported',
                'decision_changing_abstained','annotation_positive_decisive_components','slides_with_decision_dependence')},
            rendered_file_sha256=rendered,new_predictions_computed=False,source_pixels_changed=False,
            selection_uses_labels_or_scores=False,review_alert_rate=None,foreign_fragment_recall=None,automatic_tissue_action='none',
            final_test_ready=False,interpretation='Bounded unchanged-PNG examples for saved training dependence; no new scientific evaluation or foreignness decision')
        if summary['components'] != c['components']: raise ValueError('Frozen preview component count differs')
        registry.checkpoint('summary',summary);registry.status('verified',validation=True,interpretation=summary['interpretation']);return summary
    except BaseException as exc:
        registry.status('failed',interpretation=type(exc).__name__+': '+str(exc));raise
