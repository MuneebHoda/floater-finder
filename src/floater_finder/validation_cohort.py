"""Outcome-blind, metadata-only fresh PANDA validation proposals; no acquisition."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def propose(train_rows, catalog, excluded_ids, *, provider, per_group=20, seed=20261021):
    if provider not in ("radboud", "karolinska") or per_group < 1:
        raise ValueError("Specify a PANDA provider and a positive group size")
    if not catalog.get("complete") or catalog.get("error"):
        raise ValueError("Complete successful official catalog required")
    if len({r["image_id"] for r in train_rows}) != len(train_rows):
        raise ValueError("Duplicate metadata slide ID")
    files = {}
    for f in catalog["files"]:
        if f["name"] in files or type(f["bytes"]) is not int or f["bytes"] <= 0:
            raise ValueError("Invalid or duplicate catalog record")
        files[f["name"]] = f["bytes"]
    excluded_ids = set(excluded_ids)
    exposed_patients = {r["patient_id"] for r in train_rows
                        if r["image_id"] in excluded_ids and r.get("patient_id")}
    eligible = {g: [] for g in ("benign", "gg1", "high_grade")}
    for r in train_rows:
        sid, grade = r["image_id"], int(r["isup_grade"])
        if len(sid) != 32 or any(c not in "0123456789abcdef" for c in sid):
            raise ValueError("Invalid PANDA image ID")
        group = "benign" if grade == 0 else "gg1" if grade == 1 else "high_grade" if grade in (4, 5) else None
        patient = r.get("patient_id", "")
        image, mask = f"train_images/{sid}.tiff", f"train_label_masks/{sid}_mask.tiff"
        if (r["data_provider"] != provider or group is None or sid in excluded_ids
                or (patient and patient in exposed_patients) or image not in files):
            continue
        eligible[group].append(dict(image_id=sid, data_provider=provider,
            isup_grade=grade, gleason_score=r["gleason_score"], group=group,
            patient_id=patient, split="fresh_development_validation", seed=seed,
            image_file=image, image_catalog_bytes=files[image],
            mask_file=mask if mask in files else "", mask_catalog_bytes=files.get(mask, 0),
            mask_usable_verified=False, acquisition_status="not_checked"))
    chosen, selected_patients = [], set()
    for group, pool in eligible.items():
        pool.sort(key=lambda r: (not r["mask_file"], hashlib.sha256(
            f"{seed}:fresh-validation:{provider}:{r['image_id']}".encode()).hexdigest()))
        count = 0
        for r in pool:
            if r["patient_id"] and r["patient_id"] in selected_patients:
                continue
            chosen.append(r)
            if r["patient_id"]:
                selected_patients.add(r["patient_id"])
            count += 1
            if count == per_group:
                break
    counts = dict(Counter(r["group"] for r in chosen))
    return chosen, dict(provider=provider, seed=seed, target_per_group=per_group,
        eligible_after_exclusion={g: len(v) for g, v in eligible.items()},
        selected_counts={g: counts.get(g, 0) for g in eligible}, selected_slides=len(chosen),
        target_met=all(counts.get(g, 0) == per_group for g in eligible),
        excluded_slide_ids=len(excluded_ids), selected_excluded_overlap=0,
        selected_known_patient_ids=len(selected_patients),
        patient_independence="unknown unless every selected and excluded slide has a verified patient identifier",
        catalog_masks=sum(bool(r["mask_file"]) for r in chosen),
        usable_mask_coverage="unverified; catalog presence is not readable annotation",
        catalog_tiff_bytes=sum(r["image_catalog_bytes"] + r["mask_catalog_bytes"] for r in chosen),
        transfer_bytes="unmeasured; compression/ZIP overhead can change network volume",
        selection_rule="catalog mask first, then SHA256(seed:purpose:provider:image_id); no predictions or annotation contents",
        status="metadata-only proposal; acquisition, tiling, encoding and validation not executed")


def write_proposal(train, catalog_path, exclude_manifests, output, *, per_group=20, seed=20261021):
    train, catalog_path, output = Path(train), Path(catalog_path), Path(output)
    with train.open(newline="") as f:
        rows = list(csv.DictReader(f))
    excluded = set()
    for path in exclude_manifests:
        with Path(path).open(newline="") as f:
            excluded.update(r["image_id"] for r in csv.DictReader(f))
    catalog = json.loads(catalog_path.read_text())
    proposals = {p: propose(rows, catalog, excluded, provider=p, per_group=per_group, seed=seed)
                 for p in ("radboud", "karolinska")}
    output.mkdir(parents=True, exist_ok=False)
    report = dict(train_sha256=sha256(train), catalog_sha256=sha256(catalog_path),
        exclusion_manifest_sha256={str(p): sha256(p) for p in exclude_manifests},
        patient_id_column_present="patient_id" in rows[0], proposals={})
    for provider, (chosen, summary) in proposals.items():
        path = output / f"{provider}_fresh_validation_candidates.csv"
        if chosen:
            with path.open("x", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(chosen[0]))
                writer.writeheader()
                writer.writerows(chosen)
            summary["manifest_sha256"] = sha256(path)
        report["proposals"][provider] = summary
    (output / "proposal.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def prepare_fresh_baseline(project, train, catalog_path, pilot, output):
    """Freeze the existing Radboud60 proposal and models; never acquire or predict."""
    from .predictors import load_predictor
    project, output = Path(project), Path(output)
    proposal_root = project/'reports/fresh_validation_metadata_v1'
    proposal = json.loads((proposal_root/'proposal.json').read_text())
    candidate = proposal_root/'radboud_fresh_validation_candidates.csv'
    exposed = project/'reports/manifests/panda_candidate_120_20261020.csv'
    if (sha256(train) != proposal['train_sha256'] or sha256(catalog_path) != proposal['catalog_sha256'] or
            sha256(candidate) != proposal['proposals']['radboud']['manifest_sha256'] or
            sha256(exposed) != proposal['exclusion_manifest_sha256']['reports/manifests/panda_candidate_120_20261020.csv'] or
            sha256(pilot) != proposal['exclusion_manifest_sha256']['/tmp/floater-fresh-validation-metadata/pilot.csv']):
        raise ValueError('Metadata proposal/input checksums changed')
    def rows(path):
        with Path(path).open(newline='') as handle: return list(csv.DictReader(handle))
    originals = {r['image_id']:r for r in rows(train)}
    exclusions = rows(exposed)+rows(pilot); excluded = {r['image_id'] for r in exclusions}
    patients = {r['patient_id'] for r in exclusions if r.get('patient_id')}
    chosen = rows(candidate)
    if len(chosen) != 60 or len({r['image_id'] for r in chosen}) != 60:
        raise ValueError('Exactly the frozen 60 candidates required')
    catalog = json.loads(Path(catalog_path).read_text())
    if not catalog['complete'] or catalog.get('error'): raise ValueError('Successful complete catalog required')
    files = {r['name']:r['bytes'] for r in catalog['files']}
    required = []; execution = []
    for row in chosen:
        sid = row['image_id']; original = originals[sid]
        if (sid in excluded or (row['patient_id'] and row['patient_id'] in patients) or
                row['split'] != 'fresh_development_validation' or row['data_provider'] != 'radboud' or
                any(str(row[k]) != str(original[k]) for k in ('data_provider','isup_grade','gleason_score'))):
            raise ValueError('Fresh slide/patient exclusion or original label check failed')
        for role in ('image','mask'):
            name = row[role+'_file']; size = int(row[role+'_catalog_bytes'])
            expected = ('train_images/' if role=='image' else 'train_label_masks/')+sid+('_mask' if role=='mask' else '')+'.tiff'
            if name != expected or files.get(name) != size or size <= 0: raise ValueError('Catalog file identity differs')
            required.append(dict(image_id=sid,role=role,name=name,bytes=size))
        execution.append(dict(row,candidate_split=row['split'],split='engineering',validation_role=row['split']))
    if Counter(r['group'] for r in chosen) != dict(benign=20,gg1=20,high_grade=20):
        raise ValueError('Frozen group counts differ')
    selection_path = project/'reports/panda_predictors_v1/run/selection_frozen.json'
    selection = json.loads(selection_path.read_text()); models = []
    for task,historical in (('benign_cancer','zero_shot_top5pct'),('low_high','zero_shot_mean')):
        if selection['tasks'][task]['primary'] != 'linear_mean_max_topk' or selection['calibration_opened_for_selection']:
            raise ValueError('Original training-only model selection differs')
        for role,name,base in (('primary','linear_mean_max_topk','run'),('historical',historical,'adapter_acceptance/corrected_models')):
            directory = Path('reports/panda_predictors_v1')/(base+'/models' if base=='run' else base)/task/name
            model = load_predictor(project/directory)
            if set(model.spec['train_ids']) & {r['image_id'] for r in chosen}: raise ValueError('Model training overlap')
            models.append(dict(task=task,role=role,model_id=name,directory=str(directory),
                sha256={n:sha256(project/directory/n) for n in ('predictor.json','parameters.npz')}))
    source_names = ['src/floater_finder/predictors/fresh.py','src/floater_finder/predictors/linear_probe.py',
        'src/floater_finder/predictors/pooling.py','src/floater_finder/predictors/evaluation.py',
        'src/floater_finder/artifacts.py','src/floater_finder/panda.py','src/floater_finder/panda_encoding.py',
        'src/floater_finder/panda_final.py','src/floater_finder/panda_review.py','src/floater_finder/validation_cohort.py',
        'scripts/panda_fresh_baseline.py','scripts/panda_fresh_baseline_prepare.py','scripts/panda_tile_cohort.py',
        'scripts/panda_acquire.py','scripts/panda_encode_batch.py','configs/panda_morphology_v1.yaml',
        'scripts/slurm/panda_fresh_acquire.sbatch','scripts/slurm/panda_fresh_baseline.sbatch',
        'scripts/slurm/panda_tile_cohort.sbatch','scripts/slurm/panda_encode_cohort.sbatch']
    model = load_predictor(project/models[0]['directory'])
    protocol = dict(schema_version=1,status='frozen_before_acquisition',scope='fresh_clean_baseline_only',
        candidate_sha256=sha256(candidate),train_sha256=sha256(train),catalog_sha256=sha256(catalog_path),
        selection_sha256=sha256(selection_path),image_ids=[r['image_id'] for r in chosen],excluded_slide_ids=sorted(excluded),
        models=models,embedding_model=model.spec['embedding_model'],text_fingerprint=model.spec['text_fingerprint'],
        prompts_sha256=sha256(project/'configs/panda_morphology_v1.yaml'),bootstrap_seed=20261024,
        source_files={n:sha256(project/n) for n in source_names},
        analysis='Report both frozen train-selected linear primaries plus exact historical BC top5% / grade mean comparators. No fitting, model switch, thresholds, contamination or floater-policy claims. BC: all60; low/high: ISUP1 vs4/5 only40; no ISUP2/3 claim. Class confusion/recall/BA, conditional unique-slide bootstrap and uncalibrated probability diagnostics; no outcome-driven revision.',
        intake_gate='All60 input artifacts must pass before any prediction. Technical failures remain recorded and block this v1; no silent replacement/exclusion. An explicit pre-prediction protocol amendment is needed if the frozen cohort cannot be completed.',
        limitations=['Slide-disjoint from129 exposed IDs; patient independence unknown.',
            'Known calibration was repeatedly inspected development. Training-only selection is historical; fresh results cannot retune it.',
            'Artificial tests verify software only; acquisition, mask usability, new embeddings and fresh scientific results are unexecuted.',
            'This evaluates clean slide predictions, not a floater detector, clinical grading or final-test readiness. Original24 test slides remain sealed.'])
    output.mkdir(parents=True,exist_ok=False)
    with (output/'manifest.csv').open('x',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=list(execution[0])); writer.writeheader(); writer.writerows(execution)
    protocol['manifest_sha256'] = sha256(output/'manifest.csv')
    acquisition = dict(slides=60,files=required,catalog_tiff_bytes=sum(r['bytes'] for r in required),
        candidate_sha256=sha256(candidate),manifest_sha256=protocol['manifest_sha256'],catalog_sha256=sha256(catalog_path),
        approval_required=True,integrity='Catalog sizes; after approval verify ZIP CRC when present, local SHA256 and bounded CPU reader alignment. No external checksums available.')
    for name,value in (('protocol.json',protocol),('acquisition.json',acquisition)):
        (output/name).write_text(json.dumps(value,indent=2)+'\n')
    return dict(status='prepared_not_executed',slides=60,groups=dict(Counter(r['group'] for r in chosen)),
        excluded_ids=len(excluded),catalog_tiff_bytes=acquisition['catalog_tiff_bytes'],
        hashes={p.name:sha256(p) for p in sorted(output.iterdir())},predictions_computed=False,downloads_started=False)
