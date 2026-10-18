"""Bounded raw-pixel extraction at verified existing tissue coordinates."""

from collections import deque
import csv
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from .artifacts import write_json
from .experiments import file_sha256
from .injection import grid_neighbors


def physical_metadata(slide):
    """Read measured calibration; never infer MPP from objective magnification."""
    try:
        x, y = [float(slide.properties[key]) for key in ("openslide.mpp-x", "openslide.mpp-y")]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Measured OpenSlide MPP X/Y are required") from error
    if not np.isfinite([x, y]).all() or min(x, y) <= 0 or not np.isclose(x, y, rtol=0, atol=1e-8):
        raise ValueError("This pipeline requires finite, positive, isotropic measured MPP")
    objective = slide.properties.get("openslide.objective-power")
    return {"coordinate_units": "level0_pixels", "coordinate_reference": "top-left pixel of extracted region",
            "microns_per_unit": x, "measured_mpp_xy": [x, y],
            "objective_power": float(objective) if objective is not None else None,
            "scale_provenance": "OpenSlide openslide.mpp-x and openslide.mpp-y header properties"}


def connected_subset(coords, step, cap):
    """Deterministic BFS around the largest component's center, for smoke tests."""
    coords = np.asarray(coords)
    if coords.ndim != 2 or coords.shape[1] != 2 or len(coords) == 0 or not isinstance(cap, int) or cap < 1:
        raise ValueError("Nonempty Nx2 coordinates and a positive cap are required")
    neighbors = grid_neighbors(SimpleNamespace(coords=coords, metadata={"tile_step": [step, step]}))
    remaining = set(range(len(coords)))
    components = []
    while remaining:
        start = min(remaining)
        queue, component = deque([start]), []
        remaining.remove(start)
        while queue:
            index = queue.popleft()
            component.append(index)
            for other in neighbors[index]:
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
        components.append(component)
    component = max(components, key=len)
    center = coords[component].mean(axis=0)
    start = min(component, key=lambda i: (float(np.sum((coords[i] - center) ** 2)), i))
    queue, seen, chosen = deque([start]), {start}, []
    while queue and len(chosen) < cap:
        index = queue.popleft()
        chosen.append(index)
        for other in neighbors[index]:
            if other not in seen:
                seen.add(other)
                queue.append(other)
    return np.asarray(chosen), len(component)


def physical_grid(coords, source_footprint, mpp, field_um, dimensions):
    """Use existing tissue-region centers as candidates on a common physical grid."""
    if not np.isfinite(field_um) or field_um <= 0:
        raise ValueError("Positive physical field size required")
    cells = np.unique(np.floor((coords + source_footprint / 2) * mpp / field_um).astype(np.int64), axis=0)
    inside = np.all(cells >= 0, axis=1) & np.all((cells + 1) * field_um / mpp <= dimensions, axis=1)
    return cells[inside], int((~inside).sum())


def region_geometry(cell, mpp, field_um):
    """Integer read bounds plus fractional crop for the exact requested physical FOV."""
    start = np.asarray(cell) * field_um / mpp
    end = (np.asarray(cell) + 1) * field_um / mpp
    origin = np.floor(start).astype(int)
    size = np.ceil(end).astype(int) - origin
    box = tuple(np.concatenate([start - origin, end - origin]))
    return tuple(map(int, origin)), tuple(map(int, size)), box


def extract_tiles(item, output, max_tiles=128, field_um=256, pixels=512):
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("WSI extraction requires an authorized Slurm job")
    import h5py
    import openslide

    output = Path(output)
    if output.exists():
        raise FileExistsError("Preserve existing tile output")
    path = Path(item["path"])
    if path.stat().st_size != item["bytes"] or path.stem != item["slide_id"]:
        raise ValueError("WSI identity/size differs from verified input")
    with openslide.OpenSlide(path) as slide, h5py.File(item["coordinate_h5"], "r") as handle:
        metadata = physical_metadata(slide)
        dataset = handle["coords"]
        attrs = dataset.attrs
        if dataset.shape[0] > 20000 or dataset.shape[1:] != (2,):
            raise ValueError("Unexpected or oversized coordinate source")
        if attrs["name"] != path.stem or tuple(slide.dimensions) != (int(attrs["level0_width"]), int(attrs["level0_height"])):
            raise ValueError("Coordinate source does not match raw WSI")
        footprint = int(attrs["patch_size_level0"])
        if footprint < 1 or footprint > 4096 or pixels < 1 or pixels > 2048 or attrs["overlap"] != 0:
            raise ValueError("Unsupported coordinate extraction geometry")
        coords = dataset[:]
        if coords.dtype.kind not in "iu":
            raise ValueError("Expected integer level-0 coordinates")
        coordinate_sha = hashlib.sha256(coords.tobytes()).hexdigest()
        cells, excluded = physical_grid(coords, footprint, metadata["microns_per_unit"], field_um, np.asarray(slide.dimensions))
        selected, component_size = connected_subset(cells, 1, max_tiles)
        output.mkdir(parents=True, exist_ok=False)
        rows, regions = [], []
        contact = Image.new("RGB", (8 * 96, ((len(selected) + 7) // 8) * 96), "white")
        for order, index in enumerate(selected):
            cell = cells[index]
            x, y = cell * field_um
            origin, size, box = region_geometry(cell, metadata["microns_per_unit"], field_um)
            if max(size) > 4096:
                raise ValueError("Requested physical tile exceeds bounded pixel reads")
            tile_id = f"c{cell[0]}_r{cell[1]}"
            image = slide.read_region(origin, 0, size)
            if np.asarray(image.getchannel("A")).min() != 255:
                raise ValueError("Transparent pixels in an in-bounds region; stop extraction")
            image = image.convert("RGB").resize((pixels, pixels), Image.Resampling.BICUBIC, box=box)
            image.save(output / (tile_id + ".png"))
            contact.paste(image.resize((96, 96)), ((order % 8) * 96, (order // 8) * 96))
            rows.append({"tile_id": tile_id, "path": tile_id + ".png", "x": x, "y": y})
            regions.append({"tile_id": tile_id, "read_origin_level0": list(map(int, origin)),
                            "read_size_level0": list(map(int, size)), "fractional_resize_box": list(box)})
        contact.save(output / "contact_sheet.png")
        with (output / "tiles.csv").open("x", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["tile_id", "path", "x", "y"])
            writer.writeheader()
            writer.writerows(rows)
        metadata.update({key: item[key] for key in ("slide_id", "patient_id", "project", "organ", "label", "split", "diagnostic_provenance", "report_provenance")})
        metadata.update(source_kind="real", tile_step=[field_um, field_um],
                        coordinate_units="microns", microns_per_unit=1.0, magnification=None,
                        coordinate_reference="requested physical tile top-left on a resampled regular grid",
                        extraction={"kind": "connected tile subset; not a full slide", "max_tiles": max_tiles,
                            "tiles": len(rows), "source_coordinate_count": len(coords),
                            "largest_in_bounds_component": component_size, "out_of_bounds_candidate_cells_excluded": excluded,
                            "selection": "largest component; nearest centroid start; deterministic four-neighbor BFS",
                            "coordinate_h5": item["coordinate_h5"], "coordinate_sha256": coordinate_sha,
                            "selected_physical_grid_cells": cells[selected].tolist(), "feature_values_read": False,
                            "candidate_mapping": "source tissue-region centers mapped to containing physical-grid cells; duplicates collapsed",
                            "source_wsi": str(path), "source_wsi_checksum": item["checksum"],
                            "source_mask_footprint_level0_pixels": footprint, "export_pixels": pixels,
                            "field_um": field_um, "output_microns_per_pixel": field_um / pixels,
                            "source_target_magnification": float(attrs["target_magnification"]),
                            "resampling": "OpenSlide level0 RGBA; require opaque; RGB; fractional physical FOV via Pillow BICUBIC resize box",
                            "color_handling": "Stored RGB values; no ICC conversion or stain normalization"})
        metadata["extraction"]["tile_manifest_sha256"] = file_sha256(output / "tiles.csv")
        write_json(output / "regions.json", regions)
        write_json(output / "metadata.json", metadata)
        return {"tiles": len(rows), "metadata": metadata, "tile_manifest": str(output / "tiles.csv")}
