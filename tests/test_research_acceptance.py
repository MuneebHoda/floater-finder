"""Temporary fixture workflow checks; never real-data performance evidence."""
import json
from pathlib import Path
import numpy as np
import pytest
from floater_finder.research.acceptance import run
from floater_finder.research.registry import Registry
from test_research_engine import text
from test_panda_stress import slide


def test_acceptance_cpu_gate_precedes_any_input_access(monkeypatch, tmp_path):
    monkeypatch.delenv('SLURM_JOB_ID', raising=False)
    with pytest.raises(RuntimeError, match='CPU Slurm'): run(*(['missing']*7), tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_complete_fixture_acceptance_resume_and_coordinate_invariance(monkeypatch, tmp_path):
    import floater_finder.research.acceptance as module
    monkeypatch.setenv('SLURM_JOB_ID', 'fixture-not-real')
    monkeypatch.delenv('SLURM_JOB_GPUS', raising=False)
    sources = {}
    t = text()
    for grade in (0, 1, 4):
        for number in range(2):
            sid = f'fixture-{grade}-{number}'
            s = slide(sid, grade)
            s.coords[:, 1] = 200
            rows = [dict(tile_id=tile_id, gleason3_fraction=.2 if grade == 1 else 0,
                gleason4_fraction=.2 if grade == 4 else 0, gleason5_fraction=0) for tile_id in s.tile_ids]
            sources[sid] = dict(slide=s, rows=rows, text=t)
    monkeypatch.setattr(module, '_load_training', lambda *args: (sources, dict(text_fingerprint=t.fingerprint())))
    reads = []
    def overview(source, config, receipts, output):
        source['mask'] = np.zeros((100, 250), bool)
        source['mask'][20:30, :200] = True
        source['pixel_um'] = np.array([10., 10.])
        sid = source['slide'].metadata['slide_id']
        reads.append(sid)
        return dict(image_id=sid, image_sha256='a'*64, mapping_fraction=1.)
    monkeypatch.setattr(module, 'read_overview', overview)
    for name in ('manifest', 'directories', 'verification'):
        (tmp_path/name).write_text('fixture')
    args = [tmp_path/'manifest', tmp_path/'directories', 'unused-embeddings', tmp_path/'verification',
            'unused-receipts', Path(__file__).parents[1]/'configs/research_engine_acceptance_v1.json', 'f'*40, tmp_path/'out']
    result = run(*args)
    assert result['unique_host_slides'] == 4
    assert result['trial_instances'] == result['exact_oracle_passes'] == 1008
    assert result['exact_legacy_comparisons'] == 168
    assert result['coordinate_only_invariance_checks'] == 504
    assert result['test_slides_scored'] is False and len(reads) == 4
    assert run(*args) == result and len(reads) == 4  # Resume skips all geometry/interventions.
    registry = json.loads((tmp_path/'out/run.json').read_text())
    assert registry['run']['split'] == 'train'
    assert json.loads((tmp_path/'out/seal.json').read_text())['last_sha256']


def test_s2_v2_requires_a_predeclared_ready_predictor_before_writing_output(monkeypatch, tmp_path):
    monkeypatch.setenv('SLURM_JOB_ID', 'fixture-not-real')
    monkeypatch.delenv('SLURM_JOB_GPUS', raising=False)
    config = Path(__file__).parents[1]/'configs/research_engine_acceptance_v2.json'
    with pytest.raises(ValueError, match='requires the frozen improved predictor'):
        run('missing', 'missing', 'missing', 'missing', 'missing', config, 'f'*40, tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_s2_v2_fixture_integrates_frozen_predictor_and_same_grade_controls(monkeypatch, tmp_path):
    import floater_finder.research.acceptance as module
    from floater_finder.predictors import FrozenPredictor
    from floater_finder.research.registry import file_hash
    monkeypatch.setenv('SLURM_JOB_ID', 'fixture-not-real')
    monkeypatch.delenv('SLURM_JOB_GPUS', raising=False)
    sources = {}
    t = text()
    for grade in (0, 1, 4):
        for number in range(2):
            sid = f'fixture-{grade}-{number}'; s = slide(sid, grade); s.coords[:, 1] = 200
            sources[sid] = dict(slide=s, text=t, rows=[dict(tile_id=x, gleason3_fraction=.2 if grade == 1 else 0,
                gleason4_fraction=.2 if grade == 4 else 0, gleason5_fraction=0) for x in s.tile_ids])
    monkeypatch.setattr(module, '_load_training', lambda *args: (sources, dict(text_fingerprint=t.fingerprint())))
    def overview(source, *args):
        source['mask'] = np.zeros((100, 250), bool); source['mask'][20:30, :200] = True
        source['pixel_um'] = np.array([10., 10.])
        return dict(image_sha256='a'*64)
    monkeypatch.setattr(module, 'read_overview', overview)
    model_root = tmp_path/'models/low_high/fixture-linear'
    sample = sources['fixture-1-0']['slide']
    spec = dict(schema_version=1, kind='linear_probe', classes=['low_grade', 'high_grade'], input_dimensions=512,
        feature_rule='mean', top_k=5, embedding_model=sample.metadata['model'], source_kind='fixture', model_id='fixture-linear')
    model = FrozenPredictor(spec, dict(coef=np.zeros(512), mean=np.zeros(512), scale=np.ones(512), intercept=np.array([-1.])))
    model.save(model_root)
    selection = tmp_path/'selection_frozen.json'
    selection.write_text(json.dumps(dict(tasks=dict(low_high=dict(primary='fixture-linear', s2_engineering_readiness=True)),
        calibration_opened_for_selection=False, test_slides_scored=False)))
    cfg = json.loads((Path(__file__).parents[1]/'configs/research_engine_acceptance_v2.json').read_text())
    cfg['predictor_selection_sha256'] = file_hash(selection)
    protocol = tmp_path/'protocol.json'; protocol.write_text(json.dumps(cfg))
    for name in ('manifest', 'directories', 'verification'): (tmp_path/name).write_text('fixture')
    result = run(tmp_path/'manifest', tmp_path/'directories', 'unused', tmp_path/'verification', 'unused', protocol,
        'f'*40, tmp_path/'out', model_root)
    assert result['trial_instances'] == result['exact_oracle_passes'] == 1176
    assert result['s2_training_stress_is_resubstitution'] is True
    assert result['s2_v2_full_cohort_completed'] is False
    same_grade = [r for r in result['metrics'] if r['task'] == 's2' and r['condition'] == 'same_grade_gp3_only']
    assert len(same_grade) == 28 and all(r['control'] == 'same_grade_donor' for r in same_grade)
    assert all(r['induced_error_instances'] == 0 for r in same_grade)
