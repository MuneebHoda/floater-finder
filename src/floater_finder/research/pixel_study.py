"""Four-pair, training-only pixel feasibility study; historical artifacts stay immutable."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image

from ..artifacts import Slide, TextEmbeddings, normalize, write_json
from ..experiments import file_sha256
from ..panda import panda_readers, _rgb_region, label_fractions, LABELS
from ..panda_encoding import encoding_contract, validate_saved
from ..predictors import load_predictor
from .pixel_controls import prepare

DOSES = (1, 5, 10)
SIDES = (22, 50, 71)
PLACEMENTS = (("upper_left", .125, .125), ("lower_right", .55, .55))
ROLES = ("host", "donor", "native_sham")


def rows(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def checked_json(entry):
    if file_sha256(entry["path"]) != entry["sha256"]:
        raise ValueError("Frozen input checksum differs: " + str(entry["path"]))
    return json.loads(Path(entry["path"]).read_text())


def preflight(config_path, digest, project, check_inputs=False):
    if file_sha256(config_path) != digest:
        raise ValueError("Frozen pixel-study protocol changed")
    c = json.loads(Path(config_path).read_text()); project = Path(project)
    if (c["experiment_id"] != "panda_pixel_contamination_v1" or c["schema_version"] != 1 or
            c["split"] != "train" or len(c["pairs"]) != 4 or c["maximum_images"] != 96 or
            c["doses_percent"] != list(DOSES) or c["patch_sides_pixels"] != list(SIDES) or
            len({p["id"] for p in c["pairs"]}) != 4 or
            len({p[r] for p in c["pairs"] for r in ("host", "donor")}) != 8 or
            [p["task"] for p in c["pairs"]] != ["s1", "s1", "s2", "s2"]):
        raise ValueError("Exactly four distinct predetermined training pairs and 96 images required")
    required = {"src/floater_finder/research/pixel_study.py", "src/floater_finder/research/pixel_controls.py",
        "src/floater_finder/conch.py", "src/floater_finder/panda.py", "src/floater_finder/panda_encoding.py",
        "scripts/panda_pixel_study.py", "scripts/slurm/panda_pixel_prepare.sbatch", "scripts/slurm/panda_pixel_encode.sbatch"}
    if not required.issubset(c["source_files"]): raise ValueError("Incomplete source freeze")
    for name, expected in c["source_files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts or file_sha256(project/name) != expected:
            raise ValueError("Frozen pixel-study source differs: " + name)
    for model in c["models"]:
        for name, expected in model["sha256"].items():
            if file_sha256(project/model["directory"]/name) != expected:
                raise ValueError("Frozen predictor differs")
    if check_inputs:
        for entry in c["inputs"].values():
            if file_sha256(entry["path"]) != entry["sha256"]:
                raise ValueError("Frozen pixel-study input differs")
        cohort = {r["image_id"]: r for r in rows(c["inputs"]["manifest"]["path"])}
        for pair in c["pairs"]:
            for role in ("host", "donor"):
                r = cohort[pair[role]]
                grades = (0,) if pair["task"] == "s1" and role == "host" else (1,) if role == "host" else (4, 5)
                if r["split"] != "train" or r["data_provider"] != "radboud" or int(r["isup_grade"]) not in grades or r["mask_usable"] != "True":
                    raise ValueError("Only predetermined masked Radboud training sources allowed")
        if file_sha256(project/"configs/panda_morphology_v1.yaml") != c["prompts_sha256"]:
            raise ValueError("Canonical morphology prompts differ")
    return c


def crop_fractions(native_labels, box, export_pixels=224):
    """Exact native-label area overlap with a crop in the exported RGB pixel grid."""
    a = np.asarray(native_labels)
    if (a.ndim != 2 or min(a.shape) < 1 or not np.isin(a, range(6)).all() or
            len(box) != 4 or any(type(v) is not int for v in box) or
            not 0 <= box[0] < box[2] <= export_pixels or not 0 <= box[1] < box[3] <= export_pixels):
        raise ValueError("Valid native Radboud labels and in-bounds crop required")
    left, top, right, bottom = np.array(box)*np.array([a.shape[1], a.shape[0]]*2)/export_pixels
    wx = np.maximum(0, np.minimum(np.arange(a.shape[1])+1, right)-np.maximum(np.arange(a.shape[1]), left))
    wy = np.maximum(0, np.minimum(np.arange(a.shape[0])+1, bottom)-np.maximum(np.arange(a.shape[0]), top))
    weights = wy[:, None]*wx[None, :]
    return {name+"_fraction": float(weights[a == i].sum()/weights.sum()) for i, name in enumerate(LABELS)}


def eligible(fractions, kind):
    cancer = sum(fractions[f"gleason{g}_fraction"] for g in (3, 4, 5))
    relevant = cancer if kind == "cancer" else fractions["gleason4_fraction"]+fractions["gleason5_fraction"] if kind == "gp45" else fractions["gleason3_fraction"] if kind == "gp3" else fractions["benign_fraction"]
    return (relevant >= .1 and fractions["background_fraction"] <= .5 and
            (kind != "benign" or cancer == 0) and
            (kind != "gp3" or fractions["gleason4_fraction"]+fractions["gleason5_fraction"] == 0))


def choose_crop(labels, kind):
    # Fixed anchor order, no pixels/features/predictions used to select the crop.
    for x, y in ((112,112),(56,56),(56,112),(56,168),(112,56),(112,168),(168,56),(168,112),(168,168)):
        boxes = [[x-s//2, y-s//2, x-s//2+s, y-s//2+s] for s in SIDES]
        fractions = [crop_fractions(labels, b) for b in boxes]
        if all(eligible(f, kind) for f in fractions):
            return boxes, fractions
    return None


def assert_scale(host, donor):
    for key in ("tile_size", "measured_mpp_xy", "footprint_level0_pixels_xy", "export_pixels"):
        if host[key] != donor[key]:
            raise ValueError("Host/donor physical scale differs; rescaling is not authorized")
    if host["export_pixels"] != 224:
        raise ValueError("Canonical 224-pixel PANDA exports required")


def verify_composites(folder, manifest):
    """Verify all raster controls independently of the compositor's recorded fractions."""
    folder = Path(folder); parents = {p["pair_id"]: p["parents"] for p in manifest["parents"]}
    groups = {}; byte_count = 0
    for r in manifest["records"]:
        groups.setdefault((r["pair_id"], r["placement_id"]), []).append(r)
        parent = parents[r["pair_id"]]
        with Image.open(parent["host"]["path"]) as im: host = np.array(im.convert("RGB"))
        loaded = {}
        for kind, entry in r["files"].items():
            path = folder/entry["path"]
            if path.resolve().parent != folder.resolve() or file_sha256(path) != entry["sha256"]:
                raise ValueError("Composite output checksum/path differs")
            byte_count += path.stat().st_size
            with Image.open(path) as im: loaded[kind] = np.array(im)
        target = np.zeros(host.shape[:2], bool); x0,y0,x1,y1 = r["destination_box_xyxy"]; target[y0:y1,x0:x1] = True
        actual = np.any(loaded["image"] != host, axis=2)
        if (not np.array_equal(loaded["target_mask"] > 0, target) or
                not np.array_equal(loaded["changed_mask"] > 0, actual) or
                not np.array_equal(loaded["foreign_mask"] > 0, target if r["variant"] == "foreign_patch" else np.zeros_like(target)) or
                np.any(actual & ~target) or not math.isclose(r["realized_area_fraction"], target.mean()) or
                not math.isclose(r["changed_pixel_fraction"], actual.mean())):
            raise ValueError("Composite masks, changed pixels or geometry differ")
        if r["variant"] in ("unchanged", "cut_reinsert_null"):
            if not np.array_equal(loaded["image"], host): raise ValueError("Null control changed pixels")
        else:
            role = "donor" if r["variant"] == "foreign_patch" else "native_sham"
            box = parent[role]["crop_box"]
            if (box[2]-box[0],box[3]-box[1]) != (x1-x0,y1-y0):
                raise ValueError("Unexpected patch rescaling")
            with Image.open(parent[role]["path"]) as im: patch = np.array(im.convert("RGB").crop(box))
            if not np.array_equal(loaded["image"][y0:y1,x0:x1],patch):
                raise ValueError("Same-size patch pixels differ")
    for group in groups.values():
        if len(group) != 4 or {r["variant"] for r in group} != {"foreign_patch","native_sham","unchanged","cut_reinsert_null"}:
            raise ValueError("Four matched controls required")
        if len({tuple(r["destination_box_xyxy"]) for r in group}) != 1:
            raise ValueError("Matched controls have different geometry")
    return dict(images=len(manifest["records"]),matched_groups=len(groups),png_bytes=byte_count,
        nulls_pixel_identical=True,no_patch_rescaling=True,no_clipping=True,mask_semantics_verified=True)


def _load_source(c, sid, cohort, verified):
    root = Path(c["encoded_root"])/sid
    if file_sha256(root/"completion.json") != verified[sid]["completion_sha256"]:
        raise ValueError("Existing embedding receipt differs")
    completion = json.loads((root/"completion.json").read_text()); identity = completion["input_identity"]
    directory = Path(cohort[sid]["tile_manifest_path"]).parent
    for name, key in (("tiles.csv","manifest_sha256"),("metadata.json","metadata_sha256")):
        if file_sha256(directory/name) != identity[key]: raise ValueError("Source tiling metadata differs")
    tile_rows = rows(directory/"tiles.csv"); meta = json.loads((directory/"metadata.json").read_text())
    if (meta["cohort_split"] != "train" or meta["slide_id"] != sid or meta["source_kind"] != "real" or
            meta["extraction"]["sampling_mode"] != "representative" or meta["extraction"]["selection_uses_mask"]):
        raise ValueError("Only original unbiased training exports allowed")
    validate_saved(root,tile_rows,identity)
    if (Slide.load(root/"slide.npz").metadata["model"] != c["embedding_model"] or
            TextEmbeddings.load(root/"text.npz").fingerprint() != c["text_fingerprint"]):
        raise ValueError("Original model/text fingerprint differs")
    if (identity["checkpoint_sha256"] != c["checkpoint_sha256"] or identity["prompts_sha256"] != c["prompts_sha256"] or
            identity["encoding_contract"] != encoding_contract()):
        raise ValueError("Canonical encoding/runtime contract differs")
    return directory, tile_rows, meta, identity


def _select(c, sid, kind, source, cohort, output):
    directory,tile_rows,meta,identity = source
    preview = Path(c["preview_root"])/"checkpoints"/("slide-"+sid+".json")
    entry = json.loads(preview.read_text()); assets = entry["png_assets"]
    # Only reuse existing unchanged PNG gallery exports; labels are selection truth, not detector input.
    available = {Path(v["source_path"]).stem:(name,v) for name,v in assets.items()}
    candidates = [r for r in tile_rows if r["tile_id"] in available and
        eligible({n+"_fraction":float(r[n+"_fraction"]) for n in LABELS},kind)]
    candidates.sort(key=lambda r:hashlib.sha256((str(c["selection_seed"])+"/"+sid+"/"+r["tile_id"]).encode()).hexdigest())
    item = cohort[sid]
    for role in ("image","mask"):
        if file_sha256(item[role+"_path"]) != item[role+"_sha256"]:
            raise ValueError("Original TIFF checksum differs")
    with panda_readers(item["image_path"], item["mask_path"], meta["measured_mpp_xy"]) as (image,mask,provenance):
        footprint = tuple(meta["footprint_level0_pixels_xy"])
        for row in candidates[:64]:
            origin = (int(row["x_level0"]),int(row["y_level0"]))
            labels_rgba = mask.read_region(origin,0,footprint)
            fractions = label_fractions(labels_rgba)
            if any(not math.isclose(fractions[n+"_fraction"],float(row[n+"_fraction"]),abs_tol=1e-12) for n in LABELS):
                raise ValueError("Native mask fractions disagree with saved tile")
            labels = np.array(labels_rgba)[:,:,0]; crop = choose_crop(labels,kind)
            if crop is None: continue
            name, asset = available[row["tile_id"]]; path = Path(c["preview_root"])/name
            if file_sha256(path) != asset["sha256"] or asset["sha256"] != identity["png_sha256"][row["tile_id"]] or file_sha256(directory/row["path"]) != asset["sha256"]:
                raise ValueError("Verified PNG export differs from encoded source")
            with Image.open(path) as im: pixels = np.array(im.convert("RGB"))
            reread = np.array(_rgb_region(image,origin,footprint,meta["extraction"]["image_level"],224))
            if pixels.shape != (224,224,3) or not np.array_equal(pixels,reread):
                raise ValueError("PNG and bounded original WSI region differ")
            mask_name = sid+"__"+row["tile_id"]+"__native-labels.png"
            mask_path = output/"source_masks"/mask_name
            Image.fromarray(labels).save(mask_path)
            return dict(slide_id=sid,tile_id=row["tile_id"],path=str(path),sha256=asset["sha256"],
                tile_index=next(i for i,r in enumerate(tile_rows) if r["tile_id"] == row["tile_id"]),
                native_mask_path=str(mask_path),native_mask_sha256=file_sha256(mask_path),
                crop_boxes=crop[0],crop_native_fractions=crop[1],selection_kind=kind,
                tile_native_fractions=fractions,coordinates_um=[float(row["x"]),float(row["y"])],
                origin_level0_xy=list(origin),tile_size_um_xy=meta["tile_size"],export_pixel_um_xy=[v/224 for v in meta["tile_size"]],
                footprint_level0_pixels_xy=list(footprint),measured_mpp_xy=meta["measured_mpp_xy"],
                source_image_sha256=item["image_sha256"],source_mask_sha256=item["mask_sha256"],
                embedding_completion_sha256=verified_digest(c,sid),preview_checkpoint_sha256=file_sha256(preview),
                mask_alignment=provenance["alignment_check"],mask_channel=0,
                saved_slide_sha256=file_sha256(Path(c["encoded_root"])/sid/"slide.npz"))
    raise ValueError("Predetermined source has no eligible exported crop: "+sid+"/"+kind)


def verified_digest(c,sid):
    return file_sha256(Path(c["encoded_root"])/sid/"completion.json")


def prepare_real(config_path, digest, project, output, source_commit):
    if not os.environ.get("SLURM_JOB_ID") or os.environ.get("SLURM_JOB_GPUS"):
        raise RuntimeError("Pixel preparation requires bounded CPU Slurm execution")
    c = preflight(config_path,digest,project,True); output = Path(output)
    if str(output) != c["preparation_output"]: raise ValueError("Exact versioned preparation output required")
    output.mkdir(exist_ok=False); (output/"source_masks").mkdir()
    cohort = {r["image_id"]:r for r in rows(c["inputs"]["manifest"]["path"])}
    verified = {r["image_id"]:r for r in checked_json(c["inputs"]["verification"])["records"]}
    preview_summary = checked_json(c["inputs"]["preview_summary"])
    pairs = []; plans = []
    try:
        for pair in c["pairs"]:
            selected = {}; source = {}
            for role in ("host","donor"):
                sid = pair[role]; public = "reports/"+sid+".json"
                if file_sha256(Path(c["preview_root"])/public) != preview_summary["rendered_file_sha256"][public]:
                    raise ValueError("Original training preview changed")
                source[role] = _load_source(c,sid,cohort,verified)
            assert_scale(source["host"][2],source["donor"][2])
            kind = "benign" if pair["task"] == "s1" else "gp3"
            selected["host"] = _select(c,pair["host"],kind,source["host"],cohort,output)
            selected["native_sham"] = dict(selected["host"])
            selected["donor"] = _select(c,pair["donor"],"cancer" if pair["task"] == "s1" else "gp45",source["donor"],cohort,output)
            pairs.append(dict(**pair,sources=selected,host_tiles=len(source["host"][1]),patient_independence_verified=False))
            for j,(dose,side) in enumerate(zip(DOSES,SIDES)):
                p = dict(id=pair["id"]+f"-d{dose}")
                for role in ROLES:
                    s = selected[role]
                    p[role] = {k:s[k] for k in ("path","sha256","slide_id","tile_id")}
                    p[role]["crop_box"] = [0,0,224,224] if role == "host" else s["crop_boxes"][j]
                plans.append(p)
        # Existing compositor supports one crop per pair; 12 dose-pairs x 2 locations x 4 controls = 96.
        # Each dose uses its own two placements, because patch size differs; combined manifest retains all 96.
        records = []; parents = []; plan_receipts = []
        for j,(dose,side) in enumerate(zip(DOSES,SIDES)):
            plan = dict(schema_version=1,source_kind="real",interpolation="bilinear",pairs=plans[j::3],
                placements=[dict(id=name,width_fraction=side/224,height_fraction=side/224,left_fraction=x,top_fraction=y) for name,x,y in PLACEMENTS])
            plan_path = output/f"plan-d{dose}.json"; write_json(plan_path,plan)
            folder = output/f"dose-{dose}"; manifest = prepare(plan_path,folder); checks = verify_composites(folder,manifest)
            if checks["images"] != 32: raise ValueError("Incomplete dose-control set")
            for r in manifest["records"]:
                r["nominal_patch_area_percent"] = dose
                r["realized_patch_area_percent"] = 100*r["realized_area_fraction"]
                parent = next(p for p in pairs if p["id"] == r["pair_id"].rsplit("-d",1)[0])
                r["physical_patch_area_mm2"] = r["realized_area_fraction"]*math.prod(parent["sources"]["host"]["tile_size_um_xy"])/1e6
                for entry in r["files"].values(): entry["path"] = f"dose-{dose}/"+entry["path"]
                records.append(r)
            parents.extend(manifest["parents"])
            plan_receipts.append(dict(path=str(plan_path),sha256=file_sha256(plan_path),validation=checks))
        receipt = dict(schema_version=1,experiment_id=c["experiment_id"],source_kind="real",split="train",source_commit=source_commit,
            protocol_sha256=digest,slurm_job_id=os.environ["SLURM_JOB_ID"],images=96,pairs=pairs,records=records,
            parents=parents,plans=plan_receipts,checkpoint_sha256=c["checkpoint_sha256"],prompts_sha256=c["prompts_sha256"],
            encoding_contract=encoding_contract(),embedding_model=c["embedding_model"],models=c["models"],
            output_schema="embeddings.npz: float32 unit feats[96,512], opaque record_ids[96]; anchors.npz: 8 source vectors; measurements.json: all raw comparisons and paired summaries",
            inference_executed=False,scientific_effects_measured=False,final_test_accessed=False,
            limitations=c["limitations"])
        write_json(output/"image_manifest.json",receipt)
        files = {str(p.relative_to(output)):file_sha256(p) for p in sorted(output.rglob("*")) if p.is_file()}
        if len(records) != 96 or sum(p.stat().st_size for p in output.rglob("*.png")) > 100*1024**2:
            raise ValueError("Frozen image/storage bound exceeded")
        write_json(output/"completion.json",dict(status="prepared_verified_no_inference",files=files,images=96,
            manifest_sha256=file_sha256(output/"image_manifest.json"),protocol_sha256=digest,source_commit=source_commit))
        return receipt
    except BaseException as exc:
        write_json(output/"failure.json",dict(error=type(exc).__name__,message=str(exc),partial_outputs_preserved=True))
        raise


def prepared_inputs(output, expected_manifest):
    output = Path(output); completion = json.loads((output/"completion.json").read_text())
    if file_sha256(output/"image_manifest.json") != expected_manifest or completion["manifest_sha256"] != expected_manifest:
        raise ValueError("Frozen real image manifest differs")
    for name,digest in completion["files"].items():
        if (output/name).resolve().is_relative_to(output.resolve()) is False or file_sha256(output/name) != digest:
            raise ValueError("Prepared pixels/masks/provenance changed")
    m = json.loads((output/"image_manifest.json").read_text())
    if m["images"] != 96 or len(m["records"]) != 96 or m["split"] != "train":
        raise ValueError("Exactly frozen training composites required")
    for r in m["records"]:
        for e in r["files"].values():
            path = (output/e["path"]).resolve()
            if not path.is_relative_to(output.resolve()) or file_sha256(path) != e["sha256"]:
                raise ValueError("Frozen raster image/mask checksum differs")
    for pair in m["pairs"]:
        for s in pair["sources"].values():
            if file_sha256(s["path"]) != s["sha256"] or file_sha256(s["native_mask_path"]) != s["native_mask_sha256"]:
                raise ValueError("Original image/mask source changed")
    return m


def drift_gate(old, new, max_cosine_distance=1e-5, max_absolute_difference=5e-4):
    old = np.asarray(old); new = np.asarray(new)
    if old.shape != new.shape or not np.isfinite(new).all(): raise ValueError("Aligned finite unchanged embeddings required")
    distances = 1-np.clip(np.einsum("ij,ij->i",normalize(old.astype(float)),normalize(new.astype(float))),-1,1)
    maximum = np.max(np.abs(old-new),axis=1)
    result = dict(cosine_distance=distances.tolist(),maximum_absolute_difference=maximum.tolist(),
        maximum_cosine_distance_allowed=max_cosine_distance,maximum_absolute_difference_allowed=max_absolute_difference,
        passed=bool(np.all(distances <= max_cosine_distance) and np.all(maximum <= max_absolute_difference)))
    return result


def vector_signal(query, references):
    """Truth-free cosine NN5; no filenames, interventions or pixel masks enter."""
    q = np.asarray(query,float); ref = np.asarray(references,float)
    if q.ndim != 1 or ref.ndim != 2 or ref.shape[1] != len(q) or len(ref) < 5 or not np.isfinite(q).all() or not np.isfinite(ref).all():
        raise ValueError("Finite query and at least five native reference vectors required")
    if not np.isclose(np.linalg.norm(q),1,atol=1e-4) or not np.allclose(np.linalg.norm(ref,axis=1),1,atol=1e-4):
        raise ValueError("Unit-normalized query/reference embeddings required")
    similarities = np.einsum("d,id->i",q,ref,optimize=False)
    return float(1-np.clip(np.sort(similarities)[-5:],-1,1).mean())


def intervention_slides(host, donor_vector, host_index, composite_vector):
    """Matched one-slot image replacement; full-donor append/replacement are different doses."""
    mixed = host.feats.copy(); mixed[host_index] = composite_vector
    replacement = host.feats.copy(); replacement[host_index] = donor_vector
    return dict(mixed_image_replacement=Slide(mixed,host.coords,host.tile_ids,host.metadata),
        separate_donor_replacement=Slide(replacement,host.coords,host.tile_ids,host.metadata),
        separate_donor_append=Slide(np.vstack((host.feats,donor_vector)),np.vstack((host.coords,host.coords[host_index])),
            np.concatenate((host.tile_ids,np.array(["pixel-study-appended-donor"]))),host.metadata))


def measurements(c, m, features, sources, models):
    """Measurements fixed before GPU results; no threshold fitting or tissue filtering."""
    features = np.asarray(features)
    if features.ndim != 2 or len(features) != len(m["records"]) or not np.isfinite(features).all():
        raise ValueError("Aligned finite composite features required")
    pairs = {p["id"]:p for p in m["pairs"]}; result = []; base = {}; native = {}
    for pair in m["pairs"]:
        host,text = sources[pair["host"]]; i = pair["sources"]["host"]["tile_index"]
        ref = np.delete(host.feats,i,axis=0)
        controls = [vector_signal(host.feats[j],np.delete(host.feats,j,axis=0)) for j in range(len(host.feats)) if j != i]
        native[pair["id"]] = (ref,controls)
        base[pair["id"]] = {role:models[(pair["task"],role)].score_slide(host) for role in ("primary","historical")}
    for number,(r,feat) in enumerate(zip(m["records"],features)):
        pair_id = r["pair_id"].rsplit("-d",1)[0]; pair = pairs[pair_id]
        host,text = sources[pair["host"]]; donor,_ = sources[pair["donor"]]
        i = pair["sources"]["host"]["tile_index"]; di = pair["sources"]["donor"]["tile_index"]
        original = host.feats[i]; donor_vector = donor.feats[di]
        ref,controls = native[pair_id]; anomaly = vector_signal(feat,ref)
        bags = intervention_slides(host,donor_vector,i,feat)
        predictions = {mode:{role:models[(pair["task"],role)].score_slide(bag) for role in ("primary","historical")} for mode,bag in bags.items()}
        result.append(dict(record_id=f"image-{number:03d}",pair_id=pair_id,task=pair["task"],variant=r["variant"],
            nominal_patch_area_percent=r["nominal_patch_area_percent"],realized_patch_area_percent=r["realized_patch_area_percent"],
            placement_id=r["placement_id"],physical_patch_area_mm2=r["physical_patch_area_mm2"],
            edited_tile_percent_of_original_sampled_bag=100/len(host.feats),
            mixed_donor_area_percent_of_original_sampled_bag=r["realized_patch_area_percent"]/len(host.feats),
            distance_from_saved_host=float(1-np.clip(np.dot(feat,original),-1,1)),
            distance_from_saved_full_donor_tile=float(1-np.clip(np.dot(feat,donor_vector),-1,1)),
            morphology_similarity=dict(zip(text.classes,np.einsum("d,cd->c",feat,text.feats,optimize=False).tolist())),
            morphology_similarity_delta=dict(zip(text.classes,np.einsum("d,cd->c",feat-original,text.feats,optimize=False).tolist())),
            original_morphology_similarity=dict(zip(text.classes,np.einsum("d,cd->c",original,text.feats,optimize=False).tolist())),
            donor_morphology_similarity=dict(zip(text.classes,np.einsum("d,cd->c",donor_vector,text.feats,optimize=False).tolist())),
            nn5_anomaly=anomaly,native_control_percentile=float(np.mean(np.array(controls) <= anomaly)),
            native_controls=len(controls),native_control_nn5=controls,baseline_predictions=base[pair_id],intervention_predictions=predictions,
            decision_changes={mode:{role:p["prediction"] != base[pair_id][role]["prediction"] for role,p in values.items()} for mode,values in predictions.items()}))
    paired = []
    for key in sorted({(r["pair_id"],r["nominal_patch_area_percent"],r["placement_id"]) for r in result}):
        group = {r["variant"]:r for r in result if (r["pair_id"],r["nominal_patch_area_percent"],r["placement_id"]) == key}
        foreign = group["foreign_patch"]
        comparisons = {}
        for name in ("native_sham","unchanged","cut_reinsert_null"):
            control = group[name]
            comparisons[name] = dict(host_distance_difference=foreign["distance_from_saved_host"]-control["distance_from_saved_host"],
                donor_distance_difference=foreign["distance_from_saved_full_donor_tile"]-control["distance_from_saved_full_donor_tile"],
                nn5_difference=foreign["nn5_anomaly"]-control["nn5_anomaly"],
                morphology_score_difference={k:foreign["morphology_similarity"][k]-control["morphology_similarity"][k] for k in foreign["morphology_similarity"]})
        paired.append(dict(pair_id=key[0],nominal_patch_area_percent=key[1],placement_id=key[2],comparisons=comparisons))
    return dict(records=result,paired_comparisons=paired,unique_training_pairs=4,independent_patients_verified=False,
        no_threshold_selected=True,pixel_localization_evaluated=False,tissue_action="none",limitations=c["limitations"])


def encode_real(config_path, digest, project, preparation, manifest_sha256, output, source_commit):
    if not os.environ.get("SLURM_JOB_ID") or not os.environ.get("SLURM_JOB_GPUS"):
        raise RuntimeError("Explicitly approved GPU Slurm execution required")
    c = preflight(config_path,digest,project,True); m = prepared_inputs(preparation,manifest_sha256)
    if m["protocol_sha256"] != digest or str(output) != c["gpu_output"] or str(preparation) != c["preparation_output"]:
        raise ValueError("Exact frozen image/protocol/output paths required")
    import torch
    from ..conch import ConchEncoder
    if torch.cuda.device_count() != 1 or file_sha256(c["checkpoint"]) != c["checkpoint_sha256"]:
        raise ValueError("Exactly one GPU and verified existing checkpoint required")
    torch.set_num_threads(4); torch.manual_seed(0)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    if encoding_contract() != m["encoding_contract"]:
        raise ValueError("Frozen canonical GPU environment changed")
    output = Path(output); output.mkdir(exist_ok=False)
    try:
        encoder = ConchEncoder(c["checkpoint"])
        if encoder.provenance != m["embedding_model"]: raise ValueError("Canonical preprocessing/model provenance changed")
        sources = {}; paths = []; old = []
        for pair in m["pairs"]:
            for role in ("host","donor"):
                sid = pair[role]; s = pair["sources"][role]; root = Path(c["encoded_root"])/sid
                if file_sha256(root/"slide.npz") != s["saved_slide_sha256"] or verified_digest(c,sid) != s["embedding_completion_sha256"]:
                    raise ValueError("Original source embedding changed")
                slide,text = Slide.load(root/"slide.npz"),TextEmbeddings.load(root/"text.npz")
                if slide.metadata["model"] != encoder.provenance or text.fingerprint() != c["text_fingerprint"]:
                    raise ValueError("Saved source/text provenance differs")
                sources[sid] = (slide,text); paths.append(s["path"]); old.append(slide.feats[s["tile_index"]])
        anchors,anchor_seconds = encoder.images(paths,16)
        gate = drift_gate(np.array(old),anchors,**c["drift_tolerances"])
        write_json(output/"unchanged_drift_gate.json",gate)
        with (output/"anchors.npz").open("xb") as f: np.savez_compressed(f,feats=anchors)
        if not gate["passed"]: raise RuntimeError("Unchanged-source drift: stop before encoding composites")
        paths = [str(Path(preparation)/r["files"]["image"]["path"]) for r in m["records"]]
        feats,seconds = encoder.images(paths,16)
        if feats.shape != (96,512) or not np.isfinite(feats).all() or not np.allclose(np.linalg.norm(feats,axis=1),1,atol=1e-4):
            raise ValueError("Canonical composite vector shape/norm differs")
        with (output/"embeddings.npz").open("xb") as f:
            np.savez_compressed(f,feats=feats,record_ids=np.array([f"image-{i:03d}" for i in range(96)]))
        null_old = []; null_new = []
        for r,feat in zip(m["records"],feats):
            if r["variant"] in ("unchanged","cut_reinsert_null"):
                pair = next(p for p in m["pairs"] if p["id"] == r["pair_id"].rsplit("-d",1)[0])
                null_old.append(sources[pair["host"]][0].feats[pair["sources"]["host"]["tile_index"]]); null_new.append(feat)
        null_gate = drift_gate(np.array(null_old),np.array(null_new),**c["drift_tolerances"])
        write_json(output/"null_control_drift_gate.json",null_gate)
        if not null_gate["passed"]: raise RuntimeError("Null-control feature drift: stop before measurements")
        models = {(e["task"],e["role"]):load_predictor(Path(project)/e["directory"]) for e in c["models"]}
        report = measurements(c,m,feats,sources,models)
        report.update(source_commit=source_commit,manifest_sha256=manifest_sha256,protocol_sha256=digest,slurm_job_id=os.environ["SLURM_JOB_ID"],
            model=encoder.provenance,anchor_encoding_seconds=anchor_seconds,composite_encoding_seconds=seconds)
        write_json(output/"measurements.json",report)
        prepared_inputs(preparation,manifest_sha256)
        write_json(output/"completion.json",dict(status="verified",images=96,protocol_sha256=digest,manifest_sha256=manifest_sha256,
            files={p.name:file_sha256(p) for p in output.iterdir() if p.is_file()}))
        return report
    except BaseException as exc:
        write_json(output/"failure.json",dict(error=type(exc).__name__,message=str(exc),partial_outputs_preserved=True))
        raise
