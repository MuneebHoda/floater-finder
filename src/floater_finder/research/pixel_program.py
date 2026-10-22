"""New, source-separated pixel benchmark. Does not change the frozen 96-image study.

CPU preparation measures eligibility and deduplicates actual RGB pixels. It never
loads a predictor or infers missing tissue, physical scale, or patient identity.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import time

import numpy as np
from PIL import Image

from ..artifacts import write_json
from ..experiments import file_sha256
from ..panda import panda_readers, _rgb_region, LABELS, label_fractions
from .pixel_study import crop_fractions, eligible, drift_gate

SIDES = (11, 16, 22, 50, 71)
PLACEMENTS = (("nw", .2, .2, "tissue"), ("ne", .8, .2, "tissue"),
              ("sw", .2, .8, "tissue"), ("se", .8, .8, "boundary"),
              ("detached", .5, .5, "background"))
VARIANTS = ("foreign", "native_sham", "seam_only", "unchanged", "identity")


def ordered(value):
    return hashlib.sha256(("20261021/pixel-program-v1/"+value).encode()).hexdigest()


def csv_rows(path):
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def make_pairs(sources):
    """Outcome-blind deterministic schedule, with all grade directions in fit."""
    result = []
    for split, count in (("fit", 24), ("calibration", 8), ("validation", 8)):
        groups = [[r for r in sources if r["program_role"] == "benchmark" and
                   r["program_split"] == split and int(r["isup_grade"]) in grades]
                  for grades in ((0,), (1,), (4, 5))]
        used = set(); seen = set()
        for i in range(count):
            hg, dg = divmod(i % 9, 3)
            options = [(h, d) for h in groups[hg] for d in groups[dg]
                       if h["image_id"] != d["image_id"] and
                       (h["image_id"], d["image_id"]) not in used]
            if not options:
                raise ValueError("Insufficient distinct sources for frozen pair schedule")
            options.sort(key=lambda p: (-(int(p[0]["image_id"] not in seen)+int(p[1]["image_id"] not in seen)),
                                         ordered(split+"/"+p[0]["image_id"]+"/"+p[1]["image_id"])))
            h, d = options[0]; hid, did = h["image_id"], d["image_id"]
            result.append(dict(pair_id=f"{split}-{i:02d}", split=split, host=hid, donor=did,
                               host_grade=int(h["isup_grade"]), donor_grade=int(d["isup_grade"])))
            used.add((hid, did)); seen.update((hid, did))
        expected = {r["image_id"] for g in groups for r in g}
        if seen != expected:
            raise ValueError("Pair schedule failed complete selected-source coverage")
    return result


def validate_sources(sources, excluded):
    if len(sources) != 57 or len({r["image_id"] for r in sources}) != 57:
        raise ValueError("Exactly 57 unique selected sources required")
    patients = {}
    for r in sources:
        if (r["source_split"] != "train" or r["data_provider"] != "radboud" or
                r["image_id"] in excluded or int(r["isup_grade"]) not in (0, 1, 4, 5)):
            raise ValueError("Original calibration/test, pilot or unsupported source")
        if r["patient_id_known"].lower() == "true":
            key = (r["program_role"], r["program_split"])
            if not r["patient_id"] or patients.setdefault(r["patient_id"], key) != key:
                raise ValueError("Known patient crosses source groups")
    for role, counts in (("benchmark", (9, 3, 3)), ("dense", (2, 1, 1))):
        for split, count in zip(("fit", "calibration", "validation"), counts):
            for grades in ((0,), (1,), (4, 5)):
                if sum(r["program_role"] == role and r["program_split"] == split and
                       int(r["isup_grade"]) in grades for r in sources) != count:
                    raise ValueError("Frozen role/split/grade counts differ")


def tissue(rgb):
    # A recorded RGB proxy, not a segmentation ground truth.
    a = np.asarray(rgb, dtype=np.int16)
    return (a.mean(axis=2) < 235) & ((a.max(axis=2)-a.min(axis=2)) > 12)


def largest_piece(binary):
    """Actual 4-connected RGB occupancy; no gap bridging or invented boundaries."""
    a = np.asarray(binary, bool); seen = np.zeros_like(a); best = []
    for y, x in zip(*np.where(a)):
        if seen[y, x]:
            continue
        stack = [(y, x)]; seen[y, x] = True; cells = []
        while stack:
            yy, xx = stack.pop(); cells.append((yy, xx))
            for ny, nx in ((yy-1, xx), (yy+1, xx), (yy, xx-1), (yy, xx+1)):
                if 0 <= ny < a.shape[0] and 0 <= nx < a.shape[1] and a[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; stack.append((ny, nx))
        if len(cells) > len(best):
            best = cells
    out = np.zeros_like(a)
    for y, x in best:
        out[y, x] = True
    return out


def destination(side, placement):
    _, x, y, _ = placement
    left, top = round(x*224)-side//2, round(y*224)-side//2
    return [left, top, left+side, top+side]


def context_ok(rgb, labels, box, kind):
    x0, y0, x1, y1 = box
    if not 2 <= x0 < x1 <= 222 or not 2 <= y0 < y1 <= 222:
        return False
    f = crop_fractions(labels, box); occupied = 1-f["background_fraction"]
    t = tissue(rgb)[y0:y1, x0:x1].mean()
    if kind == "background":
        # Check footprint AND an isolation ring, both RGB and native annotation.
        margin = [x0-2, y0-2, x1+2, y1+2]
        return (crop_fractions(labels, margin)["background_fraction"] == 1 and
                bool(np.all(np.asarray(rgb)[y0-2:y1+2, x0-2:x1+2] >= 240)))
    return (occupied >= .25 and t >= .25) if kind == "tissue" else (.1 <= occupied <= .9 and .1 <= t <= .9)


def composite_group(host, donor, native, box, support):
    """Matched geometry; seam-only changes a one-pixel inner boundary band.

    The seam control matches a scalar contrast, not complete seam morphology.
    The native sham shares the *foreign* support, avoiding silhouette mismatch.
    """
    host = np.asarray(host, np.uint8); donor = np.asarray(donor, np.uint8); native = np.asarray(native, np.uint8)
    x0, y0, x1, y1 = box; shape = (y1-y0, x1-x0)
    if host.shape != (224, 224, 3) or donor.shape != (*shape, 3) or native.shape != donor.shape or support.shape != shape or not support.any():
        raise ValueError("Aligned nonempty bounded RGB composition required")
    footprint = np.zeros((224, 224), bool); footprint[y0:y1, x0:x1] = support
    eroded = support.copy()
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        shifted = np.zeros_like(support)
        sy = slice(max(0, -dy), min(shape[0], shape[0]-dy)); sx = slice(max(0, -dx), min(shape[1], shape[1]-dx))
        shifted[slice(max(0, dy), min(shape[0], shape[0]+dy)), slice(max(0, dx), min(shape[1], shape[1]+dx))] = support[sy, sx]
        eroded &= shifted
    band = support & ~eroded
    target = host[y0:y1, x0:x1]
    contrast = float(np.abs(donor.astype(float)-target)[band].mean())
    seam = np.clip(target.astype(float)+contrast, 0, 255).round().astype(np.uint8)
    images = {}
    for name in VARIANTS:
        image = host.copy(); region = image[y0:y1, x0:x1]
        if name in ("foreign", "native_sham"):
            region[support] = (donor if name == "foreign" else native)[support]
        elif name == "seam_only":
            region[band] = seam[band]
        elif name == "identity":
            region[support] = target[support]
        images[name] = image
    if any(not np.array_equal(images[v], host) for v in ("unchanged", "identity")):
        raise RuntimeError("Identity/null gate failed")
    if np.array_equal(images["native_sham"], host) or np.array_equal(images["foreign"], host):
        raise ValueError("Degenerate edit: exclude the entire matched group")
    realized = float(np.abs(seam.astype(float)-target)[band].mean())
    return images, footprint, dict(requested_boundary_mean_absolute_contrast=contrast,
                                   realized_seam_control_contrast=realized,
                                   seam_contrast_absolute_error=abs(realized-contrast),
                                   seam_clipped_channel_fraction=float(((target.astype(float)+contrast)[band] > 255).mean()))


def store_rgb(root, pixels, split, index):
    """Global RGB deduplication; a cross-fold pixel collision blocks inference."""
    digest = hashlib.sha256(pixels.tobytes()).hexdigest()
    if digest in index and index[digest]["split"] != split:
        raise ValueError("Identical pixels cross source folds; stop, do not silently deduplicate leakage")
    if digest not in index:
        path = root/"images"/(digest+".png")
        Image.fromarray(pixels).save(path, compress_level=1)
        index[digest] = dict(pixel_sha256=digest, path=str(path), sha256=file_sha256(path), split=split)
    return digest


def load_config(project, config_path, expected_sha):
    project = Path(project)
    if file_sha256(config_path) != expected_sha:
        raise ValueError("Frozen program configuration changed")
    c = json.loads(Path(config_path).read_text())
    for name, digest in c["source_files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts or file_sha256(project/name) != digest:
            raise ValueError("Frozen source differs: "+name)
    sources = csv_rows(project/c["sources_csv"])
    if file_sha256(project/c["sources_csv"]) != c["sources_sha256"]:
        raise ValueError("Selected source manifest changed")
    validate_sources(sources, set(c["excluded_pilot_ids"]))
    if c["pairs"] != make_pairs(sources) or c["target_records"] != 10000 or c["sides_pixels"] != list(SIDES):
        raise ValueError("Frozen pair schedule or intervention geometry differs")
    return c, sources


def _source(c, r, output):
    """Read at most 64 old unbiased exports, plus their bounded native regions."""
    sid = r["image_id"]; directory = Path(r["tile_manifest_path"]).parent
    meta = json.loads(Path(r["tile_metadata_path"]).read_text())
    receipt_path = Path(c["encoded_root"])/sid/"completion.json"
    if file_sha256(receipt_path) != c["verified_receipts"][sid]:
        raise ValueError("Original verified embedding receipt differs")
    receipt = json.loads(receipt_path.read_text()); identity = receipt["input_identity"]
    if (meta["slide_id"] != sid or meta["source_kind"] != "real" or meta["cohort_split"] != "train" or
            meta["extraction"]["sampling_mode"] != "representative" or meta["extraction"]["selection_uses_mask"] or
            meta["export_pixels"] != 224 or
            file_sha256(directory/"tiles.csv") != identity["manifest_sha256"] or
            file_sha256(directory/"metadata.json") != identity["metadata_sha256"] or
            identity["checkpoint_sha256"] != c["checkpoint_sha256"]):
        raise ValueError("Original unbiased source provenance differs")
    for role in ("image", "mask"):
        if file_sha256(r[role+"_path"]) != r[role+"_sha256"]:
            raise ValueError("Real TIFF hash differs")
    kind = "benign" if int(r["isup_grade"]) == 0 else "gp3" if int(r["isup_grade"]) == 1 else "gp45"
    sampled = csv_rows(directory/"tiles.csv")
    sampled.sort(key=lambda row: ordered(sid+"/"+row["tile_id"]))
    hosts = {}; crops = []; inspected = 0
    with panda_readers(r["image_path"], r["mask_path"], meta["measured_mpp_xy"]) as (image, mask, provenance):
        if r["program_role"] == "benchmark":
            for row in sampled[:64]:
                inspected += 1; origin = (int(row["x_level0"]), int(row["y_level0"]))
                footprint = tuple(meta["footprint_level0_pixels_xy"])
                rgba = mask.read_region(origin, 0, footprint); labels = np.asarray(rgba)[:, :, 0]
                fractions = label_fractions(rgba)
                if any(not math.isclose(fractions[n+"_fraction"], float(row[n+"_fraction"]), abs_tol=1e-12) for n in LABELS):
                    raise ValueError("Native mask differs from saved tile labels")
                path = directory/row["path"]
                if file_sha256(path) != identity["png_sha256"][row["tile_id"]]:
                    raise ValueError("Existing tile PNG hash differs")
                with Image.open(path) as im:
                    rgb = np.array(im.convert("RGB"))
                if not np.array_equal(rgb, np.asarray(_rgb_region(image, origin, footprint, meta["extraction"]["image_level"], 224))):
                    raise ValueError("Saved PNG differs from canonical WSI region")
                source = dict(slide_id=sid, tile_id=row["tile_id"], path=str(path), sha256=file_sha256(path),
                              origin_level0_xy=list(origin), tile_size_um_xy=meta["tile_size"],
                              measured_mpp_xy=meta["measured_mpp_xy"], footprint_level0_pixels_xy=list(footprint))
                if eligible(fractions, kind):
                    for placement in PLACEMENTS:
                        if placement[0] not in hosts and all(context_ok(rgb, labels, destination(s, placement), placement[3]) for s in SIDES):
                            hosts[placement[0]] = (rgb, labels, source)
                    if len(crops) < 2:
                        for x, y in ((112,112), (56,56), (168,56), (56,168), (168,168), (56,112), (168,112), (112,56), (112,168)):
                            boxes = [[x-s//2, y-s//2, x-s//2+s, y-s//2+s] for s in SIDES]
                            if all(eligible(crop_fractions(labels, b), kind) for b in boxes):
                                crops.append((rgb, labels, source, boxes)); break
                if len(crops) == 2 and len(hosts) == 5:
                    break
        facts = dict(image_id=sid, role=r["program_role"], split=r["program_split"],
                     source_image_sha256=r["image_sha256"], source_mask_sha256=r["mask_sha256"],
                     embedding_receipt_sha256=file_sha256(receipt_path),
                     physical_scale_and_alignment=provenance, candidates_inspected=inspected,
                     eligible_host_placements=sorted(hosts), eligible_crop_tiles=len(crops),
                     source_patient_independence_verified=False)
    write_json(output/"sources"/(sid+".json"), facts)
    return hosts, crops, meta


def prepare(project, config_path, config_sha, output):
    if not os.environ.get("SLURM_JOB_ID") or os.environ.get("SLURM_JOB_GPUS"):
        raise RuntimeError("Use a bounded CPU Slurm job")
    start = time.monotonic(); project = Path(project); c, sources = load_config(project, config_path, config_sha)
    output = Path(output)
    if str(output) != c["cpu_output"]:
        raise ValueError("Use exact versioned CPU output")
    output.mkdir(exist_ok=False)
    for name in ("images", "masks", "sources"):
        (output/name).mkdir()
    try:
        if file_sha256(c["checkpoint"]) != c["checkpoint_sha256"]:
            raise ValueError("Current checkpoint hash differs")
        if file_sha256(c["cohort_manifest"]["path"]) != c["cohort_manifest"]["sha256"]:
            raise ValueError("Original cohort manifest differs")
        original = {r["image_id"]: r for r in csv_rows(c["cohort_manifest"]["path"])}
        verification = c["original_embedding_verification"]
        if file_sha256(verification["path"]) != verification["sha256"]:
            raise ValueError("Original 120-slide verification report differs")
        c["verified_receipts"] = {r["image_id"]:r["completion_sha256"]
                                  for r in json.loads(Path(verification["path"]).read_text())["records"]}
        loaded = {}
        for r in sources:
            old = original[r["image_id"]]
            if old["split"] != "train" or any(old[k] != r[k] for k in ("image_path", "mask_path", "image_sha256", "mask_sha256", "data_provider", "isup_grade")):
                raise ValueError("Selected row disagrees with verified original training cohort")
            loaded[r["image_id"]] = _source(c, r, output)
        index = {}; exclusions = []; records = []; group_number = 0
        for pair in c["pairs"]:
            hosts, native_crops, hm = loaded[pair["host"]]
            _, donor_crops, dm = loaded[pair["donor"]]
            if any(hm[k] != dm[k] for k in ("tile_size", "measured_mpp_xy", "footprint_level0_pixels_xy", "export_pixels")):
                raise ValueError("No unrecorded host/donor physical rescaling allowed")
            for j, side in enumerate(SIDES):
                for placement in PLACEMENTS:
                    for shape in ("rectangle", "irregular"):
                        group_number += 1; gid = f"group-{group_number:04d}"
                        context = dict(group_id=gid, pair_id=pair["pair_id"], side_pixels=side, placement=placement[0], shape=shape)
                        if placement[0] not in hosts or not native_crops or not donor_crops:
                            exclusions.append(dict(**context, reason="No eligible bounded native/host/donor region")); continue
                        host, host_labels, hs = hosts[placement[0]]
                        choices = [v for v in native_crops if v[2]["tile_id"] != hs["tile_id"]]
                        if not choices:
                            exclusions.append(dict(**context, reason="No distinct native-sham tile")); continue
                        native_rgb, native_labels, ns, nb = choices[0]
                        donor_rgb, donor_labels, ds, db = donor_crops[0]
                        def patch(a, b):
                            return a[b[1]:b[3], b[0]:b[2]]
                        dp, npatch = patch(donor_rgb, db[j]), patch(native_rgb, nb[j])
                        support = np.ones((side, side), bool) if shape == "rectangle" else largest_piece(tissue(dp))
                        if support.sum() < max(4, round(side*side*.1)):
                            exclusions.append(dict(**context, reason="Insufficient measured irregular donor RGB tissue")); continue
                        box = destination(side, placement)
                        try:
                            images, footprint, seam = composite_group(host, dp, npatch, box, support)
                        except ValueError as exc:
                            exclusions.append(dict(**context, reason=str(exc))); continue
                        mask_path = output/"masks"/(gid+".npz")
                        changed = np.stack([np.any(images[v] != host, axis=2) for v in VARIANTS])
                        with mask_path.open("xb") as f:
                            np.savez_compressed(f, footprint=footprint, changed=changed,
                                                donor_rgb_tissue=support & tissue(dp), variants=np.array(VARIANTS))
                        shared = dict(**context, split=pair["split"], host=hs, donor=ds, native_sham=ns,
                            destination_box_xyxy=box, donor_box_xyxy=db[j], native_sham_box_xyxy=nb[j],
                            host_native_fractions=crop_fractions(host_labels, box),
                            donor_native_fractions=crop_fractions(donor_labels, db[j]),
                            sham_native_fractions=crop_fractions(native_labels, nb[j]),
                            requested_square_area_fraction=side**2/224**2,
                            realized_source_footprint_fraction=float(footprint.mean()),
                            source_footprint_area_mm2=float(footprint.mean()*math.prod(hm["tile_size"])/1e6),
                            masks_path=str(mask_path), masks_sha256=file_sha256(mask_path), seam_control=seam)
                        for number, variant in enumerate(VARIANTS):
                            pixel_hash = store_rgb(output, images[variant], pair["split"], index)
                            records.append(dict(**shared, record_id=gid+"-"+variant, variant=variant,
                                pixel_sha256=pixel_hash, changed_pixel_fraction=float(changed[number].mean()),
                                foreign_mask_is_footprint=variant == "foreign"))
        if group_number*5 != 10000 or len(records)+5*len(exclusions) != 10000:
            raise RuntimeError("Candidate and exclusion denominators differ")
        with (output/"records.jsonl").open("x") as f:
            for r in records:
                f.write(json.dumps(r, allow_nan=False)+"\n")
        write_json(output/"exclusions.json", exclusions)
        write_json(output/"unique_images.json", sorted(index.values(), key=lambda r:(r["split"], r["pixel_sha256"])))
        actual_bytes = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
        if actual_bytes > 4*1024**3:
            raise RuntimeError("CPU preparation exceeds four-GiB storage ceiling")
        foreign = [r for r in records if r["variant"] == "foreign"]
        coverage = {split:dict(
            hosts=len({r["host"]["slide_id"] for r in foreign if r["split"] == split}),
            donors=len({r["donor"]["slide_id"] for r in foreign if r["split"] == split}),
            matched_groups=sum(r["split"] == split for r in foreign),
            shapes=sorted({r["shape"] for r in foreign if r["split"] == split}),
            placements=sorted({r["placement"] for r in foreign if r["split"] == split}),
            side_pixels=sorted({r["side_pixels"] for r in foreign if r["split"] == split}))
            for split in ("fit", "calibration", "validation")}
        ready = len(records) >= 8000 and all(
            v["hosts"] >= 3 and v["donors"] >= 3 and v["shapes"] == ["irregular", "rectangle"] and
            len(v["placements"]) == 5 and v["side_pixels"] == list(SIDES) for v in coverage.values())
        summary = dict(schema_version=1, source_kind="real", protocol_sha256=config_sha,
            target_records=10000, generated_records=len(records), excluded_records=5*len(exclusions),
            matched_groups=len(records)//5, exact_unique_images_requiring_inference=len(index),
            unique_images_by_split={s:sum(v["split"] == s for v in index.values()) for s in ("fit", "calibration", "validation")},
            sources_checked=57, benchmark_sources=45, dense_sources=12, bytes_written=actual_bytes,
            cpu_wall_seconds=time.monotonic()-start, slurm_job_id=os.environ["SLURM_JOB_ID"],
            checkpoint_current_sha256=c["checkpoint_sha256"],
            records_sha256=file_sha256(output/"records.jsonl"), unique_images_sha256=file_sha256(output/"unique_images.json"),
            exclusions_sha256=file_sha256(output/"exclusions.json"),
            source_facts_sha256={p.name:file_sha256(p) for p in sorted((output/"sources").iterdir())},
            actual_coverage=coverage, cpu_feasibility_gate_passed=ready,
            inference_executed=False, original_final_test_accessed=False, independent_patients_verified=False,
            gpu_go=False, gpu_go_reason="Review exclusions, dedup counts, source/style coverage, CPU costs; freeze exact profile scope and obtain explicit GPU approval")
        write_json(output/"completion.json", summary)
        return summary
    except BaseException as exc:
        write_json(output/"failure.json", dict(error=type(exc).__name__, message=str(exc), partial_outputs_preserved=True))
        raise


def encode(project, config_path, config_sha, preparation_sha, output, split, offset, limit):
    """Explicit ranges only; no sbatch submission, threshold fitting or scoring."""
    if not os.environ.get("SLURM_JOB_ID") or not os.environ.get("SLURM_JOB_GPUS"):
        raise RuntimeError("Explicitly authorized one-GPU Slurm job required")
    c, _ = load_config(project, config_path, config_sha); prep = Path(c["cpu_output"])
    if file_sha256(prep/"completion.json") != preparation_sha:
        raise ValueError("Exact CPU completion hash required before a GPU range can be frozen")
    receipt = json.loads((prep/"completion.json").read_text())
    if not receipt["cpu_feasibility_gate_passed"]:
        raise ValueError("CPU feasibility gate failed; freeze a new reviewed scope before inference")
    if (receipt["protocol_sha256"] != config_sha or
            file_sha256(prep/"unique_images.json") != receipt["unique_images_sha256"] or
            file_sha256(prep/"records.jsonl") != receipt["records_sha256"]):
        raise ValueError("Prepared manifest differs")
    images = [r for r in json.loads((prep/"unique_images.json").read_text()) if r["split"] == split]
    if not (0 <= offset < len(images) and 0 < limit <= 8192 and offset+limit <= len(images)):
        raise ValueError("Exact nonempty in-bounds deduplicated inference range required")
    selected = images[offset:offset+limit]
    for r in selected:
        path = Path(r["path"])
        if not path.resolve().is_relative_to(prep.resolve()) or file_sha256(path) != r["sha256"]:
            raise ValueError("Prepared image path/hash differs")
        with Image.open(path) as image:
            pixels = np.array(image.convert("RGB"))
        if pixels.shape != (224,224,3) or hashlib.sha256(pixels.tobytes()).hexdigest() != r["pixel_sha256"]:
            raise ValueError("Actual RGB identity differs")
    import torch
    from ..conch import ConchEncoder
    from ..artifacts import Slide
    if torch.cuda.device_count() != 1 or file_sha256(c["checkpoint"]) != c["checkpoint_sha256"]:
        raise ValueError("One GPU and current checkpoint hash required")
    output = Path(output); output.mkdir(exist_ok=False)
    torch.set_num_threads(4); torch.manual_seed(0)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    encoder = ConchEncoder(c["checkpoint"])
    if encoder.provenance != c["embedding_model"]:
        raise ValueError("Canonical CONCH model/preprocessing/runtime differs")
    # Existing saved source anchors establish canonical re-encoding before new images.
    records = []
    with (prep/"records.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            if r["split"] == split and r["variant"] == "unchanged":
                records.append(r["host"])
    anchors = sorted({r["slide_id"]+"/"+r["tile_id"]:r for r in records}.values(), key=lambda r:(r["slide_id"],r["tile_id"]))[:8]
    old = []
    for r in anchors:
        if file_sha256(r["path"]) != r["sha256"]:
            raise ValueError("Anchor PNG differs")
        slide = Slide.load(Path(c["encoded_root"])/r["slide_id"]/"slide.npz")
        if slide.metadata["model"] != c["embedding_model"]:
            raise ValueError("Saved anchor model differs")
        old.append(slide.feats[list(slide.tile_ids).index(r["tile_id"])])
    if not anchors:
        raise ValueError("No unchanged source anchors")
    new, anchor_seconds = encoder.images([r["path"] for r in anchors],16)
    gate = drift_gate(np.array(old),new,**c["drift_tolerances"])
    write_json(output/"anchor_drift.json",gate)
    if not gate["passed"]:
        raise RuntimeError("Anchor drift gate failed before composite inference")
    feats, seconds = encoder.images([r["path"] for r in selected],16)
    if feats.shape != (limit,512) or not np.isfinite(feats).all() or not np.allclose(np.linalg.norm(feats,axis=1),1,atol=1e-4):
        raise ValueError("CONCH feature contract failed")
    with (output/"embeddings.npz").open("xb") as f:
        np.savez_compressed(f, feats=feats, pixel_sha256=np.array([r["pixel_sha256"] for r in selected]))
    result = dict(images=limit, split=split, offset=offset, encoder=encoder.provenance,
        protocol_sha256=config_sha, preparation_sha256=preparation_sha,
        anchor_encoding_seconds=anchor_seconds, encoding_seconds=seconds,
        features_sha256=file_sha256(output/"embeddings.npz"), slurm_job_id=os.environ["SLURM_JOB_ID"],
        no_predictions_run=True)
    write_json(output/"completion.json", result)
    return result
