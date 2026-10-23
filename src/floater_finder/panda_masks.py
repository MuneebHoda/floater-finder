"""Streaming, native-resolution Radboud mask audit; never an image-plane load."""

import os
import numpy as np
from PIL import Image

from .panda import LABELS, _rgb_region


def audit_mask(mask, mpp_xy, block=512):
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Full-mask processing requires Slurm")
    if type(block) is not int or not 16 <= block <= 1024:
        raise ValueError("Mask block must be between 16 and 1024 pixels")
    mpp = np.asarray(mpp_xy, dtype=float)
    if mpp.shape != (2,) or not np.isfinite(mpp).all() or min(mpp) <= 0:
        raise ValueError("Measured X/Y physical scale required")
    counts = np.zeros(6, dtype=np.int64)
    width, height = mask.dimensions
    bbox = None
    for y in range(0, height, block):
        for x in range(0, width, block):
            region = np.asarray(mask.read_region((x, y), 0, (min(block, width-x), min(block, height-y))))
            labels = region[:, :, 0]
            if not np.isin(labels, range(6)).all() or not np.all(region[:, :, 3] == 255):
                raise ValueError("Invalid/out-of-bounds native mask labels")
            counts += np.bincount(labels.ravel(), minlength=6)
            yy, xx = np.nonzero(labels >= 4)
            if len(xx):
                bounds = [x+int(xx.min()), y+int(yy.min()), x+int(xx.max())+1, y+int(yy.max())+1]
                bbox = bounds if bbox is None else [min(bbox[0], bounds[0]), min(bbox[1], bounds[1]),
                    max(bbox[2], bounds[2]), max(bbox[3], bounds[3])]
    assert int(counts.sum()) == width * height
    pixel_mm2 = float(np.prod(mpp) / 1e6)
    return {"resolution_level": 0, "block_pixels": block, "dimensions": [width, height],
        "native_pixel_counts": dict(zip(LABELS, map(int, counts))),
        "area_mm2": dict(zip(LABELS, (counts * pixel_mm2).tolist())),
        "gp45_positive": bool(counts[4] + counts[5]), "gp45_bbox_level0_xyxy": bbox,
        "annotation_fraction_of_slide": float(counts[3:].sum() / counts.sum()),
        "gp45_fraction_of_annotated_tissue": float(counts[4:].sum() / counts[1:].sum()) if counts[1:].sum() else None,
        "area_provenance": "exact native channel-0 counts multiplied by measured TIFF X/Y MPP"}


def save_mask_overlay(image, mask, output, size=768):
    """Context image only; downsampled labels are never used for area estimates."""
    rgb = _rgb_region(image, (0, 0), image.dimensions, image.level_count - 1, size)
    labels = np.asarray(mask.read_region((0, 0), mask.level_count-1,
                       mask.level_dimensions[-1]))[:, :, 0]
    labels = np.asarray(Image.fromarray(labels).resize(rgb.size, Image.Resampling.NEAREST))
    colors = np.asarray(rgb).copy()
    for label, color in ((3, [255, 220, 0]), (4, [255, 0, 0]), (5, [0, 100, 255])):
        colors[labels == label] = color
    Image.blend(rgb, Image.fromarray(colors), .45).save(output)
