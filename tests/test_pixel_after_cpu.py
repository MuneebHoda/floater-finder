"""Artificial completion/source fixtures; no inference or real-data results."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from floater_finder.research import pixel_study

spec=importlib.util.spec_from_file_location('pixel_after_cpu',Path(__file__).parents[1]/'scripts/panda_pixel_after_cpu.py')
launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)


def fixture(tmp_path,monkeypatch):
    source=tmp_path/'release/source';source.mkdir(parents=True)
    (source/'pinned.py').write_text('# artificial source\n')
    sm=source.parent/'source_manifest.json'
    sm.write_text(json.dumps(dict(source_commit='fixture-commit',files={'pinned.py':launch.sha(source/'pinned.py')})))
    prep=tmp_path/'prepared';prep.mkdir()
    pair=dict(id='pair-1',task='s1',host='fixture-host',donor='fixture-donor')
    m=dict(slurm_job_id='123',source_commit='fixture-commit',protocol_sha256='fixture-protocol',source_kind='real',
        experiment_id='fixture-only',pairs=[pair],inference_executed=False,scientific_effects_measured=False,final_test_accessed=False)
    (prep/'image_manifest.json').write_text(json.dumps(m))
    completion=dict(status='prepared_verified_no_inference',source_commit='fixture-commit',protocol_sha256='fixture-protocol',images=96)
    (prep/'completion.json').write_text(json.dumps(completion))
    c=dict(experiment_id='fixture-only',pairs=[pair],preparation_output=str(prep),gpu_output=str(tmp_path/'gpu-output'))
    monkeypatch.setattr(pixel_study,'preflight',lambda *args:c)
    def prepared(folder,digest):
        assert launch.sha(Path(folder)/'image_manifest.json')==digest
        return json.loads((Path(folder)/'image_manifest.json').read_text())
    monkeypatch.setattr(pixel_study,'prepared_inputs',prepared)
    a=SimpleNamespace(project=str(source),source_manifest_sha256=launch.sha(sm),source_commit='fixture-commit',config_sha256='fixture-protocol',cpu_job='123',runtime='fixture-runtime')
    return a,c,m


def resolve(a):return launch.resolve(a.project,a.source_manifest_sha256,a.source_commit,a.config_sha256,a.cpu_job)


def test_missing_cpu_completion_stops_before_launch(tmp_path,monkeypatch):
    a,c,m=fixture(tmp_path,monkeypatch);(Path(c['preparation_output'])/'completion.json').unlink()
    with pytest.raises(FileNotFoundError):resolve(a)
    assert not Path(c['gpu_output']).exists()


@pytest.mark.parametrize('field,value',[('slurm_job_id','456'),('final_test_accessed',True),('source_commit','other'),('pairs',[])])
def test_wrong_job_source_scope_or_pairs_stop(tmp_path,monkeypatch,field,value):
    a,c,m=fixture(tmp_path,monkeypatch);m[field]=value
    (Path(c['preparation_output'])/'image_manifest.json').write_text(json.dumps(m))
    with pytest.raises(ValueError,match='Exact successful'):resolve(a)


def test_pinned_runtime_mutation_and_existing_gpu_output_stop(tmp_path,monkeypatch):
    a,c,m=fixture(tmp_path,monkeypatch)
    (Path(a.project)/'pinned.py').write_text('changed')
    with pytest.raises(ValueError,match='source file changed'):resolve(a)
    (Path(a.project)/'pinned.py').write_text('# artificial source\n')
    Path(c['gpu_output']).mkdir()
    with pytest.raises(FileExistsError,match='duplicate inference'):resolve(a)


def test_frozen_real_manifest_passes_only_to_unchanged_runner(tmp_path,monkeypatch):
    a,c,m=fixture(tmp_path,monkeypatch)
    monkeypatch.setenv('SLURM_JOB_ID','789');monkeypatch.setenv('SLURM_JOB_GPUS','0')
    calls=[]
    class Executed(Exception):pass
    def execv(path,args):calls.append((path,args));raise Executed()
    monkeypatch.setattr(launch.os,'execv',execv)
    with pytest.raises(Executed):launch.execute(a)
    command=calls[0][1];assert command[:2]==['/bin/bash',a.project+'/scripts/slurm/panda_pixel_encode.sbatch']
    assert command[2:]==[a.project,a.runtime,a.config_sha256,c['preparation_output'],launch.sha(Path(c['preparation_output'])/'image_manifest.json'),c['gpu_output'],a.source_commit]
    receipt=json.loads((tmp_path/'pixel-contamination-gpu-launch-789.json').read_text())
    assert receipt['cpu_job_id']=='123' and receipt['gpu_job_id']=='789' and not receipt['inference_executed']
    with pytest.raises(FileExistsError):launch.execute(a)
    assert len(calls)==1


def test_no_login_node_launch_and_same_resource_caps(tmp_path,monkeypatch):
    a,c,m=fixture(tmp_path,monkeypatch);monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='GPU Slurm'):launch.execute(a)
    text=(Path(__file__).parents[1]/'scripts/slurm/panda_pixel_after_cpu.sbatch').read_text()
    assert '--gres=gpu:1' in text and '--time=00:05:00' in text and '--cpus-per-task=4' in text and '--mem=16G' in text
    assert 'HF_HUB_OFFLINE=1' in text
