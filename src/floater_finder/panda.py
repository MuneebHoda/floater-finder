"""Bounded PANDA/Radboud tiling, independent of the frozen TCGA tiler."""

from contextlib import ExitStack, contextmanager
import csv
import importlib.metadata
import os
from pathlib import Path
import re

import numpy as np
from PIL import Image

from .artifacts import write_json
from .experiments import file_sha256
from .image_runtime import require_image_runtime


LABELS = ("background", "stroma", "benign", "gleason3", "gleason4", "gleason5")


def _csv_row(path, image_id, limit=20000):
    found = None
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "image_id" not in reader.fieldnames:
            raise ValueError(f"Missing image_id column: {path}")
        for index, row in enumerate(reader):
            if index >= limit:
                raise ValueError(f"CSV exceeds bounded {limit}-row inspection: {path}")
            if row["image_id"] == image_id:
                if found is not None:
                    raise ValueError(f"Duplicate image_id: {image_id}")
                found = row
    if found is None:
        raise ValueError(f"image_id not found in {path}: {image_id}")
    return found


def _resolve_tiff(directory, stems, required):
    matches = [directory / (stem + suffix) for stem in stems for suffix in (".tiff", ".tif")
               if (directory / (stem + suffix)).is_file()]
    if len(matches) > 1 or (required and not matches):
        raise ValueError(f"Expected one unambiguous TIFF in {directory} for {stems}")
    return matches[0] if matches else None


def panda_input(root, image_id):
    """Resolve only the selected pilot biopsy; train.csv remains label authority."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", image_id):
        raise ValueError("Unsafe image_id")
    root = Path(root).resolve()
    pilot = _csv_row(root / "pilot.csv", image_id, limit=100)
    label = _csv_row(root / "train.csv", image_id)
    if label.get("data_provider") != "radboud":
        raise ValueError("Only verified Radboud mask semantics are supported")
    try:
        grade = int(label["isup_grade"])
    except (KeyError, ValueError) as error:
        raise ValueError("Invalid slide-level ISUP grade") from error
    if grade not in range(6) or not label.get("gleason_score"):
        raise ValueError("Missing/invalid original slide-level labels")
    for key in ("data_provider", "isup_grade", "gleason_score"):
        if pilot.get(key) and pilot[key] != label[key]:
            raise ValueError(f"pilot.csv disagrees with train.csv: {key}")
    image = _resolve_tiff(root / "train_images", [image_id], True)
    mask = _resolve_tiff(root / "train_label_masks", [image_id + "_mask", image_id], False)
    return {"image_id": image_id, "image_path": image, "mask_path": mask,
            "provider": "radboud", "isup_grade": grade, "gleason_score": label["gleason_score"],
            "train_csv_sha256": file_sha256(root / "train.csv"),
            "pilot_csv_sha256": file_sha256(root / "pilot.csv")}


def _header(path):
    # tifffile reads TIFF tags here, never page.asarray() or an entire image plane.
    from tifffile import TiffFile
    with TiffFile(path) as tif:
        page = tif.pages[0]
        tags = page.tags
        orientation = int(tags["Orientation"].value) if "Orientation" in tags else 1
        resolution = {}
        for name in ("XResolution", "YResolution", "ResolutionUnit"):
            resolution[name] = tags[name].value if name in tags else None
        return {"dimensions": [int(tags["ImageWidth"].value), int(tags["ImageLength"].value)],
                "orientation": orientation, "resolution_tags": resolution,
                "compression": int(page.compression), "photometric": int(page.photometric),
                "samples_per_pixel": page.samplesperpixel, "bits_per_sample": page.bitspersample}


def _mpp(header, recorded_mpp_xy):
    tags = header["resolution_tags"]
    unit_um = {2: 25400., 3: 10000.}.get(tags["ResolutionUnit"])
    try:
        resolution = [float(value[0]) / float(value[1]) if isinstance(value, tuple) else float(value)
                      for value in (tags["XResolution"], tags["YResolution"])]
        if unit_um is None or not np.isfinite(resolution).all() or min(resolution) <= 0:
            raise ValueError
        mpp = np.array([unit_um / value for value in resolution])
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("Physical TIFF X/Y resolution and inch/centimeter units are required") from error
    if recorded_mpp_xy is not None:
        recorded = np.asarray(recorded_mpp_xy, dtype=float)
        if recorded.shape != (2,) or not np.isfinite(recorded).all() or np.any(recorded <= 0):
            raise ValueError("recorded_mpp_xy must be positive measured X/Y scale")
        if not np.allclose(mpp, recorded, rtol=.01, atol=0):
            raise ValueError("TIFF calibration differs by more than 1% from recorded MPP")
    return mpp


@contextmanager
def panda_readers(image_path, mask_path=None, recorded_mpp_xy=None):
    """Inspect headers and pyramid alignment without decoding a full image plane."""
    import openslide
    image_path = Path(image_path)
    image_header = _header(image_path)
    mpp = _mpp(image_header, recorded_mpp_xy)
    with ExitStack() as stack:
        image = stack.enter_context(openslide.OpenSlide(image_path))
        dimensions = [list(level) for level in image.level_dimensions]
        factors = list(image.level_downsamples)
        if (image_header["orientation"] != 1 or list(image.dimensions) != image_header["dimensions"] or
                len(dimensions) != 3 or not np.allclose(factors, [1, 4, 16], rtol=.005, atol=0)):
            raise ValueError("Unsupported PANDA image orientation/pyramid; expected factors 1,4,16")
        mask, mask_header = None, None
        if mask_path is not None:
            mask_header = _header(mask_path)
            if (mask_header["photometric"] != 2 or mask_header["samples_per_pixel"] not in (3, 4) or
                    mask_header["bits_per_sample"] != 8):
                raise ValueError("Radboud masks must contain 8-bit RGB/RGBA label channels")
            mask = stack.enter_context(openslide.OpenSlide(mask_path))
            if (mask_header["orientation"] != 1 or mask_header["dimensions"] != image_header["dimensions"] or
                    list(mask.level_dimensions) != list(image.level_dimensions) or
                    not np.allclose(mask.level_downsamples, factors, rtol=0, atol=1e-6)):
                raise ValueError("Image/mask pyramid alignment mismatch")
        identities = {}
        for role, path in (("image", image_path), ("mask", mask_path)):
            if path is not None:
                stat = Path(path).stat()
                identities[role] = {"path": str(Path(path).resolve()), "bytes": stat.st_size,
                                    "mtime_ns": stat.st_mtime_ns, "full_checksum_verified": False}
        metadata = {"pyramid_dimensions": dimensions, "pyramid_downsamples": factors,
                    "measured_mpp_xy": mpp.tolist(),
                    "recorded_mpp_xy": None if recorded_mpp_xy is None else np.asarray(recorded_mpp_xy).tolist(),
                    "scale_provenance": "Level-0 TIFF XResolution/YResolution/ResolutionUnit tags",
                    "image_header": image_header, "mask_header": mask_header,
                    "mask_available": mask is not None, "mask_channel": 0 if mask else None,
                    "mask_label_mapping": dict(enumerate(LABELS)), "input_files": identities,
                    "alignment_check": "matching dimensions/downsamples/orientation; not histological registration proof"}
        yield image, mask, metadata


def _rgb_region(slide, origin, footprint, level, pixels):
    downsample = slide.level_downsamples[level]
    # Align reads to the selected level's grid, then crop the exact physical box.
    aligned = np.floor(np.asarray(origin) / downsample) * downsample
    location = np.floor(aligned).astype(int)
    offset = (np.asarray(origin) - location) / downsample
    extent = np.asarray(footprint) / downsample
    size = np.ceil(offset + extent).astype(int)
    if np.prod(size) > 4_000_000:
        raise ValueError("Region exceeds four-million-pixel read bound")
    region = slide.read_region(tuple(location), level, tuple(size))
    background = Image.new("RGBA", region.size, "white")
    background.alpha_composite(region)
    return background.convert("RGB").resize((pixels, pixels), Image.Resampling.BICUBIC,
        box=tuple(offset) + tuple(offset + extent))


def label_fractions(mask_region):
    """Radboud channel 0 only; fractions use all pixels, not just annotated tissue."""
    values = np.asarray(mask_region)
    if values.ndim != 3 or values.shape[2] not in (3, 4) or not values.size:
        raise ValueError("Expected an RGB/RGBA Radboud mask region")
    labels = values[:, :, 0]
    if not np.isin(labels, range(6)).all():
        raise ValueError("Unexpected Radboud channel-0 mask labels")
    if values.shape[2] == 4 and not np.all(values[:, :, 3] == 255):
        raise ValueError("Mask region extends outside valid aligned pixels")
    counts = np.bincount(labels.reshape(-1), minlength=6)
    return {name + "_fraction": float(count / labels.size) for name, count in zip(LABELS, counts)}


def extract_panda_tiles(root, image_id, output, *, field_um=112., pixels=224, max_tiles=32,
                        max_candidates=4096, min_tissue_fraction=.1, recorded_mpp_xy=None,
                        source_kind="real"):
    """Outcome-blind row-major engineering subset; real extraction is Slurm-only."""
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("PANDA WSI processing requires an authorized Slurm job")
    require_image_runtime()
    if (not np.isfinite(field_um) or not 0 < field_um <= 2000 or
            type(pixels) is not int or not 16 <= pixels <= 1024 or
            type(max_tiles) is not int or not 1 <= max_tiles <= 128 or
            type(max_candidates) is not int or not max_tiles <= max_candidates <= 20000 or
            not np.isfinite(min_tissue_fraction) or not 0 < min_tissue_fraction <= 1 or
            source_kind not in {"fixture", "real"}):
        raise ValueError("Invalid/unbounded PANDA extraction settings")
    output = Path(output)
    if output.exists():
        raise FileExistsError("Choose a fresh output directory; previous results are preserved")
    item = panda_input(root, image_id)
    rows, examined = [], 0
    with panda_readers(item["image_path"], item["mask_path"], recorded_mpp_xy) as (image, mask, provenance):
        mpp = np.array(provenance["measured_mpp_xy"])
        footprint = np.rint(field_um / mpp).astype(int)
        if np.any(footprint < 1) or np.prod(footprint) > 4_000_000:
            raise ValueError("Native mask/tile footprint exceeds bounded pixel budget")
        field = footprint * mpp
        grid = np.array(image.dimensions) // footprint
        total = int(np.prod(grid))
        if total == 0:
            raise ValueError("No complete in-bounds tile footprints")
        desired_downsample = float(min(footprint) / pixels)
        image_level = max(i for i, factor in enumerate(image.level_downsamples)
                          if factor <= max(1., desired_downsample))
        output.mkdir(parents=True, mode=0o700, exist_ok=False)
        for candidate in range(min(total, max_candidates)):
            examined += 1
            cell = np.array([candidate % grid[0], candidate // grid[0]], dtype=int)
            origin = cell * footprint
            preview = np.asarray(_rgb_region(image, origin, footprint, image.level_count - 1, 16))
            tissue_fraction = float(((preview.min(axis=2) < 220) & (np.ptp(preview, axis=2) > 10)).mean())
            if tissue_fraction < min_tissue_fraction:
                continue
            tile_id = f"{image_id}-x{cell[0]}-y{cell[1]}"
            tile = _rgb_region(image, origin, footprint, image_level, pixels)
            tile.save(output / (tile_id + ".png"))
            fractions = {name + "_fraction": None for name in LABELS}
            if mask is not None:
                # Native-resolution reads are only one small tile; labels are never interpolated.
                fractions = label_fractions(mask.read_region(tuple(origin), 0, tuple(footprint)))
            row = {"tile_id": tile_id, "path": tile_id + ".png", "image_id": image_id,
                   "x": float(origin[0] * mpp[0]), "y": float(origin[1] * mpp[1]),
                   "x_level0": int(origin[0]), "y_level0": int(origin[1]),
                   "grid_x": int(cell[0]), "grid_y": int(cell[1]),
                   "area_mm2": float(np.prod(field) / 1e6), "tissue_fraction": tissue_fraction,
                   "mask_available": mask is not None, **fractions}
            rows.append(row)
            if len(rows) == max_tiles:
                break
        metadata = {"slide_id": image_id, "image_id": image_id, "patient_id": "unknown",
            "patient_id_known": False, "project": "PANDA", "organ": "prostate", "source_kind": source_kind,
            "split": "dev", "split_provenance": "engineering smoke only; no patient-separated evaluation",
            "data_provider": item["provider"], "isup_grade": item["isup_grade"], "gleason_score": item["gleason_score"],
            "label_scope": "ISUP/Gleason score are slide-level only; tile fractions come only from masks",
            "coordinate_units": "microns", "coordinate_reference": "tile_top_left",
            "microns_per_unit": 1, "tile_step": field.tolist(), "tile_size": field.tolist(),
            "requested_field_um": field_um, "realized_field_um_xy": field.tolist(),
            "measured_mpp_xy": mpp.tolist(),
            "footprint_level0_pixels_xy": footprint.tolist(), "export_pixels": pixels,
            "panda": provenance, "train_csv_sha256": item["train_csv_sha256"], "pilot_csv_sha256": item["pilot_csv_sha256"],
            "extraction": {"image_level": image_level, "preview_level": image.level_count - 1,
                "mask_level": 0 if mask is not None else None, "max_tiles": max_tiles,
                "max_candidates": max_candidates, "candidates_examined": examined, "total_grid_cells": total,
                "min_tissue_fraction": min_tissue_fraction, "selection": "row-major RGB tissue screen; no mask/grade enrichment",
                "subset_only": examined < total, "complete_piece_topology_verified": False,
                "partial_edge_tiles_excluded": True, "tile_labels_csv": "tiles.csv"},
            "runtime": {name: importlib.metadata.version(name) for name in ("Pillow", "openslide-python", "tifffile")}}
        write_json(output / "metadata.json", metadata)
        if not rows:
            raise ValueError("No tissue tiles within candidate bound; metadata saved, no embeddings attempted")
        with (output / "tiles.csv").open("x", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return {"tiles": len(rows), "metadata": metadata}
