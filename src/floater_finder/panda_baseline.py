"""Development-only, slide-level PANDA zero-shot baselines; no mask input to scoring."""
import csv
import json
import os
from pathlib import Path
import numpy as np

from .artifacts import Slide,TextEmbeddings,write_json
from .experiments import file_sha256
from .scoring import POOLING,pool,tile_scores

TASKS={'benign_cancer':('benign','cancer'),'low_high':('low_grade','high_grade')}


def classification_metrics(rows,classes):
    matrix=np.zeros((2,2),dtype=int)
    for row in rows:
        matrix[classes.index(row['truth']),classes.index(row['prediction'])]+=1
    support=matrix.sum(axis=1)
    recall=[float(matrix[i,i]/support[i]) if support[i] else None for i in range(2)]
    return dict(classes=list(classes),confusion_rows_truth_columns_prediction=matrix.tolist(),
        slides=int(matrix.sum()),accuracy=float(np.trace(matrix)/matrix.sum()) if matrix.sum() else None,
        balanced_accuracy=float(np.mean(recall)) if all(v is not None for v in recall) else None,
        class_support=support.tolist(),class_recall=recall,
        errors=[r['image_id'] for r in rows if r['prediction']!=r['truth']])


def evaluate_development(manifest,encoded_root,output):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Real cohort scoring requires a bounded Slurm CPU job')
    with Path(manifest).open(newline='') as handle:
        cohort=list(csv.DictReader(handle))
    if len(cohort) not in (60,120) or len({r['image_id'] for r in cohort})!=len(cohort):
        raise ValueError('Complete fixed 60/120-slide manifest required')
    selected=[r for r in cohort if r['split'] in ('train','calibration')]
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a fresh baseline output')
    records=[];inputs={};fingerprint=None
    for row in selected:
        directory=Path(encoded_root)/row['image_id']
        slide,text=Slide.load(directory/'slide.npz'),TextEmbeddings.load(directory/'text.npz')
        meta=slide.metadata
        if (meta['source_kind']!='real' or meta['project']!='PANDA' or meta['data_provider']!='radboud' or
                meta['slide_id']!=row['image_id'] or meta['isup_grade']!=int(row['isup_grade']) or
                meta.get('cohort_split')!=row['split'] or meta['extraction']['sampling_mode']!='representative' or
                meta['extraction']['selection_uses_mask'] or set(text.classes)!=set(sum(TASKS.values(),()))):
            raise ValueError('Only matching representative, correctly split real PANDA artifacts are eligible')
        if fingerprint is not None and text.fingerprint()!=fingerprint:
            raise ValueError('Prompt/model fingerprint differs between slides')
        fingerprint=text.fingerprint()
        scores=tile_scores(slide,text)
        inputs[row['image_id']]={name:file_sha256(directory/name) for name in ('slide.npz','text.npz','completion.json')}
        grade=int(row['isup_grade'])
        if grade not in (0,1,4,5):raise ValueError('Slide grade is outside the fixed cohort scope')
        for task,classes in TASKS.items():
            if task=='low_high' and grade==0:continue
            truth=classes[int(grade!=0)] if task=='benign_cancer' else classes[int(grade>=4)]
            indices=[text.classes.index(c) for c in classes]
            for rule in POOLING:
                values=pool(scores[:,indices],rule)
                records.append(dict(image_id=row['image_id'],split=row['split'],task=task,pooling=rule,
                    truth=truth,prediction=classes[int(np.argmax(values))],scores=dict(zip(classes,values.tolist())),
                    label_scope='original slide ISUP; no per-tile grade assignment'))
    summary={}
    for split in ('train','calibration'):
        for task,classes in TASKS.items():
            for rule in POOLING:
                subset=[r for r in records if r['split']==split and r['task']==task and r['pooling']==rule]
                summary[f'{split}/{task}/{rule}']=classification_metrics(subset,classes)
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'predictions.json',records)
    write_json(output/'metrics.json',dict(source_kind='real',category='PANDA development clean zero-shot baseline',
        metrics=summary,independent_unit='slide; patient independence unverified',test_slides_scored=False,
        manifest_sha256=file_sha256(manifest),text_fingerprint=fingerprint,input_artifact_sha256=inputs,
        clinical_validity_verified=False,contamination_evaluated=False))
    return summary
