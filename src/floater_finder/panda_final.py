"""Fail-closed final protocol validation and slide-level uncertainty; no predictions in preflight."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import numpy as np
from .experiments import file_sha256
from .panda_review import wilson


def _inside(path,roots):
    p=Path(path).resolve()
    return any(p==r or r in p.parents for r in roots)


def preflight(protocol_path,expected_sha256,source_root):
    if file_sha256(protocol_path)!=expected_sha256:raise ValueError('Frozen protocol checksum differs')
    protocol=json.loads(Path(protocol_path).read_text());source_root=Path(source_root).resolve()
    if protocol.get('schema_version')!=1 or protocol.get('status')!='frozen' or protocol.get('automatic_tissue_action')!='none':
        raise ValueError('A frozen review-only protocol is required')
    source=protocol['source']
    snapshot=json.loads((source_root.parent/'snapshot.json').read_text())
    if snapshot['commit']!=source['commit']:raise ValueError('Source commit differs from frozen protocol')
    for name,digest in source['files'].items():
        path=source_root/name
        if not _inside(path,[source_root]) or file_sha256(path)!=digest:raise ValueError('Frozen source file differs')
    for name,version in protocol['runtime_versions'].items():
        if importlib.metadata.version(name)!=version:raise ValueError('Runtime version differs: '+name)
    roots=[Path(p).resolve() for p in protocol['allowed_data_roots']]
    data=protocol['data'];index_path=Path(data['blinded_index'])
    for name,digest in [(data['manifest'],data['manifest_sha256']),(data['verification'],data['verification_sha256']),(index_path,data['blinded_index_sha256'])]:
        if not _inside(name,roots) or file_sha256(name)!=digest:raise ValueError('Frozen data contract differs')
    for name,digest in data.get('additional_files',{}).items():
        if not _inside(name,roots) or file_sha256(name)!=digest:raise ValueError('Additional frozen input differs')
    evidence=protocol.get('development_evidence')
    if evidence:
        if not _inside(evidence['path'],roots) or file_sha256(evidence['path'])!=evidence['sha256']:raise ValueError('Development evidence checksum/path differs')
        selection=json.loads(Path(evidence['path']).read_text())
        if selection['selected_rule']!=protocol['review_policy']['rules']['combined']:
            raise ValueError('Development selection evidence differs')
        if selection['operating_point_supported'] is not protocol['readiness']['operating_point_supported']:
            raise ValueError('Readiness contradicts observed development gates')
    index=json.loads(index_path.read_text());entries=index['entries']
    if len(entries)!=24 or len({r['image_id'] for r in entries})!=24:raise ValueError('Exactly 24 distinct test IDs required')
    if sorted(r['image_id'] for r in entries)!=sorted(protocol['test_ids']):raise ValueError('Test membership differs')
    files={};forbidden={'isup_grade','gleason_score','prediction','ground_truth','cancer_fraction'}
    for entry in entries:
        if forbidden.intersection(entry) or not re.fullmatch('[0-9a-f]{32}',entry['image_id']):raise ValueError('Blinded contract contains labels/invalid IDs')
        names={Path(p).name for p in entry['files']}
        if not {'slide.npz','text.npz','timing.json','completion.json','tiles.csv','metadata.json'}.issubset(names):raise ValueError('Incomplete test input contract')
        if not any(n.endswith('.png') for n in names) or entry['image_path'] not in entry['files']:raise ValueError('Missing RGB/WSI inputs')
        for name,digest in entry['files'].items():
            if not _inside(name,roots):raise ValueError('Input path outside approved data roots')
            if name in files and files[name]!=digest:raise ValueError('Contradictory input identity')
            files[name]=digest
    for name,digest in files.items():
        if file_sha256(name)!=digest:raise ValueError('Final input checksum mismatch: '+Path(name).name)
    target=Path(protocol['execution']['output'])
    if not _inside(target,roots):raise ValueError('Final output is outside approved roots')
    if target.exists():raise FileExistsError('Final output already exists; single execution guard')
    if not target.parent.is_dir():raise ValueError('Verified final output parent is absent')
    return dict(protocol_frozen=True,protocol_sha256=expected_sha256,source_commit=source['commit'],input_files_verified=len(files),
        test_slides=24,test_predictions_computed=False,test_labels_decoded=False,
        ready_for_final_predictions=protocol['readiness']['operating_point_supported'] is True,
        readiness_reason=protocol['readiness']['reason'],automatic_tissue_action='none')


def require_execution(protocol,execute_final):
    if not execute_final:raise RuntimeError('Final predictions require the explicit --execute-final command')
    if protocol.get('status')!='frozen' or protocol['readiness']['operating_point_supported'] is not True:
        raise RuntimeError('No supported frozen review operating point; final predictions remain blocked')


def classification_summary(truth,predictions,seed=20261021,repetitions=2000):
    truth=np.asarray(truth,dtype=int);predictions=np.asarray(predictions,dtype=int)
    if truth.shape!=predictions.shape or truth.ndim!=1 or not np.isin(truth,[0,1]).all() or not np.isin(predictions,[0,1]).all():raise ValueError('Aligned binary slide labels required')
    matrix=np.zeros((2,2),int)
    for a,b in zip(truth,predictions):matrix[a,b]+=1
    support=matrix.sum(axis=1);recall=[matrix[i,i]/support[i] if support[i] else None for i in (0,1)]
    interval=None
    if all(support):
        rng=np.random.default_rng(seed);draws=[]
        for _ in range(repetitions):
            values=[]
            for label in (0,1):
                ids=np.flatnonzero(truth==label);sample=rng.choice(ids,len(ids),replace=True);values.append(np.mean(predictions[sample]==label))
            draws.append(np.mean(values))
        interval=np.quantile(draws,[.025,.975]).tolist()
    return dict(unit='unique slide; true patient independence unverified',slides=len(truth),classes=['benign','cancer'],
        confusion_rows_truth_columns_prediction=matrix.tolist(),class_support=support.tolist(),
        accuracy=float(np.trace(matrix)/len(truth)) if len(truth) else None,
        balanced_accuracy=float(np.mean(recall)) if all(v is not None for v in recall) else None,
        class_recall=[float(v) if v is not None else None for v in recall],
        class_recall_wilson95=[wilson(int(matrix[i,i]),int(support[i])) for i in (0,1)],
        balanced_accuracy_stratified_slide_bootstrap95=interval,bootstrap_repetitions=repetitions,bootstrap_seed=seed)


def clustered_ratio_interval(rows,numerator,denominator,seed=20261021,repetitions=2000):
    """Resample unique host slides, retaining every dose/control within each host."""
    groups={}
    for row in rows:
        values=groups.setdefault(row['host_id'],[0.,0.]);values[0]+=float(row[numerator]);values[1]+=float(row[denominator])
    if not groups:return dict(estimate=None,interval95=None,unique_host_slides=0,valid_bootstraps=0)
    array=np.array(list(groups.values()));estimate=float(array[:,0].sum()/array[:,1].sum()) if array[:,1].sum() else None
    if len(array)<2 or estimate is None:return dict(estimate=estimate,interval95=None,unique_host_slides=len(array),valid_bootstraps=0)
    rng=np.random.default_rng(seed);draws=[]
    for _ in range(repetitions):
        totals=array[rng.integers(0,len(array),len(array))].sum(axis=0)
        if totals[1]:draws.append(totals[0]/totals[1])
    return dict(estimate=estimate,interval95=np.quantile(draws,[.025,.975]).tolist() if draws else None,
        unique_host_slides=len(array),valid_bootstraps=len(draws),bootstrap_seed=seed,
        interpretation='conditional on fixed donor assignments; shared donors and unknown patient overlap limit population inference')
