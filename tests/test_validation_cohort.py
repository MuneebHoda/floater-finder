import pytest

from floater_finder.validation_cohort import propose, write_proposal


def inputs():
    rows, files = [], []
    for i, grade in enumerate([0, 0, 1, 1, 4, 5]):
        sid = f"{i:032x}"
        rows.append(dict(image_id=sid, data_provider="radboud", isup_grade=str(grade),
                         gleason_score="not-used"))
        files.append(dict(name=f"train_images/{sid}.tiff", bytes=100))
        files.append(dict(name=f"train_label_masks/{sid}_mask.tiff", bytes=10))
    return rows, dict(complete=True, files=files)


def test_outcome_blind_deterministic_exclusion_and_byte_denominator():
    rows, catalog = inputs()
    a, report = propose(rows, catalog, {rows[0]["image_id"]}, provider="radboud", per_group=1)
    b, _ = propose(list(reversed(rows)), catalog, {rows[0]["image_id"]}, provider="radboud", per_group=1)
    assert a == b
    assert len(a) == 3 and report["catalog_tiff_bytes"] == 330
    assert all(r["image_id"] != rows[0]["image_id"] for r in a)
    assert report["catalog_masks"] == 3 and report["target_met"]
    assert all(not r["mask_usable_verified"] for r in a)


def test_known_patient_exclusion_shortfall_and_provider_separation():
    rows, catalog = inputs()
    rows[0]["patient_id"] = rows[1]["patient_id"] = "same-patient"
    selected, report = propose(rows, catalog, {rows[0]["image_id"]}, provider="radboud", per_group=2)
    assert report["selected_counts"]["benign"] == 0 and not report["target_met"]
    assert all(r.get("patient_id") != "same-patient" for r in selected)
    assert propose(rows, catalog, set(), provider="karolinska", per_group=1)[0] == []


def test_bad_or_incomplete_catalog_rejected():
    rows, catalog = inputs()
    with pytest.raises(ValueError, match="Complete"):
        propose(rows, dict(catalog, complete=False), set(), provider="radboud")
    with pytest.raises(ValueError, match="Duplicate metadata"):
        propose(rows + rows[:1], catalog, set(), provider="radboud")
    with pytest.raises(ValueError, match="catalog"):
        propose(rows, dict(catalog, files=catalog["files"] * 2), set(), provider="radboud")


def test_existing_output_not_overwritten(tmp_path):
    import csv
    import json
    rows, catalog = inputs()
    train, cat, exclude = (tmp_path / n for n in ("train.csv", "catalog.json", "excluded.csv"))
    with train.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    cat.write_text(json.dumps(catalog)); exclude.write_text("image_id\n")
    output = tmp_path / "proposal"
    write_proposal(train, cat, [exclude], output, per_group=1)
    before = (output / "proposal.json").read_bytes()
    with pytest.raises(FileExistsError):
        write_proposal(train, cat, [exclude], output, per_group=1)
    assert (output / "proposal.json").read_bytes() == before
