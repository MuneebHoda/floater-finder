import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

tifffile = pytest.importorskip("tifffile", reason="Install the panda extra for TIFF integration tests")
pytest.importorskip("openslide", reason="Install the panda extra for region-reader tests")

from floater_finder.panda import extract_panda_tiles, label_fractions, panda_input, panda_readers


def pyramid(path, data, mpp=(.5, .5), unit="CENTIMETER", orientation=1):
    with tifffile.TiffWriter(path) as writer:
        for level, factor in enumerate((1, 4, 16)):
            writer.write(data[::factor, ::factor], photometric="rgb", tile=(16, 16),
                subfiletype=1 if level else 0, metadata=None, compression="deflate",
                resolution=(10000 / mpp[0] / factor, 10000 / mpp[1] / factor), resolutionunit=unit,
                extratags=[(274, "H", 1, orientation, False)])


def dataset(tmp_path, mask=True):
    root = tmp_path / "panda"
    (root / "train_images").mkdir(parents=True)
    (root / "train_label_masks").mkdir()
    (root / "train.csv").write_text("image_id,data_provider,isup_grade,gleason_score\nfixture,radboud,4,4+4\n")
    (root / "pilot.csv").write_text("image_id\nfixture\n")
    image = np.full((320, 320, 3), 255, np.uint8)
    image[:64, 64:192] = [180, 70, 120]
    pyramid(root / "train_images/fixture.tiff", image)
    if mask:
        labels = np.zeros((320, 320, 3), np.uint8)
        labels[:, :, 1:] = 77  # Other channels are not Gleason labels.
        labels[:64, 64:96, 0] = 2
        labels[:64, 96:112, 0] = 3
        labels[:64, 112:128, 0] = 4
        labels[:64, 128:160, 0] = 1
        labels[:64, 160:192, 0] = 5
        pyramid(root / "train_label_masks/fixture_mask.tiff", labels)
    return root


def extract(root, output, monkeypatch, **kwargs):
    monkeypatch.setenv("SLURM_JOB_ID", "software-fixture-only")
    options = dict(field_um=32., pixels=64, max_tiles=2, max_candidates=20,
                   source_kind="fixture", recorded_mpp_xy=[.5, .5])
    options.update(kwargs)
    return extract_panda_tiles(root, "fixture", output, **options)


def test_real_tiff_backend_pyramid_mask_alignment_and_scale(tmp_path):
    root = dataset(tmp_path)
    item = panda_input(root, "fixture")
    with panda_readers(item["image_path"], item["mask_path"], [.5, .5]) as (image, mask, metadata):
        assert image.level_dimensions == mask.level_dimensions == ((320, 320), (80, 80), (20, 20))
        assert metadata["pyramid_downsamples"] == [1., 4., 16.]
        assert metadata["measured_mpp_xy"] == [.5, .5]
        assert metadata["mask_channel"] == 0
        assert metadata["input_files"]["image"]["full_checksum_verified"] is False
        assert np.asarray(mask.read_region((96, 0), 0, (1, 1)))[0, 0, 0] == 3


@pytest.mark.parametrize("fault", ["dimensions", "orientation"])
def test_alignment_rejects_mask_dimensions_and_orientation(tmp_path, fault):
    root = dataset(tmp_path)
    mask = root / "train_label_masks/fixture_mask.tiff"
    mask.unlink()
    shape = (336, 320, 3) if fault == "dimensions" else (320, 320, 3)
    pyramid(mask, np.zeros(shape, np.uint8), orientation=3 if fault == "orientation" else 1)
    with pytest.raises(ValueError, match="alignment"):
        with panda_readers(root / "train_images/fixture.tiff", mask):
            pass


def test_tissue_exclusion_geometry_labels_and_slide_provenance(tmp_path, monkeypatch):
    root, output = dataset(tmp_path), tmp_path / "tiles"
    result = extract(root, output, monkeypatch)
    with (output / "tiles.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert result["tiles"] == len(rows) == 2
    # First grid cell is white, even though the slide itself has grade 4.
    assert [(row["grid_x"], row["grid_y"]) for row in rows] == [("1", "0"), ("2", "0")]
    assert [(float(row["x"]), float(row["y"])) for row in rows] == [(32., 0.), (64., 0.)]
    assert float(rows[0]["area_mm2"]) == pytest.approx(.001024)
    assert float(rows[0]["benign_fraction"]) == .5
    assert float(rows[0]["gleason3_fraction"]) == .25
    assert float(rows[0]["gleason4_fraction"]) == .25
    assert float(rows[0]["gleason5_fraction"]) == 0
    assert float(rows[1]["stroma_fraction"]) == .5
    assert float(rows[1]["gleason5_fraction"]) == .5
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["source_kind"] == "fixture"
    assert metadata["patient_id"] == "unknown" and not metadata["patient_id_known"]
    assert metadata["data_provider"] == "radboud" and metadata["isup_grade"] == 4
    assert metadata["tile_step"] == metadata["tile_size"] == [32., 32.]
    assert metadata["extraction"]["candidates_examined"] == 3
    assert not metadata["extraction"]["complete_piece_topology_verified"]
    assert len(metadata["train_csv_sha256"]) == 64
    with Image.open(output / rows[0]["path"]) as tile:
        assert tile.size == (64, 64) and tile.mode == "RGB"
    with pytest.raises(FileExistsError):
        extract(root, output, monkeypatch)


def test_missing_mask_stays_unknown_instead_of_broadcasting_slide_grade(tmp_path, monkeypatch):
    output = tmp_path / "tiles"
    result = extract(dataset(tmp_path, mask=False), output, monkeypatch)
    assert result["metadata"]["isup_grade"] == 4
    assert not result["metadata"]["panda"]["mask_available"]
    with (output / "tiles.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert all(row["benign_fraction"] == row["gleason4_fraction"] == "" for row in rows)


def test_panda_metadata_to_saved_embedding_piece_engine(tmp_path, monkeypatch):
    from conftest import MODEL
    from floater_finder.artifacts import Slide
    from floater_finder.fragment_dependence import analyze_saved_slide
    output = tmp_path / "tiles"
    result = extract(dataset(tmp_path), output, monkeypatch)
    with (output / "tiles.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    metadata = result["metadata"] | {"model": MODEL.copy()}
    path = tmp_path / "slide.fixture.npz"
    # Artificial unit vectors exercise the saved format; no CONCH inference occurs.
    Slide(np.tile([1., 0.], (len(rows), 1)), np.array([[float(row["x"]), float(row["y"])] for row in rows]),
          np.array([row["tile_id"] for row in rows]), metadata).save(path)
    report = analyze_saved_slide(path, lambda *_: {"prediction": "benign"}, scorer_id="constant-fixture")
    assert report["source_kind"] == "fixture"
    assert report["slide_provenance"]["data_provider"] == "radboud"
    assert not report["slide_provenance"]["patient_id_known"]
    assert report["geometry"]["tile_size"] == [32., 32.]
    assert report["baseline"]["prediction"] == "benign"  # Never substituted from slide grade 4.
    assert report["pieces"][0]["area_mm2"] == pytest.approx(.002048)


def test_rounding_records_realized_physical_footprint(tmp_path, monkeypatch):
    root = dataset(tmp_path)
    result = extract(root, tmp_path / "tiles", monkeypatch, field_um=31.9)
    metadata = result["metadata"]
    assert metadata["requested_field_um"] == 31.9
    assert metadata["realized_field_um_xy"] == [32., 32.]
    assert metadata["footprint_level0_pixels_xy"] == [64, 64]


def test_bounded_reads_use_pyramid_and_never_read_whole_wsi(tmp_path, monkeypatch):
    import openslide
    root, calls = dataset(tmp_path), []
    original = openslide.OpenSlide.read_region
    def read(slide, origin, level, size):
        calls.append((level, size))
        assert np.prod(size) <= 128 * 128
        return original(slide, origin, level, size)
    monkeypatch.setattr(openslide.OpenSlide, "read_region", read)
    result = extract(root, tmp_path / "tiles", monkeypatch, field_um=64, pixels=32, max_tiles=1)
    assert result["metadata"]["extraction"]["image_level"] == 1
    assert {level for level, size in calls} == {0, 1, 2}


def test_candidate_cap_failure_retains_metadata_and_no_false_success(tmp_path, monkeypatch):
    root, output = dataset(tmp_path), tmp_path / "tiles"
    with pytest.raises(ValueError, match="No tissue"):
        extract(root, output, monkeypatch, max_tiles=1, max_candidates=1)
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["extraction"]["candidates_examined"] == 1
    assert not (output / "tiles.csv").exists()


@pytest.mark.parametrize("fault", ["unit", "recorded_scale", "provider", "pilot_label", "unsafe_id"])
def test_rejects_ambiguous_scale_provider_labels_or_path(tmp_path, monkeypatch, fault):
    root = dataset(tmp_path)
    if fault == "provider":
        (root / "train.csv").write_text("image_id,data_provider,isup_grade,gleason_score\nfixture,karolinska,4,4+4\n")
    if fault == "pilot_label":
        (root / "pilot.csv").write_text("image_id,isup_grade\nfixture,0\n")
    if fault == "unsafe_id":
        with pytest.raises(ValueError):
            panda_input(root, "../fixture")
        return
    if fault == "unit":
        path = root / "train_images/fixture.tiff"
        path.unlink()
        pyramid(path, np.zeros((320, 320, 3), np.uint8), unit="NONE")
    options = {"recorded_mpp_xy": [.486, .486]} if fault == "recorded_scale" else {}
    with pytest.raises(ValueError):
        extract(root, tmp_path / "tiles", monkeypatch, **options)


def test_mask_background_fraction_and_invalid_label():
    mask = np.zeros((2, 3, 3), np.uint8)
    mask[:, :, 0] = [[0, 1, 2], [3, 4, 5]]
    fractions = label_fractions(mask)
    assert all(value == pytest.approx(1 / 6) for value in fractions.values())
    mask[0, 0, 0] = 7
    with pytest.raises(ValueError, match="labels"):
        label_fractions(mask)


def test_manifest_passes_existing_encoder_input_contract_without_inference(tmp_path, monkeypatch):
    from floater_finder import conch
    from floater_finder.experiments import read_config
    output = tmp_path / "tiles"
    extract(dataset(tmp_path), output, monkeypatch)
    project = Path(__file__).resolve().parents[1]
    class ReachedCanonicalEncoder(Exception):
        pass
    def stop_before_inference(checkpoint):
        raise ReachedCanonicalEncoder
    monkeypatch.setattr(conch, "ConchEncoder", stop_before_inference)
    prompts = project / "configs/panda_zero_shot_smoke.yaml"
    assert set(read_config(prompts)["prompts"]) == {"benign", "cancer"}
    with pytest.raises(ReachedCanonicalEncoder):
        conch.encode_tiles(output / "tiles.csv", output / "metadata.json", prompts,
                           "unused-fixture-checkpoint", tmp_path / "not-created", max_tiles=2)
    assert not (tmp_path / "not-created").exists()


def test_no_slurm_fails_before_filesystem_or_model_io(tmp_path, monkeypatch):
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    with pytest.raises(RuntimeError, match="Slurm"):
        extract_panda_tiles("absent", "fixture", tmp_path / "absent")
    script = Path(__file__).resolve().parents[1] / "scripts/ncsa_panda_smoke.py"
    result = subprocess.run([sys.executable, str(script), "--stage", "encode", "--output", "absent"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2 and "Slurm" in result.stderr
    assert list(tmp_path.iterdir()) == []


def smoke_module():
    path = Path(__file__).resolve().parents[1] / "scripts/ncsa_panda_smoke.py"
    spec = importlib.util.spec_from_file_location("panda_smoke", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_config(root, path):
    project = Path(__file__).resolve().parents[1]
    config = json.loads((project / "configs/panda_smoke.json").read_text())
    config.update(root=str(root), source_kind="fixture", field_um=32., export_pixels=64,
                  max_tiles_per_slide=2, max_candidates_per_slide=20, recorded_mpp_xy=[.5, .5],
                  slides=[dict(image_id="fixture", isup_grade=4, mask_available=True)])
    path.write_text(json.dumps(config))
    return config


def test_cpu_runner_tiff_roundtrip_hashes_and_fixture_guard(tmp_path, monkeypatch):
    monkeypatch.setenv("SLURM_JOB_ID", "software-fixture-only")
    root, path, output = dataset(tmp_path), tmp_path / "config.json", tmp_path / "cpu"
    fixture_config(root, path)
    module = smoke_module()
    report = module.run(path, output, "tile")
    assert report["source_kind"] == "fixture" and report["category"] == "fixture_software_check"
    assert report["total_tiles"] == 2 and len(report["slides"]) == 1
    assert len(report["slides"][0]["tile_png_sha256"]) == 2
    assert not report["clinical_model_validity_verified"]
    assert json.loads((output / "tiling.json").read_text())["status"] == "passed"
    with pytest.raises(FileExistsError):
        module.run(path, output, "tile")
    with pytest.raises(ValueError, match="Fixture"):
        module.run(path, tmp_path / "gpu", "encode", output)
    assert not (tmp_path / "gpu").exists()


def test_runner_rejects_scope_and_wrong_original_labels(tmp_path, monkeypatch):
    monkeypatch.setenv("SLURM_JOB_ID", "software-fixture-only")
    root, path = dataset(tmp_path), tmp_path / "config.json"
    config = fixture_config(root, path)
    module = smoke_module()
    config["max_tiles_per_slide"] = 1000
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="scope"):
        module.run(path, tmp_path / "too-large", "tile")
    assert not (tmp_path / "too-large").exists()
    config["max_tiles_per_slide"] = 2
    config["slides"][0]["isup_grade"] = 0
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="Original labels"):
        module.run(path, tmp_path / "wrong-label", "tile")
    assert not (tmp_path / "wrong-label/tiling.json").exists()
    config["slides"][0].update(isup_grade=4, gleason_score="3+5")
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="Original labels"):
        module.run(path, tmp_path / "wrong-gleason", "tile")
    assert not (tmp_path / "wrong-gleason/tiling.json").exists()


def test_representative_scans_full_grid_is_seeded_and_mask_independent(tmp_path, monkeypatch):
    root = dataset(tmp_path)
    result = extract(root, tmp_path/'rep', monkeypatch, selection='representative', max_candidates=25, max_tiles=1)
    meta = result['metadata']['extraction']
    assert meta['candidates_examined'] == meta['total_grid_cells'] == 25
    assert meta['eligible_tissue_cells'] == 2
    assert not meta['selection_uses_mask'] and meta['clean_evaluation_eligible']
    (root/'train_label_masks/fixture_mask.tiff').unlink()
    extract(root, tmp_path/'rep2', monkeypatch, selection='representative', max_candidates=25, max_tiles=1)
    def coords(path):
        with path.open() as f:
            return [(r['grid_x'],r['grid_y']) for r in csv.DictReader(f)]
    assert coords(tmp_path/'rep/tiles.csv') == coords(tmp_path/'rep2/tiles.csv')
    with pytest.raises(ValueError, match='Full grid'):
        extract(root, tmp_path/'bounded', monkeypatch, selection='representative', max_candidates=20)


def test_donor_mode_and_native_full_mask_area(tmp_path, monkeypatch):
    from floater_finder.panda_masks import audit_mask
    root = dataset(tmp_path)
    result = extract(root, tmp_path/'donor', monkeypatch, selection='donor', max_candidates=25,
                     max_tiles=512, min_cancer_fraction=.3)
    assert result['tiles'] == 1
    assert result['metadata']['extraction']['selection_uses_mask']
    assert not result['metadata']['extraction']['clean_evaluation_eligible']
    with panda_readers(root/'train_images/fixture.tiff', root/'train_label_masks/fixture_mask.tiff') as (_, mask, meta):
        audited = audit_mask(mask, meta['measured_mpp_xy'], block=48)
    assert audited['native_pixel_counts']['gleason4'] == 64*16
    assert audited['native_pixel_counts']['gleason5'] == 64*32
    assert audited['area_mm2']['gleason4'] == pytest.approx(64*16*.5*.5/1e6)
    assert audited['gp45_bbox_level0_xyxy'] == [112,0,192,64]
    (root/'train_label_masks/fixture_mask.tiff').unlink()
    with pytest.raises(ValueError, match='requires a verified'):
        extract(root, tmp_path/'no-mask', monkeypatch, selection='donor', max_candidates=25)


def test_explicit_manifest_preserves_authority_and_cohort_split(tmp_path, monkeypatch):
    root = dataset(tmp_path)
    manifest = root/'new.csv'
    manifest.write_text('image_id,split,isup_grade\nfixture,test,4\n')
    result = extract(root, tmp_path/'tiles', monkeypatch, manifest_path=manifest)
    assert result['metadata']['cohort_split'] == 'test'
    assert result['metadata']['split'] == 'eval'
    manifest.write_text('image_id,isup_grade\nfixture,0\n')
    with pytest.raises(ValueError, match='disagrees'):
        panda_input(root, 'fixture', manifest)


def test_cohort_tiling_checkpoint_reuses_and_rejects_changed_outputs(tmp_path,monkeypatch):
    path=Path(__file__).resolve().parents[1]/'scripts/panda_tile_cohort.py'
    spec=importlib.util.spec_from_file_location('panda_tile_cohort',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    root=dataset(tmp_path);output=tmp_path/'batch'
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only')
    result=module.run(root,root/'pilot.csv',output,count=1,max_tiles=256)
    assert result[0]['status']=='tiled_validated'
    assert module.run(root,root/'pilot.csv',output,count=1,max_tiles=256)[0]['status']=='reused_validated'
    (output/'fixture/tiles.csv').write_text('changed')
    with pytest.raises(ValueError,match='preserved for inspection'):
        module.run(root,root/'pilot.csv',output,count=1,max_tiles=256)


def test_independent_mask_diagnostic_preserves_native_inputs(tmp_path,monkeypatch):
    path=Path(__file__).resolve().parents[1]/'scripts/ncsa_panda_mask_diagnostic.py'
    spec=importlib.util.spec_from_file_location('panda_mask_diagnostic',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    root=dataset(tmp_path);output=tmp_path/'diagnostic.fixture.json'
    monkeypatch.setenv('SLURM_JOB_ID','software-fixture-only')
    module.run(root,root/'pilot.csv','fixture',output)
    report=json.loads(output.read_text())
    assert report['inputs_modified'] is False and report['mask_sha256']==report['mask_sha256_after']
    assert report['pillow_native_decode_passed']
    assert report['pillow_native_pixel_counts']==report['openslide_audit']['native_pixel_counts']


def test_explicit_unusable_mask_exclusion_keeps_annotations_unknown_and_source_unchanged(tmp_path,monkeypatch):
    from floater_finder.experiments import file_sha256
    root=dataset(tmp_path);path=root/'train_label_masks/fixture_mask.tiff';digest=file_sha256(path)
    exclusion=dict(sha256=digest,reason='Simulated decoder failure in software fixture only')
    result=extract(root,tmp_path/'excluded',monkeypatch,mask_exclusion=exclusion)
    assert not result['metadata']['panda']['mask_available']
    assert result['metadata']['panda']['excluded_mask']['sha256']==digest
    assert path.is_file() and file_sha256(path)==digest
    with (tmp_path/'excluded/tiles.csv').open() as handle:
        assert all(r['gleason4_fraction']=='' for r in csv.DictReader(handle))
    with pytest.raises(ValueError,match='exact existing mask'):
        extract(root,tmp_path/'wrong',monkeypatch,mask_exclusion=exclusion|dict(sha256='0'*64))
    with pytest.raises(ValueError,match='requires a verified'):
        extract(root,tmp_path/'donor-excluded',monkeypatch,mask_exclusion=exclusion,selection='donor',max_candidates=25)
