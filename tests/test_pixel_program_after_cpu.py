"""Artificial receipts only; no model or dataset reads, scientific inference or jobs."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from floater_finder.research import pixel_program

spec = importlib.util.spec_from_file_location("program_launch", Path(__file__).parents[1]/"scripts/panda_pixel_program_after_cpu.py")
launch = importlib.util.module_from_spec(spec); spec.loader.exec_module(launch)


def fixture(tmp_path, monkeypatch):
    project = tmp_path/"source"; project.mkdir(); (project/"pinned.py").write_text("# fixture only\n")
    source = tmp_path/"source_manifest.json"
    source.write_text(json.dumps(dict(parent_commit="fixture-parent", files={"pinned.py":launch.sha(project/"pinned.py")})))
    prep = tmp_path/"prepared"; prep.mkdir(); (prep/"sources").mkdir()
    for name in ("records.jsonl", "exclusions.json"):
        (prep/name).write_text("[]\n")
    images = [dict(pixel_sha256=f"{i:064x}",split="fit" if i<600 else "calibration" if i<700 else "validation") for i in range(800)]
    (prep/"unique_images.json").write_text(json.dumps(images))
    facts = {}
    for i in range(57):
        p = prep/"sources"/(str(i)+".json"); p.write_text("{}"); facts[p.name] = launch.sha(p)
    m = dict(cpu_feasibility_gate_passed=True, source_kind="real", slurm_job_id="123", protocol_sha256="fixture-protocol",
        checkpoint_current_sha256="c"*64, target_records=10000, generated_records=10000, excluded_records=0,
        sources_checked=57, benchmark_sources=45, dense_sources=12, inference_executed=False,
        original_final_test_accessed=False, source_facts_sha256=facts, exact_unique_images_requiring_inference=800,
        unique_images_by_split=dict(fit=600,calibration=100,validation=100),
        records_sha256=launch.sha(prep/"records.jsonl"), exclusions_sha256=launch.sha(prep/"exclusions.json"),
        unique_images_sha256=launch.sha(prep/"unique_images.json"))
    (prep/"completion.json").write_text(json.dumps(m))
    c = dict(cpu_output=str(prep),checkpoint_sha256="c"*64)
    monkeypatch.setattr(pixel_program,"load_config",lambda *args:(c,[]))
    a = SimpleNamespace(project=str(project),runtime="fixture-runtime",source_manifest_sha256=launch.sha(source),
                        config_sha256="fixture-protocol",cpu_job="123")
    return a,prep,m


def resolve(a):
    return launch.resolve(a.project,a.source_manifest_sha256,a.config_sha256,a.cpu_job)


@pytest.mark.parametrize("field,value",[("slurm_job_id","999"),("cpu_feasibility_gate_passed",False),
    ("original_final_test_accessed",True),("generated_records",7500),("checkpoint_current_sha256","other")])
def test_invalid_completion_blocks_before_any_encoder(tmp_path,monkeypatch,field,value):
    a,prep,m = fixture(tmp_path,monkeypatch); m[field] = value
    (prep/"completion.json").write_text(json.dumps(m))
    with pytest.raises(ValueError,match="Exact successful"):
        resolve(a)
    assert not (tmp_path/"pixel-program-10k-v1-profile").exists()


def test_missing_completion_and_record_mutation_stop(tmp_path,monkeypatch):
    a,prep,m = fixture(tmp_path,monkeypatch); completion = prep/"completion.json"; completion.unlink()
    with pytest.raises(FileNotFoundError):
        resolve(a)
    completion.write_text(json.dumps(m)); (prep/"records.jsonl").write_text("changed")
    with pytest.raises(ValueError,match="CPU manifest"):
        resolve(a)


def test_source_mutation_and_duplicate_profile_stop(tmp_path,monkeypatch):
    a,prep,m = fixture(tmp_path,monkeypatch); p = Path(a.project)/"pinned.py"; old = p.read_text(); p.write_text("changed")
    with pytest.raises(ValueError,match="source file"):
        resolve(a)
    p.write_text(old); (tmp_path/"pixel-program-10k-v1-profile").mkdir()
    with pytest.raises(FileExistsError,match="Existing profile"):
        resolve(a)


def test_changed_dedup_denominators_and_scope_stop(tmp_path,monkeypatch):
    a,prep,m = fixture(tmp_path,monkeypatch)
    m["exact_unique_images_requiring_inference"] = 10000
    (prep/"completion.json").write_text(json.dumps(m))
    with pytest.raises(ValueError,match="Deduplicated inference scope"):
        resolve(a)
    m["exact_unique_images_requiring_inference"] = 800; m["unique_images_by_split"]["fit"] = 601
    (prep/"completion.json").write_text(json.dumps(m))
    with pytest.raises(ValueError,match="split denominators"):
        resolve(a)


def test_execute_freezes_actual_receipt_and_only_first_512_fit_images(tmp_path,monkeypatch):
    a,prep,m = fixture(tmp_path,monkeypatch)
    monkeypatch.setenv("SLURM_JOB_ID","456"); monkeypatch.setenv("SLURM_JOB_GPUS","0")
    calls = []
    class Executed(Exception): pass
    def execv(path, args):
        calls.append(args); raise Executed()
    monkeypatch.setattr(launch.os,"execv",execv)
    with pytest.raises(Executed):
        launch.execute(a)
    command = calls[0]
    assert command[:2] == ["/bin/bash",a.project+"/scripts/slurm/panda_pixel_program_encode.sbatch"]
    assert command[4] == a.config_sha256 and command[5] == launch.sha(prep/"completion.json")
    assert command[-3:] == ["fit","0","512"]
    receipt = json.loads((tmp_path/"pixel-program-10k-v1-profile-launch-456.json").read_text())
    assert receipt["images"] == 512 and receipt["exact_unique_images"] == 800
    assert not receipt["inference_executed"] and not receipt["remaining_batches_submitted"]
    with pytest.raises(FileExistsError):
        launch.execute(a)
    assert len(calls) == 1


def test_login_execution_blocked_and_resources_bounded(tmp_path,monkeypatch):
    a,prep,m = fixture(tmp_path,monkeypatch); monkeypatch.delenv("SLURM_JOB_ID",raising=False)
    with pytest.raises(RuntimeError,match="GPU Slurm"):
        launch.execute(a)
    script = (Path(__file__).parents[1]/"scripts/slurm/panda_pixel_program_after_cpu.sbatch").read_text()
    for option in ("--gres=gpu:1","--time=00:15:00","--cpus-per-task=4","--mem=16G","--partition=gpuA100x4\n"):
        assert option in script
