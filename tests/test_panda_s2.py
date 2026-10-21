"""S2 software fixtures; no scientific performance evidence."""
import numpy as np
import pytest
from conftest import MODEL
from floater_finder.artifacts import TextEmbeddings
from floater_finder.injection import verify_oracle
from floater_finder.panda_s2 import pattern_components, inject, predictions, summarize, visual_distance, run
from test_panda_stress import slide


def labels(n, fractions):
    return [dict(tile_id=f't{i}',gleason3_fraction=a,gleason4_fraction=b,gleason5_fraction=c)
            for i,(a,b,c) in enumerate(fractions[:n])]


def test_pattern_controls_require_native_fractions_and_four_connectivity():
    d=slide('high-donor',4,5);d.coords[:,0]=[0,100,300,400,600]
    rows=labels(5,[(0,.2,0),(0,.3,0),(0,.1,.2),(.3,0,0),(0,0,.3)])
    assert [x.tolist() for x in pattern_components(d,rows,'high_gp45')]==[[0,1],[2],[4]]
    assert [x.tolist() for x in pattern_components(d,rows,'high_gp4_only')]==[[0,1]]
    assert [x.tolist() for x in pattern_components(d,rows,'high_gp5_positive')]==[[2],[4]]
    assert pattern_components(d,rows,'same_grade_gp3_only')==[]
    d.metadata['isup_grade']=1
    assert [x.tolist() for x in pattern_components(d,rows,'same_grade_gp3_only')]==[[3]]
    d.metadata['panda']['mask_available']=False
    assert pattern_components(d,rows,'high_gp45')==[]
    rows[0]['tile_id']='wrong'
    with pytest.raises(ValueError,match='align'):pattern_components(d,rows,'high_gp45')


def test_s2_oracle_preserves_unknown_patients_all_arrays_and_original_metadata():
    h,d=slide('host',1),slide('donor',4)
    phrases={c:[c+' fixture '+str(i) for i in range(3)] for c in ('benign','cancer','low_grade','high_grade')}
    text=TextEmbeddings(np.eye(4,512),list(phrases),phrases,MODEL,'fixture')
    before=h.feats.copy();mixed=inject(h,d,np.array([0,1]),10,20261020,'high_gp45')
    assert mixed.metadata['isup_grade']==1 and mixed.metadata['patient_id']=='unknown'
    assert mixed.metadata['injection']['patient_independence_verified'] is False
    assert mixed.metadata['injection']['donor_slide_id']=='donor'
    assert np.array_equal(mixed.feats[:20],before)
    restored=verify_oracle(h,mixed,text)
    assert restored.metadata==h.metadata and predictions(restored,text)==predictions(h,text)
    assert np.array_equal(h.feats,before)
    assert len(mixed.feats)==22 and mixed.foreign_mask.sum()==2


def test_s2_blocks_test_leakage_wrong_grade_same_patient_and_disconnected_tiles():
    h,d=slide('host',1),slide('donor',4)
    with pytest.raises(ValueError,match='four-connected'):inject(h,d,np.array([0,2]),10,0,'high_gp45')
    with pytest.raises(ValueError,match='Unique donor'):inject(h,d,np.array([0,0]),10,0,'high_gp45')
    with pytest.raises(ValueError,match='condition-specific'):inject(h,d,np.array([0,1]),10,0,'same_grade_gp3_only')
    d.metadata['cohort_split']='test'
    with pytest.raises(ValueError,match='development split'):inject(h,d,np.array([0,1]),10,0,'high_gp45')
    d.metadata['cohort_split']='train';h.metadata['patient_id_known']=d.metadata['patient_id_known']=True
    with pytest.raises(ValueError,match='eligible distinct'):inject(h,d,np.array([0,1]),10,0,'high_gp45')


def test_s2_new_error_denominator_excludes_initially_high_hosts_and_retains_reversals():
    def pred(value):return {p:dict(prediction=value,high_minus_low_margin=.1) for p in ('mean','top1pct','top5pct')}
    trials=[dict(split='calibration',condition='high_gp45',requested_percent=1,baseline=pred(a),contaminated=pred(b),oracle_exact_recovery=True)
            for a,b in [('low_grade','high_grade'),('low_grade','low_grade'),('high_grade','high_grade'),('high_grade','low_grade')]]
    row=next(r for r in summarize(trials) if (r['split'],r['condition'],r['requested_percent'],r['pooling'])==('calibration','high_gp45',1,'mean'))
    assert row['hosts']==4 and row['originally_correct_low_hosts']==2
    assert row['initially_high_hosts']==2 and row['newly_induced_low_to_high_errors']==1
    assert row['new_error_rate']==.5 and row['prediction_changes']==2 and row['high_to_low_reversals']==1
    assert row['oracle_exact_passes']==4


def test_visual_context_and_cpu_gate(monkeypatch,tmp_path):
    x=np.eye(2,512)
    assert visual_distance(x[:1],x[:1])==0
    assert visual_distance(x[:1],x[1:])==1
    assert visual_distance(x[:0],x) is None
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='bounded CPU Slurm'):run(*(['missing']*6),tmp_path/'output')
    assert not (tmp_path/'output').exists()
