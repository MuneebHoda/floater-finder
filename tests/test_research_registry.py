"""Registry correctness on temporary software fixtures; no real scientific results."""
from dataclasses import replace
import json
import pytest
from floater_finder.research import ExperimentRun, Registry
from floater_finder.research.contracts import canonical


def run():
    return ExperimentRun('fixture-engine-v1', 'fixture oracle only', 'a'*40, canonical({'doses': [0, .25, 10]}),
        'fixture-manifest-sha', 'train', 'fixture-checkpoint-sha', 'fixture-embeddings-sha', canonical({'cpus': 2}))


def test_registry_exclusive_checkpoints_resume_and_coherent_status(tmp_path):
    registry = Registry(tmp_path/'r', run())
    registry.status('planned')
    registry.status('running', slurm_job_id='fixture')
    value = {'oracle': True, 'scores': [0, 1]}
    registry.checkpoint('host-a-seed-1', value)
    same = Registry(tmp_path/'r', run())
    assert same.load_checkpoint('host-a-seed-1') == value
    same.checkpoint('host-a-seed-1', value)
    with pytest.raises(ValueError, match='different'): same.checkpoint('host-a-seed-1', {'oracle': False})
    assert same.report()['checkpoints'] == 1
    with pytest.raises(ValueError, match='validation'): same.status('verified')
    same.status('verified', validation=True, interpretation='fixture passed', limitations=['not scientific'])
    assert same.report()['status'] == 'verified'
    with pytest.raises(ValueError, match='immutable'): same.status('running')
    with pytest.raises(ValueError, match='identity'): Registry(tmp_path/'r', replace(run(), source_commit='b'*40))


def test_registry_refuses_corrupt_artifact_and_event_chain(tmp_path):
    registry = Registry(tmp_path/'r', run())
    registry.status('planned'); registry.status('running')
    registry.checkpoint('x', {'x': 1})
    (tmp_path/'r/checkpoints/x.json').write_text('{"x":2}\n')
    with pytest.raises(ValueError, match='hash changed'): registry.report()
    (tmp_path/'r/checkpoints/x.json').write_text('{"x":1}\n')
    event = tmp_path/'r/events/000001.json'
    row = json.loads(event.read_text()); row['status'] = 'verified'; event.write_text(json.dumps(row))
    with pytest.raises(ValueError, match='chain'): registry.report()


def test_registry_preserves_failed_partial_runs_and_rejects_sealed_test_scope(tmp_path):
    registry = Registry(tmp_path/'r', run())
    registry.status('planned'); registry.status('running'); registry.checkpoint('done', {'oracle': True})
    registry.status('failed', interpretation='fixture interrupted')
    registry.status('running')
    assert registry.load_checkpoint('done') == {'oracle': True}
    registry.checkpoint('second', {'oracle': True})
    assert registry.report()['checkpoints'] == 2
    with pytest.raises(ValueError, match='development'): replace(run(), split='test')
