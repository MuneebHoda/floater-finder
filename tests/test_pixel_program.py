"""Artificial arrays only. These tests are not scientific results."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from floater_finder.research import pixel_program as pp


def sources():
    result = []
    for group, grade in enumerate((0, 1, 4)):
        for i in range(19):
            result.append(dict(image_id=f"{group*19+i+1:032x}", data_provider="radboud", isup_grade=str(grade),
                source_split="train", patient_id="", patient_id_known="False",
                program_role="benchmark" if i < 15 else "dense",
                program_split=("fit" if i < 9 else "calibration" if i < 12 else "validation") if i < 15 else
                              ("fit" if i < 17 else "calibration" if i == 17 else "validation")))
    return result


def test_source_graph_is_disjoint_complete_and_deterministic():
    rows = sources(); pp.validate_sources(rows, set()); pairs = pp.make_pairs(rows)
    assert pairs == pp.make_pairs(list(reversed(rows)))
    assert len(pairs) == 40
    folds = [{p[r] for p in pairs if p["split"] == s for r in ("host", "donor")} for s in ("fit", "calibration", "validation")]
    assert list(map(len, folds)) == [27, 9, 9]
    assert all(not a & b for i, a in enumerate(folds) for b in folds[i+1:])
    assert all(p["host"] != p["donor"] for p in pairs)
    assert len({(p["host_grade"],p["donor_grade"]) for p in pairs if p["split"] == "fit"}) == 9


@pytest.mark.parametrize("bad", ["test", "calibration"])
def test_original_holdouts_blocked(bad):
    rows = sources(); rows[0]["source_split"] = bad
    with pytest.raises(ValueError, match="Original calibration/test"):
        pp.validate_sources(rows, set())


def test_pilot_and_known_patient_cross_fold_blocked():
    rows = sources()
    with pytest.raises(ValueError):
        pp.validate_sources(rows, {rows[0]["image_id"]})
    for index in (0, 9):
        rows[index].update(patient_id="known-patient", patient_id_known="True")
    with pytest.raises(ValueError, match="patient crosses"):
        pp.validate_sources(rows, set())


def test_measured_irregular_piece_has_no_gap_bridging():
    a = np.zeros((11, 11), bool); a[1:4, 1:4] = True; a[7:9, 7:9] = True
    out = pp.largest_piece(a)
    assert out.sum() == 9 and np.all(out <= a) and not out[5, 5]
    assert not pp.largest_piece(np.zeros((11,11),bool)).any()


def test_detached_requires_rgb_blank_and_native_mask_with_isolation_ring():
    rgb = np.full((224,224,3),255,np.uint8); labels = np.zeros((230,230),np.uint8); box = [90,90,110,110]
    assert pp.context_ok(rgb,labels,box,"background")
    rgb[89,95] = 130
    assert not pp.context_ok(rgb,labels,box,"background")
    rgb[:] = 255; labels[95:110,95:110] = 4
    assert not pp.context_ok(rgb,labels,box,"background")


def test_matched_shams_seam_null_and_masks():
    host = np.full((224,224,3),70,np.uint8)
    donor = np.full((11,11,3),150,np.uint8); native = np.full_like(donor,90)
    support = np.zeros((11,11),bool); support[2:9,2:9] = True
    images, footprint, seam = pp.composite_group(host,donor,native,[40,40,51,51],support)
    assert footprint.sum() == 49 and np.all(images["foreign"][footprint] == 150)
    assert np.all(images["native_sham"][footprint] == 90)
    assert np.array_equal(images["identity"],host) and np.array_equal(images["unchanged"],host)
    assert not np.any(np.any(images["seam_only"] != host,axis=2) & ~footprint)
    assert np.array_equal(images["seam_only"][45,45],host[45,45])
    assert seam["seam_contrast_absolute_error"] == 0
    assert footprint.mean()*112**2/1e6 == pytest.approx(49*.5**2/1e6)
    with pytest.raises(ValueError,match="Degenerate"):
        pp.composite_group(host,np.full_like(donor,70),native,[40,40,51,51],support)


def test_actual_rgb_dedup_and_cross_fold_collision(tmp_path):
    (tmp_path/"images").mkdir(); index = {}; pixels = np.zeros((224,224,3),np.uint8)
    a = pp.store_rgb(tmp_path,pixels,"fit",index)
    assert a == pp.store_rgb(tmp_path,pixels.copy(),"fit",index) and len(index) == 1
    with pytest.raises(ValueError,match="cross source folds"):
        pp.store_rgb(tmp_path,pixels,"validation",index)
    assert len(list((tmp_path/"images").iterdir())) == 1


def test_preparation_requires_cpu_slurm(monkeypatch,tmp_path):
    monkeypatch.delenv("SLURM_JOB_ID",raising=False)
    with pytest.raises(RuntimeError):
        pp.prepare(tmp_path,"missing","missing",tmp_path/"out")
    monkeypatch.setenv("SLURM_JOB_ID","fixture"); monkeypatch.setenv("SLURM_JOB_GPUS","0")
    with pytest.raises(RuntimeError):
        pp.prepare(tmp_path,"missing","missing",tmp_path/"out")


def test_full_10000_fixture_receipt_provenance_and_immutability(tmp_path,monkeypatch):
    rows = sources(); output = tmp_path/"prepared"; checkpoint = tmp_path/"model"; checkpoint.write_bytes(b"fixture only")
    original = tmp_path/"cohort.csv"
    for r in rows:
        r.update(image_path="fixture",mask_path="fixture",image_sha256="a"*64,mask_sha256="b"*64,split="train")
    with original.open("w",newline="") as f:
        w = csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    c = dict(cpu_output=str(output),checkpoint=str(checkpoint),checkpoint_sha256=pp.file_sha256(checkpoint),
             cohort_manifest=dict(path=str(original),sha256=pp.file_sha256(original)),pairs=pp.make_pairs(rows))
    verification = tmp_path/"original_verification.json"; verification.write_text('{"records":[]}')
    c["original_embedding_verification"] = dict(path=str(verification),sha256=pp.file_sha256(verification))
    monkeypatch.setattr(pp,"load_config",lambda *a:(c,rows))
    monkeypatch.setenv("SLURM_JOB_ID","fixture-only"); monkeypatch.delenv("SLURM_JOB_GPUS",raising=False)
    def mock_source(c,r,output):
        i = int(r["image_id"],16); y,x = np.indices((224,224))
        rgb = np.stack((40+i+y%31,20+i+x%29,90+i+(x+y)%23),axis=2).astype(np.uint8)
        labels = np.full((224,224),2 if r["isup_grade"] == "0" else 3 if r["isup_grade"] == "1" else 4,np.uint8)
        source = dict(slide_id=r["image_id"],tile_id="host",tile_size_um_xy=[112.,112.])
        crop_source = dict(source,tile_id="native")
        boxes = [[112-s//2,112-s//2,112-s//2+s,112-s//2+s] for s in pp.SIDES]
        return ({p[0]:(rgb,labels,source) for p in pp.PLACEMENTS},[(np.roll(rgb,3,axis=0),labels,crop_source,boxes)],
                dict(tile_size=[112.,112.],measured_mpp_xy=[.5,.5],footprint_level0_pixels_xy=[224,224],export_pixels=224))
    monkeypatch.setattr(pp,"_source",mock_source)
    result = pp.prepare(tmp_path,"fixture","c"*64,output)
    assert result["target_records"] == 10000 and result["generated_records"] == 10000
    assert not result["inference_executed"] and not result["gpu_go"]
    assert result["exact_unique_images_requiring_inference"] < 10000
    records = [json.loads(line) for line in (output/"records.jsonl").read_text().splitlines()]
    assert len(records) == 10000 and all(r["source_footprint_area_mm2"] > 0 for r in records)
    assert records[0]["donor"]["slide_id"] != records[0]["host"]["slide_id"]
    digest = pp.file_sha256(output/"completion.json")
    with pytest.raises(FileExistsError):
        pp.prepare(tmp_path,"fixture","c"*64,output)
    assert pp.file_sha256(output/"completion.json") == digest


def test_gpu_has_no_implicit_submission_or_unfrozen_execution(monkeypatch,tmp_path):
    monkeypatch.delenv("SLURM_JOB_ID",raising=False)
    with pytest.raises(RuntimeError):
        pp.encode(tmp_path,"missing","missing","missing",tmp_path/"out","fit",0,512)
