import pytest
from floater_finder.panda_baseline import classification_metrics


def test_balanced_accuracy_uses_class_denominators_and_lists_errors():
    rows=[dict(image_id=str(i),truth='cancer' if i<4 else 'benign',prediction='cancer') for i in range(6)]
    result=classification_metrics(rows,('benign','cancer'))
    assert result['accuracy']==pytest.approx(4/6)
    assert result['balanced_accuracy']==.5
    assert result['confusion_rows_truth_columns_prediction']==[[0,2],[0,4]]
    assert result['errors']==['4','5']
    assert classification_metrics(rows[:4],('benign','cancer'))['balanced_accuracy'] is None


def test_baseline_seals_test_slides_and_rejects_mask_enriched_views(tmp_path,monkeypatch):
    # Synthetic contract mocks only; temporary metrics are never scientific evidence.
    import csv
    from pathlib import Path
    import numpy as np
    from floater_finder import panda_baseline as baseline
    from floater_finder.artifacts import Slide,TextEmbeddings
    from conftest import MODEL
    rows=[]
    for g,grade in enumerate((0,1,4)):
        for i in range(20):rows.append(dict(image_id=f'{g*100+i:032x}',isup_grade=grade,split='train' if i<12 else 'calibration' if i<16 else 'test'))
    manifest=tmp_path/'fixture.csv'
    with manifest.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    by_id={r['image_id']:r for r in rows};loaded=[];mask_enriched=False
    model=MODEL|{'checkpoint_sha256':'0'*64}
    phrases={c:[f'{c} fixture {i}' for i in range(3)] for c in sum(baseline.TASKS.values(),())}
    text=TextEmbeddings(np.eye(4),list(phrases),phrases,model,'real')
    def load(path):
        sid=Path(path).parent.name;row=by_id[sid];loaded.append(sid)
        assert row['split']!='test'
        meta=dict(slide_id=sid,patient_id='unknown',project='PANDA',organ='prostate',coordinate_units='microns',
            source_kind='real',split='dev',cohort_split=row['split'],data_provider='radboud',isup_grade=row['isup_grade'],
            model=model,extraction=dict(sampling_mode='donor' if mask_enriched else 'representative',selection_uses_mask=mask_enriched))
        return Slide(np.eye(1,4),np.zeros((1,2)),np.array(['fixture-tile']),meta)
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only')
    monkeypatch.setattr(baseline.Slide,'load',load)
    monkeypatch.setattr(baseline.TextEmbeddings,'load',lambda _:text)
    monkeypatch.setattr(baseline,'file_sha256',lambda _:'0'*64)
    metrics=baseline.evaluate_development(manifest,tmp_path/'encoded',tmp_path/'fixture-output')
    assert len(loaded)==48 and not {r['image_id'] for r in rows if r['split']=='test'}.intersection(loaded)
    assert metrics['train/benign_cancer/mean']['slides']==36
    assert metrics['calibration/low_high/mean']['slides']==8
    mask_enriched=True
    with pytest.raises(ValueError,match='Only matching representative'):
        baseline.evaluate_development(manifest,tmp_path/'encoded',tmp_path/'rejected')
    assert not (tmp_path/'rejected').exists()
