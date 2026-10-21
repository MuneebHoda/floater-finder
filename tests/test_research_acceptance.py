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
    monkeypatch.setattr(module, 'load_sources', lambda *args: (sources, dict(text_fingerprint=t.fingerprint())))
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
