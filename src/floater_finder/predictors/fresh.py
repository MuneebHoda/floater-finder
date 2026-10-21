"""Frozen, clean-slide validation on a separately approved, slide-disjoint cohort."""
import csv
import json
import os
from pathlib import Path
from ..artifacts import Slide, TextEmbeddings, write_json
from ..experiments import file_sha256
from ..panda_encoding import validate_saved
from .linear_probe import load_predictor
from .evaluation import metrics


def read_rows(path):
    with Path(path).open(newline='') as handle:
        return list(csv.DictReader(handle))


def frozen_inputs(protocol_path, expected_sha256, project):
    """Verify fixed files/models/membership without calling any predictor."""
    project = Path(project)
    if file_sha256(protocol_path) != expected_sha256:
        raise ValueError('Frozen fresh protocol changed')
    protocol = json.loads(Path(protocol_path).read_text())
    if (protocol['status'] != 'frozen_before_acquisition' or protocol['scope'] != 'fresh_clean_baseline_only' or
            protocol['schema_version'] != 1):
        raise ValueError('Frozen clean-baseline protocol required')
    for name,digest in protocol['source_files'].items():
        if file_sha256(project/name) != digest: raise ValueError('Frozen source differs: '+name)
    manifest = Path(protocol_path).parent/'manifest.csv'
    if file_sha256(manifest) != protocol['manifest_sha256']: raise ValueError('Fresh manifest changed')
    rows = read_rows(manifest); ids = [r['image_id'] for r in rows]
    if (len(ids) != 60 or len(set(ids)) != 60 or ids != protocol['image_ids'] or
            set(ids) & set(protocol['excluded_slide_ids'])):
        raise ValueError('Fresh membership/overlap guard failed before opening slide artifacts')
    for row in rows:
        if (row['split'] != 'engineering' or row['validation_role'] != 'fresh_development_validation' or
                row['candidate_split'] != 'fresh_development_validation' or row['data_provider'] != 'radboud'):
            raise ValueError('Dedicated fresh Radboud execution manifest required')
    counts = [sum(int(r['isup_grade']) in grades for r in rows) for grades in ((0,),(1,),(4,5))]
    if counts != [20,20,20]: raise ValueError('Frozen three-group counts differ')
    models = {}
    for entry in protocol['models']:
        directory = project/entry['directory']
        for name,digest in entry['sha256'].items():
            if file_sha256(directory/name) != digest: raise ValueError('Frozen model differs')
        model = load_predictor(directory)
        if (model.spec['text_fingerprint'] != protocol['text_fingerprint'] or
                model.spec['embedding_model'] != protocol['embedding_model'] or
                set(model.spec['train_ids']) & set(ids)):
            raise ValueError('Frozen model provenance or training overlap differs')
        models[(entry['task'],entry['role'])] = model
    if len(protocol['models']) != 4 or set(models) != {(task,role) for task in ('benign_cancer','low_high') for role in ('primary','historical')}:
        raise ValueError('Exactly the four preregistered predictors required')
    return protocol,rows,models


def load_fresh(protocol, rows, manifest, directories, encoded, verification):
    """Exact whitelist before opening any arrays; original test artifacts are forbidden."""
    ids = {r['image_id'] for r in rows}
    if len(ids) != len(rows) or ids & set(protocol['excluded_slide_ids']):
        raise ValueError('Exposed/original test IDs forbidden before opening artifacts')
    receipt = json.loads(Path(verification).read_text())
    if (receipt['source_kind'] != 'real' or receipt['manifest_sha256'] != file_sha256(manifest) or receipt['slides'] != len(rows) or
            receipt['text_fingerprint'] != protocol['text_fingerprint']):
        raise ValueError('Fresh embedding verification receipt differs')
    byid = {r['image_id']:r for r in receipt['records']}
    if len(byid) != len(receipt['records']) or set(byid) != ids:
        raise ValueError('Missing/extra verification records; do not silently drop slides')
    paths = [Path(p) for p in json.loads(Path(directories).read_text())]
    if len(paths) != len(rows): raise ValueError('Exact completed fresh tiling list required')
    resolved = {sid:[p for p in paths if sid in p.parts] for sid in ids}
    if any(len(v) != 1 for v in resolved.values()) or len({p for v in resolved.values() for p in v}) != len(rows):
        raise ValueError('Fresh tiling directory whitelist failed')
    sources = []
    for row in rows:
        sid = row['image_id']; directory = resolved[sid][0]; root = Path(encoded)/sid; expected = byid[sid]
        if file_sha256(root/'completion.json') != expected['completion_sha256']:
            raise ValueError('Embedding completion checksum differs')
        completion = json.loads((root/'completion.json').read_text()); identity = completion['input_identity']
        if expected['artifact_sha256'] != completion['artifact_sha256']:
            raise ValueError('Verification and encoding receipts differ')
        for name,key in (('tiles.csv','manifest_sha256'),('metadata.json','metadata_sha256'),('completion.json','prepared_tiling_receipt_sha256')):
            if file_sha256(directory/name) != identity[key]: raise ValueError('Prepared tiling provenance differs')
        if identity['prompts_sha256'] != protocol['prompts_sha256']:
            raise ValueError('Fresh prompts differ')
        tile_rows = read_rows(directory/'tiles.csv')
        validate_saved(root,tile_rows,identity)
        slide = Slide.load(root/'slide.npz'); text = TextEmbeddings.load(root/'text.npz'); m = slide.metadata; ex = m['extraction']
        original_metadata = json.loads((directory/'metadata.json').read_text())
        if (any(m.get(k) != v for k,v in original_metadata.items() if k != 'model') or
                expected['split'] != 'engineering' or expected['tiles'] != len(slide.feats) or
                m['project'] != 'PANDA' or m['source_kind'] != 'real' or m['data_provider'] != 'radboud' or
                m['slide_id'] != sid or m['isup_grade'] != int(row['isup_grade']) or m['cohort_split'] != 'engineering' or
                m['selection_manifest_sha256'] != protocol['manifest_sha256'] or m['train_csv_sha256'] != protocol['train_sha256'] or
                m['model'] != protocol['embedding_model'] or text.fingerprint() != protocol['text_fingerprint'] or
                m['coordinate_units'] != 'microns' or m['microns_per_unit'] != 1 or m['requested_field_um'] != 112. or
                m['export_pixels'] != 224 or not 1 <= len(slide.feats) <= 512 or ex['max_tiles'] != 512 or
                ex['sampling_mode'] != 'representative' or ex['selection_uses_mask'] or ex['seed'] != 20261020 or
                ex['max_candidates'] != 20000 or ex['min_tissue_fraction'] != .1 or
                slide.foreign_mask.any() or 'injection' in m):
            raise ValueError('Fresh original slide/sampling/model provenance differs')
        sources.append(dict(slide=slide,image_id=sid,grade=int(row['isup_grade']),identity=expected))
    return sources


def score_sources(sources, models, seed):
    """No fitting/selection: all four frozen models and every eligible slide are reported."""
    predictions = {}; summaries = {}
    for (task,role),model in models.items():
        rows = []
        for source in sources:
            grade = source['grade']
            if task == 'low_high' and grade == 0: continue
            truth = int(grade > 0) if task == 'benign_cancer' else int(grade >= 4)
            rows.append(dict(image_id=source['image_id'],truth=model.spec['classes'][truth],
                tiles=len(source['slide'].feats),**model.score_slide(source['slide'])))
        key = task+'/'+role
        predictions[key] = rows; summaries[key] = metrics(rows,model.spec['classes'],seed)
    return predictions,summaries


def run(protocol_path, expected_sha256, project, directories, encoded, verification, output, source_commit, execute=False):
    if not execute: raise RuntimeError('Fresh predictions require --execute-fresh; use metadata preflight first')
    if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Fresh real-input validation requires bounded CPU Slurm, no GPU')
    output = Path(output)
    if output.exists(): raise FileExistsError('Single execution guard; preserve old outputs')
    protocol,rows,models = frozen_inputs(protocol_path,expected_sha256,project)
    sources = load_fresh(protocol,rows,Path(protocol_path).parent/'manifest.csv',directories,encoded,verification)
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'execution.json',dict(source_commit=source_commit,slurm_job_id=os.environ['SLURM_JOB_ID'],
        protocol_sha256=expected_sha256,verification_sha256=file_sha256(verification),directories_sha256=file_sha256(directories),
        split='fresh_development_validation',original_final_test_predictions_computed=False))
    predictions,summaries = score_sources(sources,models,protocol['bootstrap_seed'])
    write_json(output/'predictions.json',predictions)
    write_json(output/'summary.json',dict(results=summaries,slides=len(sources),models_refit=False,
        original_final_test_predictions_computed=False,clinical_validity_verified=False,patient_independence_verified=False,
        no_policy_or_final_readiness_inferred=True,limitations=protocol['limitations']))
    write_json(output/'completion.json',dict(status='verified',artifacts={n:file_sha256(output/n) for n in ('execution.json','predictions.json','summary.json')}))
