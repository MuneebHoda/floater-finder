"""Software fixtures only: these arrays are never PANDA scientific evidence."""
import numpy as np
import pytest
from floater_finder.artifacts import Slide,TextEmbeddings
from floater_finder.injection import grid_neighbors,verify_oracle
from floater_finder.panda_stress import cancer_components,foreign_count,inject_development_s1,run
from conftest import MODEL


def slide(sid,grade,n=20):
    meta=dict(slide_id=sid,patient_id='unknown',patient_id_known=False,project='PANDA',organ='prostate',
        coordinate_units='microns',microns_per_unit=1,tile_step=[100.,100.],tile_size=[100.,100.],
        split='dev',cohort_split='train',data_provider='radboud',isup_grade=grade,source_kind='fixture',
        model=MODEL,panda=dict(mask_available=True))
    return Slide(np.eye(n,512),np.c_[np.arange(n)*100.,np.zeros(n)],np.array([f't{i}' for i in range(n)]),meta)


def test_cancer_components_use_native_fractions_and_do_not_bridge_missing_tiles():
    d=slide('donor-fixture',1,4);d.coords[:,0]=[0,100,300,500]
    rows=[dict(tile_id=f't{i}',gleason3_fraction=a,gleason4_fraction=b,gleason5_fraction=0.)
          for i,(a,b) in enumerate(((.2,0),(.05,.05),(0,.3),(.02,0)))]
    assert [a.tolist() for a in cancer_components(d,rows,.1)]==[[0,1],[2]]
    d.metadata['panda']['mask_available']=False
    assert cancer_components(d,rows,.1)==[]
    rows[0]['tile_id']='misaligned'
    with pytest.raises(ValueError,match='align'):cancer_components(d,rows,.1)


def test_unknown_patients_stay_unknown_and_exact_oracle_restores_host():
    h,d=slide('host-fixture',0),slide('donor-fixture',4)
    phrases={c:[c+' fixture '+str(i) for i in range(3)] for c in ('benign','cancer','low_grade','high_grade')}
    text=TextEmbeddings(np.eye(4,512),list(phrases),phrases,MODEL,'fixture')
    before=h.feats.copy();mixed=inject_development_s1(h,d,np.array([0,1]),10,20261020)
    assert len(mixed.feats)==22 and mixed.foreign_mask.sum()==2
    assert mixed.metadata['patient_id']=='unknown' and mixed.metadata['injection']['donor_patient_id']=='unknown'
    assert mixed.metadata['injection']['patient_independence_verified'] is False
    assert mixed.metadata['injection']['realized_percent']==10
    assert len(grid_neighbors(mixed))==22  # Translation preserves the common physical grid.
    restored=verify_oracle(h,mixed,text)
    assert np.array_equal(before,h.feats) and np.array_equal(restored.feats,h.feats)
    assert restored.metadata==h.metadata
    zero=inject_development_s1(h,d,np.array([],dtype=int),0,20261020)
    assert not zero.foreign_mask.any() and verify_oracle(h,zero,text).metadata==h.metadata
    assert foreign_count(.5,512)==3 and foreign_count(10,183)==19


def test_s1_refuses_test_leakage_repeated_tiles_disconnected_fragments_and_same_patient():
    h,d=slide('host-fixture',0),slide('donor-fixture',4)
    with pytest.raises(ValueError,match='four-connected'):inject_development_s1(h,d,np.array([0,2]),10,0)
    with pytest.raises(ValueError,match='Distinct donor indices'):inject_development_s1(h,d,np.array([0,0]),10,0)
    d.metadata['cohort_split']='test'
    with pytest.raises(ValueError,match='same development split'):inject_development_s1(h,d,np.array([0,1]),10,0)
    d.metadata['cohort_split']='train';h.metadata['patient_id_known']=d.metadata['patient_id_known']=True
    with pytest.raises(ValueError,match='same-patient'):inject_development_s1(h,d,np.array([0,1]),10,0)


def test_real_s1_runner_requires_slurm_before_reading_inputs(monkeypatch,tmp_path):
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='CPU Slurm'):run('absent','absent','absent','absent','absent',tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_frozen_test_injection_preserves_real_split_without_relaxing_development_guard():
    from floater_finder.panda_stress import _inject_s1
    h,d=slide('test-host-fixture',0),slide('test-donor-fixture',4)
    h.metadata['cohort_split']=d.metadata['cohort_split']='test'
    h.metadata['split']=d.metadata['split']='eval'
    with pytest.raises(ValueError,match='development split'):inject_development_s1(h,d,np.array([0,1]),10,0)
    mixed=_inject_s1(h,d,np.array([0,1]),10,0,allowed_splits=('test',))
    assert mixed.metadata['cohort_split']=='test' and mixed.metadata['split']=='eval'
    assert mixed.metadata['injection']['host_metadata']['cohort_split']=='test'
    assert h.metadata['patient_id']=='unknown'
