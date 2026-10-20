from types import SimpleNamespace
from contextlib import nullcontext
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from floater_finder.tiling import connected_subset, extract_tiles, physical_grid, physical_metadata, region_geometry, spatial_windows


def test_calibration_requires_measured_isotropic_mpp():
    with pytest.raises(ValueError, match="MPP"):
        physical_metadata(SimpleNamespace(properties={"openslide.objective-power": "40"}))
    with pytest.raises(ValueError, match="isotropic"):
        physical_metadata(SimpleNamespace(properties={"openslide.mpp-x": ".25", "openslide.mpp-y": ".5"}))
    metadata = physical_metadata(SimpleNamespace(properties={"openslide.mpp-x": ".25", "openslide.mpp-y": ".25"}))
    assert metadata["microns_per_unit"] == .25 and metadata["objective_power"] is None


def test_subset_is_connected_deterministic_and_uses_largest_component():
    coords = np.array([[x, y] for x in range(4) for y in range(4)] + [[99, 99]]) * 1024
    indices, size = connected_subset(coords, 1024, 8)
    assert size == 16 and len(indices) == 8 and 16 not in indices
    np.testing.assert_array_equal(indices, connected_subset(coords, 1024, 8)[0])
    selected = set(map(tuple, coords[indices] // 1024))
    reached = {next(iter(selected))}
    while True:
        added = {p for p in selected if any(abs(p[0]-q[0])+abs(p[1]-q[1]) == 1 for q in reached)} - reached
        if not added:
            break
        reached.update(added)
    assert reached == selected
    with pytest.raises(ValueError, match="Duplicate"):
        connected_subset(np.array([[0, 0], [0, 0]]), 1024, 2)


def test_spatial_windows_are_disjoint_connected_separated_and_order_independent():
    cells = np.array([[x + dx, y + dy] for dx, dy in [(0, 0), (50, 0), (0, 50), (50, 50)]
                      for x in range(20) for y in range(20)])
    indices, summary = spatial_windows(cells)
    assert len(indices) == len(set(indices)) == 512
    chosen = cells[indices]
    for offset in range(0, 512, 128):
        window = chosen[offset:offset+128]
        assert connected_subset(window, 1, 128)[1] == 128
        if offset:
            minimum = np.sqrt(((window[:, None] - chosen[None, :offset]) ** 2).sum(axis=2).min()) * 256
            assert minimum >= 1000
    shuffled = cells[np.random.default_rng(42).permutation(len(cells))]
    np.testing.assert_array_equal(chosen, shuffled[spatial_windows(shuffled)[0]])
    assert all(w["tiles"] == 128 for w in summary["windows"])


def test_spatial_sampling_refuses_silent_reduction_and_duplicate_positions():
    with pytest.raises(ValueError, match="capacity"):
        spatial_windows(np.array([[x, 0] for x in range(128)]))
    with pytest.raises(ValueError, match="Duplicate"):
        spatial_windows(np.array([[0, 0], [0, 0]]))


def test_tiling_never_runs_outside_slurm(monkeypatch, tmp_path):
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    with pytest.raises(RuntimeError, match="Slurm"):
        extract_tiles({}, tmp_path / "tiles")
    assert not (tmp_path / "tiles").exists()


def test_resampling_has_the_same_physical_field_for_different_scanners():
    for mpp in [.2527, .2277]:
        cell = np.array([10, 20])
        origin, size, box = region_geometry(cell, mpp, 256)
        np.testing.assert_allclose((np.array(origin) + box[:2]) * mpp, cell * 256)
        np.testing.assert_allclose((np.array(box[2:]) - box[:2]) * mpp, [256, 256])
        assert box[0] >= 0 and box[1] >= 0 and box[2] <= size[0] and box[3] <= size[1]
    cells, excluded = physical_grid(np.array([[0, 0], [1, 1], [9999, 9999]]), 1024, .25, 256, np.array([4096, 4096]))
    assert cells.tolist() == [[0, 0]] and excluded == 1


def test_extraction_reads_pixels_and_coordinates_but_never_existing_features(monkeypatch, tmp_path):
    class Coordinates:
        shape = (4, 2)
        attrs = {"name": "fixture-slide", "level0_width": 16, "level0_height": 16,
                 "patch_size_level0": 4, "patch_size": 4, "overlap": 0, "target_magnification": 20}
        def __getitem__(self, key):
            return np.array([[0, 0], [4, 0], [0, 4], [4, 4]])
    class Handle:
        def __getitem__(self, key):
            assert key == "coords", "Existing model feature values must never be used"
            return Coordinates()
    class Raster:
        dimensions = (16, 16)
        properties = {"openslide.mpp-x": ".5", "openslide.mpp-y": ".5", "openslide.objective-power": "40"}
        def read_region(self, origin, level, size):
            assert level == 0 and origin[0] >= 0
            return Image.new("RGBA", size, (180, 90, 120, 255))
    monkeypatch.setenv("SLURM_JOB_ID", "software-fixture")
    monkeypatch.setitem(sys.modules, "h5py", SimpleNamespace(File=lambda *args: nullcontext(Handle())))
    monkeypatch.setitem(sys.modules, "openslide", SimpleNamespace(OpenSlide=lambda *args: nullcontext(Raster())))
    source = tmp_path / "fixture-slide.svs"
    source.write_bytes(b"fixture, not real pathology data")
    item = dict(path=str(source), slide_id=source.stem, bytes=source.stat().st_size, coordinate_h5="fixture-coords.h5",
                patient_id="fixture-patient", project="FIXTURE", organ="prostate", label="prostate", split="eval",
                diagnostic_provenance="artificial test", report_provenance=None, checksum={"algorithm":"md5","value":"fixture"})
    output = tmp_path / "tiles"
    result = extract_tiles(item, output, max_tiles=3, field_um=2, pixels=4)
    metadata = json.loads((output / "metadata.json").read_text())
    assert result["tiles"] == 3 and metadata["tile_step"] == [2, 2]
    assert metadata["microns_per_unit"] == 1 and metadata["measured_mpp_xy"] == [.5, .5]
    assert metadata["extraction"]["feature_values_read"] is False
    assert len(list(output.glob("c*.png"))) == 4  # three tiles plus contact sheet
    with pytest.raises(FileExistsError):
        extract_tiles(item, output)


def test_multiwindow_extraction_uses_the_same_selection_and_preserves_existing_output(monkeypatch, tmp_path):
    cells = np.array([[dx+x, dy+y] for dx, dy in [(0,0),(40,0),(0,40),(40,40)]
                      for x in range(8) for y in range(8)])
    class Coordinates:
        shape = (len(cells), 2)
        attrs = dict(name="fixture", level0_width=25600, level0_height=25600,
                     patch_size_level0=512, overlap=0, target_magnification=20)
        def __getitem__(self, key):
            return cells * 512
    class Handle:
        def __getitem__(self, key):
            assert key == "coords"
            return Coordinates()
    class Raster:
        dimensions = (25600, 25600)
        properties = {"openslide.mpp-x":".5", "openslide.mpp-y":".5"}
        def read_region(self, origin, level, size):
            return Image.new("RGBA", size, (180,90,120,255))
    monkeypatch.setenv("SLURM_JOB_ID", "software-fixture")
    monkeypatch.setitem(sys.modules, "h5py", SimpleNamespace(File=lambda *args: nullcontext(Handle())))
    monkeypatch.setitem(sys.modules, "openslide", SimpleNamespace(OpenSlide=lambda *args: nullcontext(Raster())))
    path = tmp_path / "fixture.svs"
    path.write_bytes(b"artificial software fixture")
    item = dict(path=str(path), slide_id=path.stem, bytes=path.stat().st_size, coordinate_h5="fixture.h5",
                patient_id="fixture-patient", project="FIXTURE", organ="prostate", label="prostate", split="dev",
                diagnostic_provenance="artificial test", report_provenance=None, checksum={"algorithm":"md5","value":"fixture"})
    output = tmp_path / "tiles"
    result = extract_tiles(item, output, max_tiles=16, pixels=8, windows=4)
    extraction = result["metadata"]["extraction"]
    assert result["tiles"] == 16 and extraction["window_sampling"]["window_count"] == 4
    np.testing.assert_array_equal(extraction["selected_physical_grid_cells"], cells[spatial_windows(cells, tiles_per_window=4)[0]])
    with pytest.raises(FileExistsError):
        extract_tiles(item, output, max_tiles=16, pixels=8, windows=4)


@pytest.mark.parametrize("script,arguments", [
    ("ncsa_pilot_preflight.py", ["--config", "absent", "--output", "absent"]),
    ("ncsa_runtime_preflight.py", ["--config", "absent", "--output", "absent"]),
    ("ncsa_one_pair_smoke.py", ["--config", "absent", "--prompts", "absent", "--output", "absent"]),
    ("ncsa_bidirectional_smoke.py", ["--input", "absent", "--prompts", "absent", "--output", "absent"]),
    ("ncsa_detector_smoke.py", ["--development", "absent", "--evaluation", "absent", "--config", "absent", "--output", "absent"]),
])
def test_scheduled_scripts_fail_before_model_import_or_io_on_login_nodes(monkeypatch, tmp_path, script, arguments):
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    source = Path(__file__).resolve().parents[1] / "scripts" / script
    result = subprocess.run([sys.executable, str(source), *arguments], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2 and "Slurm" in result.stderr
    assert list(tmp_path.iterdir()) == []
