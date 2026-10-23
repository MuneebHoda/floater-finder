"""Deterministic candidate manifests from official PANDA metadata and file catalog."""
import csv
import hashlib
import json
from pathlib import Path

from .experiments import file_sha256
from .artifacts import write_json

GROUPS = ('benign', 'gg1', 'high_grade')


def candidates(train_rows, files, seed=20261020, engineering_ids=()):
    if len({r['image_id'] for r in train_rows}) != len(train_rows):
        raise ValueError('Duplicate original image IDs')
    catalog = {}
    for item in files:
        if item['name'] in catalog or type(item['bytes']) is not int or item['bytes'] <= 0:
            raise ValueError('Duplicate/invalid catalog entry')
        catalog[item['name']] = item['bytes']
    rows = []
    for original in train_rows:
        image_id = original['image_id']
        if len(image_id) != 32 or any(c not in '0123456789abcdef' for c in image_id):
            raise ValueError('Unexpected official PANDA image ID')
        if original['data_provider'] != 'radboud':
            continue
        grade = int(original['isup_grade'])
        group = 'benign' if grade == 0 else 'gg1' if grade == 1 else 'high_grade' if grade in (4,5) else None
        image, mask = f'train_images/{image_id}.tiff', f'train_label_masks/{image_id}_mask.tiff'
        if group is None or image not in catalog:
            continue
        rows.append(dict(image_id=image_id, data_provider='radboud', isup_grade=grade,
            gleason_score=original['gleason_score'], group=group, patient_id='', patient_id_known=False,
            image_file=image, image_catalog_bytes=catalog[image], mask_file=mask if mask in catalog else '',
            mask_catalog_bytes=catalog.get(mask,0), mask_catalog_available=mask in catalog,
            mask_usable_verified=False, gp45_positive_verified=False,
            engineering_exposed=image_id in engineering_ids, selection_seed=seed))
    return rows


def select(rows, per_group, seed=20261020):
    if per_group not in (20,40):
        raise ValueError('Approved planning targets are 20 or 40 per group')
    def rank(row, purpose):
        return hashlib.sha256(f"{seed}:{purpose}:{row['image_id']}".encode()).hexdigest()
    selected = []
    for group in GROUPS:
        pool = [r.copy() for r in rows if r['group'] == group]
        pool.sort(key=lambda r:(not r['engineering_exposed'], not r['gp45_positive_verified'],
                               not r['mask_catalog_available'], rank(r,'select')))
        if len(pool) < per_group:
            raise ValueError(f'Insufficient catalog-eligible {group}: {len(pool)} < {per_group}')
        chosen = pool[:per_group]
        # Nested 60/120 plans preserve the split assigned to every shared slide.
        for start in range(0, per_group, 20):
            block = chosen[start:start+20]
            block.sort(key=lambda r:(not r['engineering_exposed'], rank(r,'split')))
            for index, row in enumerate(block):
                row['split'] = 'train' if index < 12 else 'calibration' if index < 16 else 'test'
                if row['engineering_exposed'] and row['split'] != 'train':
                    raise ValueError('Too many exposed cases for training-only allocation')
                selected.append(row)
    if len({r['image_id'] for r in selected}) != len(selected):
        raise ValueError('Duplicate selected slides')
    return selected


def plan(root, catalog_path, output, seed=20261020, mask_profile=None):
    root, output = Path(root), Path(output)
    catalog = json.loads(Path(catalog_path).read_text())
    if not catalog['complete'] or catalog.get('error'):
        raise ValueError('A complete, successful official catalog is required')
    with (root/'train.csv').open(newline='') as f:
        originals = list(csv.DictReader(f))
    with (root/'annotated_cohort.csv').open(newline='') as f:
        exposed = {r['image_id'] for r in csv.DictReader(f)}
    eligible = candidates(originals, catalog['files'], seed, exposed)
    if mask_profile is not None:
        audits = {r['image_id']: r for r in json.loads(Path(mask_profile).read_text())['slides']}
        for row in eligible:
            audited = audits.get(row['image_id'], {}).get('mask_audit')
            if audited:
                row['mask_usable_verified'] = True
                row['gp45_positive_verified'] = audited['gp45_positive']
    output.mkdir(parents=True, exist_ok=False)
    provenance = dict(status='candidate plans; acquisition and mask usability are not verified', seed=seed,
        train_csv_sha256=file_sha256(root/'train.csv'), catalog_sha256=file_sha256(catalog_path),
        preserved_partial_manifest_sha256=file_sha256(root/'annotated_cohort.csv'),
        eligible_catalog_counts={g:sum(r['group']==g for r in eligible) for g in GROUPS},
        patient_independence='unknown; no patient identifiers supplied; slide-disjoint splits only', plans={})
    provenance['mask_profile_sha256'] = file_sha256(mask_profile) if mask_profile is not None else None
    for count in (60,120):
        chosen = select(eligible, count//3, seed)
        required = []
        for row in chosen:
            row.update(acquisition_status='not_acquired', verification_status='not_run', tiling_status='not_run',
                       embedding_status='not_run', evaluation_status='not_run')
            for role in ('image','mask'):
                name, size = row[role+'_file'], row[role+'_catalog_bytes']
                path = root/name if name else None
                exists = bool(path and path.is_file())
                actual = path.stat().st_size if exists else 0
                if exists and actual != size:
                    raise ValueError(f'Existing file/catalog size mismatch: {name}')
                row[role+'_local_present'] = exists
                row[role+'_actual_bytes'] = actual
                if name:
                    required.append(dict(name=name, bytes=size, existing=exists, image_id=row['image_id'], role=role))
            row['acquisition_status'] = 'local_size_match_only' if row['image_local_present'] else 'not_acquired'
        manifest = output/f'candidate_{count}.csv'
        with manifest.open('x',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(chosen[0]));writer.writeheader();writer.writerows(chosen)
        record = dict(slides=count, manifest_sha256=file_sha256(manifest), files=required,
            listed_missing_file_bytes=sum(f['bytes'] for f in required if not f['existing']),
            listed_total_file_bytes=sum(f['bytes'] for f in required),
            catalog_masks=sum(r['mask_catalog_available'] for r in chosen),
            local_images=sum(r['image_local_present'] for r in chosen), local_masks=sum(r['mask_local_present'] for r in chosen),
            transfer_bytes='not measured; the per-file endpoint may ZIP-compress TIFFs',
            integrity='catalog sizes only; downloaded bytes require CRC/SHA256 and reader checks')
        write_json(output/f'acquisition_{count}.json',record)
        provenance['plans'][str(count)]={k:v for k,v in record.items() if k!='files'}
    write_json(output/'provenance.json',provenance)
    return provenance
