"""Verified train/known-calibration loaders which never open held-out slide artifacts."""
import csv
import json
from pathlib import Path
from ..artifacts import Slide, TextEmbeddings, check_compatible
from ..experiments import file_sha256


def load_development(manifest, directories, encoded, verification, split):
    if split not in ('train', 'calibration'):
        raise ValueError('Final test artifacts are forbidden in predictor development')
    receipt = json.loads(Path(verification).read_text())
    if file_sha256(manifest) != receipt['manifest_sha256']:
        raise ValueError('Cohort manifest differs from verified receipt')
    # Read split/ID first. Never inspect test metadata, arrays, coordinates or labels.
    with Path(manifest).open(newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['split'] == split]
    if not rows or len({r['image_id'] for r in rows}) != len(rows):
        raise ValueError('Nonempty unique development split required')
    paths = [Path(p) for p in json.loads(Path(directories).read_text())]
    identities = {r['image_id']: r for r in receipt['records']}; sources = []
    for row in rows:
        sid = row['image_id']; root = Path(encoded)/sid
        matches = [p for p in paths if sid in p.parts]
        if len(matches) != 1:
            raise ValueError('Source paths must uniquely contain the eligible slide ID')
        directory = matches[0]; identity = identities[sid]
        if file_sha256(root/'completion.json') != identity['completion_sha256']:
            raise ValueError('Embedding completion identity differs')
        for name, digest in identity['artifact_sha256'].items():
            if file_sha256(root/name) != digest:
                raise ValueError('Embedding artifact identity differs')
        completion = json.loads((root/'completion.json').read_text())
        for name, key in [('tiles.csv', 'manifest_sha256'), ('metadata.json', 'metadata_sha256')]:
            if file_sha256(directory/name) != completion['input_identity'][key]:
                raise ValueError('Tiling input identity differs')
        slide, text = Slide.load(root/'slide.npz'), TextEmbeddings.load(root/'text.npz'); m = slide.metadata
        check_compatible(slide, text)
        if (m['source_kind'] != 'real' or m['project'] != 'PANDA' or m['data_provider'] != 'radboud' or
            m['slide_id'] != sid or m['cohort_split'] != split or int(row['isup_grade']) != m['isup_grade'] or
            m['isup_grade'] not in (0, 1, 4, 5) or m['extraction']['sampling_mode'] != 'representative' or
            m['extraction']['selection_uses_mask'] or text.fingerprint() != receipt['text_fingerprint']):
            raise ValueError('Only matching original representative Radboud development inputs are eligible')
        if slide.foreign_mask.any() or 'injection' in m:
            raise ValueError('Unmodified original slide required')
        with (directory/'tiles.csv').open(newline='') as f:
            annotations = list(csv.DictReader(f))
        if [r['tile_id'] for r in annotations] != slide.tile_ids.tolist():
            raise ValueError('Diagnostic annotation rows differ from tile order')
        sources.append(dict(slide=slide, text=text, annotations=annotations, directory=directory,
            identity=identity, group=('patient:'+m['patient_id']) if m.get('patient_id_known') else 'slide:'+sid))
    return sources, receipt
