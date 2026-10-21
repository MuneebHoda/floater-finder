"""CPU-only frozen-CONCH research. Selection is persisted before opening known calibration."""
import json
import os
from pathlib import Path
import importlib.metadata
import numpy as np
from ..artifacts import write_json
from ..experiments import file_sha256
from .data import load_development
from .linear_probe import FrozenPredictor
from .evaluation import metrics, nested_linear

SIMPLICITY = {'zero_shot_mean': 0, 'linear_mean': 1, 'zero_shot_top1pct': 2, 'zero_shot_top5pct': 3, 'linear_mean_max_topk': 4}


def task_sources(sources, task):
    return [s for s in sources if task == 'benign_cancer' or s['slide'].metadata['isup_grade'] != 0]


def label(source, task):
    grade = source['slide'].metadata['isup_grade']
    return int(grade > 0) if task == 'benign_cancer' else int(grade >= 4)


def diagnostic(source):
    s = source['slide']; m = s.metadata; rows = source['annotations']; ex = m['extraction']
    dimensions = m['panda']['pyramid_dimensions'][0]; mpp = m['measured_mpp_xy']
    slide_area = np.prod(dimensions)*np.prod(mpp)/1e6
    area = sum(float(r['area_mm2']) for r in rows)
    known = m['panda']['mask_available']
    fractions = {str(g): sum(float(r['area_mm2'])*float(r[f'gleason{g}_fraction']) for r in rows) if known else None for g in (3, 4, 5)}
    return dict(image_id=m['slide_id'], split=m['cohort_split'], isup_grade=m['isup_grade'], tiles=len(s.feats),
        source_slide_area_mm2=float(slide_area), sampled_footprint_area_mm2=area,
        sampled_tile_density_per_slide_mm2=float(len(s.feats)/slide_area),
        tissue_grid_coverage=ex.get('sampled_tissue_grid_fraction'), eligible_tissue_cells=ex.get('eligible_tissue_cells'),
        mask_available=known, sampled_pattern_area_mm2=fractions,
        sampled_cancer_area_mm2=sum(fractions.values()) if known else None,
        annotation_scope='Annotation only within exported representative footprints; not full-slide tumor burden. Masks never enter model features.')


def audit_predictions(sources, task, predictions):
    from scipy.stats import spearmanr
    by_id = {s['slide'].metadata['slide_id']: diagnostic(s) for s in sources}; out = []; correlations = []
    for r in predictions:
        d = by_id[r['image_id']]
        out.append(dict(r, diagnostic=d, correct=r['truth'] == r['prediction']))
    fields = ['source_slide_area_mm2', 'tiles', 'sampled_tile_density_per_slide_mm2', 'tissue_grid_coverage', 'sampled_cancer_area_mm2']
    for cls in ('all', *sorted({r['truth'] for r in predictions})):
        subset = [r for r in out if cls == 'all' or r['truth'] == cls]
        for field in fields:
            pairs = [(r['diagnostic'][field], r['margin'], int(not r['correct'])) for r in subset if r['diagnostic'][field] is not None]
            for outcome, column in [('raw_margin', 1), ('clean_error', 2)]:
                x = [p[0] for p in pairs]; y = [p[column] for p in pairs]
                rho = float(spearmanr(x, y).statistic) if len(pairs) >= 3 and len(set(x)) > 1 and len(set(y)) > 1 else None
                correlations.append(dict(task=task, truth_class=cls, feature=field, outcome=outcome, slides=len(pairs), spearman_rho=rho,
                    caveat='Exploratory within-development association, no multiplicity correction or causal interpretation'))
    return out, correlations


def run(manifest, directories, encoded, verification, config_path, output):
    if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Real predictor analysis requires bounded CPU Slurm without GPU')
    config = json.loads(Path(config_path).read_text()); output = Path(output)
    if config['splits_for_selection'] != ['train'] or set(config['models']) != set(SIMPLICITY) or len(config['models']) != len(SIMPLICITY):
        raise ValueError('Predeclared training-only predictor configuration required')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'execution.json', dict(source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'),
        slurm_job_id=os.environ['SLURM_JOB_ID'], config_sha256=file_sha256(config_path), manifest_sha256=file_sha256(manifest),
        runtime={k: importlib.metadata.version(k) for k in ('numpy','scikit-learn','scipy')},
        test_slides_scored=False, clinical_validity_verified=False))
    train, receipt = load_development(manifest, directories, encoded, verification, 'train')
    fitted = {}; tasks = {}; raw = {}; fold_audit = {}; failures = []
    for task, classes in config['tasks'].items():
        sources = task_sources(train, task); slides = [s['slide'] for s in sources]
        y = [label(s, task) for s in sources]; groups = [s['group'] for s in sources]
        common = dict(schema_version=1, task=task, classes=classes, input_dimensions=slides[0].feats.shape[1],
            top_k=config['top_k'], checkpoint_sha256=slides[0].metadata['model']['checkpoint_sha256'],
            text_fingerprint=receipt['text_fingerprint'], config_sha256=file_sha256(config_path),
            train_ids=[s.metadata['slide_id'] for s in slides], trained_on='train only', patient_independence_verified=False,
            source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'))
        results = {}
        for name in config['models']:
            spec = dict(common, model_id=name)
            try:
                if name.startswith('zero_shot_'):
                    text = sources[0]['text']; model = FrozenPredictor(dict(spec, kind='zero_shot', pooling=name.removeprefix('zero_shot_')),
                        dict(text=text.feats[[text.classes.index(c) for c in classes]]))
                    rows = [dict(image_id=s.metadata['slide_id'], truth=classes[v], outer_fold='fixed scorer; no fitting', **model(s.feats)) for s, v in zip(slides, y)]
                    folds = dict(fitting='None; unchanged historical fixed text cosine and pooling')
                else:
                    rows, model, folds = nested_linear(slides, y, groups, name.removeprefix('linear_'), config, spec)
                fitted[(task, name)] = model
                results[name] = metrics(rows, classes, config['seed']); raw[(task, name)] = rows
                fold_audit[f'{task}/{name}'] = folds
                model.save(output/'models'/task/name)
                write_json(output/f'{task}_{name}_oof.json', rows)
            except Exception as exc:
                failures.append(dict(task=task, model=name, failure=f'{type(exc).__name__}: {exc}'))
            write_json(output/'model_attempts'/f'{task}_{name}.json',
                dict(task=task, model=name, metrics=results.get(name),
                     cv=fold_audit.get(f'{task}/{name}'),
                     failures=[r for r in failures if r['task']==task and r['model']==name]))
        if not results:
            raise RuntimeError(f'All models failed for {task}')
        primary = max(results, key=lambda name: (results[name]['balanced_accuracy'], min(results[name]['class_recall']), -SIMPLICITY[name]))
        selected = results[primary]; gate = config['minimum_support_for_s2_readiness']
        tasks[task] = dict(training_slides=len(slides), unique_groups=len(set(groups)), all_models=results,
            primary=primary, selected_using='Train out-of-fold BA, worst recall, frozen simplicity tie-break only',
            s2_engineering_readiness=selected['balanced_accuracy'] >= gate['balanced_accuracy'] and min(selected['class_recall']) >= gate['each_class_recall'])
    # Freeze chosen primary before reading any known calibration arrays or outcomes.
    selection = dict(config=config, tasks=tasks, failures=failures, test_slides_scored=False,
        calibration_opened_for_selection=False, nested_cv_caveat='Outer predictions estimate each model algorithm. Choosing among five by these predictions introduces selection optimism; no independent claim.',
        model4=config['mil'], patient_independence_verified=False)
    write_json(output/'selection_frozen.json', selection)
    write_json(output/'fold_audit.json', fold_audit)
    known_cal, _ = load_development(manifest, directories, encoded, verification, 'calibration')
    development = {}; all_diagnostics = []; correlations = []
    for task, classes in config['tasks'].items():
        for name in tasks[task]['all_models']:
            model = fitted[(task, name)]; sources = task_sources(known_cal, task)
            rows = [dict(image_id=s['slide'].metadata['slide_id'], truth=classes[label(s, task)], **model(s['slide'].feats)) for s in sources]
            development[f'{task}/{name}'] = metrics(rows, classes, config['seed'])
            write_json(output/f'{task}_{name}_known_calibration.json', rows)
            for split, selected_sources, predictions in [('train', task_sources(train, task), raw[(task,name)]), ('calibration', sources, rows)]:
                cases, corr = audit_predictions(selected_sources, task, predictions)
                all_diagnostics.extend(dict(r, task=task, model=name, split=split) for r in cases)
                correlations.extend(dict(r, model=name, split=split) for r in corr)
    write_json(output/'known_calibration_metrics.json', dict(role=config['known_calibration_role'], metrics=development,
        used_for_selection=False, test_slides_scored=False))
    write_json(output/'clean_error_case_studies.json', all_diagnostics)
    write_json(output/'diagnostic_correlations.json', correlations)
    write_json(output/'input_identity.json', dict(receipt_sha256=file_sha256(verification), manifest_sha256=file_sha256(manifest),
        train={s['slide'].metadata['slide_id']:s['identity'] for s in train},
        known_calibration={s['slide'].metadata['slide_id']:s['identity'] for s in known_cal}, final_test_artifacts_opened=False))
    write_json(output/'completion.json', dict(source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'), slurm_job_id=os.environ['SLURM_JOB_ID'],
        files={str(p.relative_to(output)):file_sha256(p) for p in output.rglob('*') if p.is_file()}, test_slides_scored=False))
    return tasks
