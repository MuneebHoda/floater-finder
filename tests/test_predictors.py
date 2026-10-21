"""Software fixtures only; no scientific evidence is generated here."""
import json
from types import SimpleNamespace
import numpy as np
import pytest
from floater_finder.predictors import FrozenPredictor, load_predictor, slide_vector
from floater_finder.predictors.data import load_development
from floater_finder.predictors.evaluation import grouped_folds, nested_linear, metrics


def common(d=3):
    return dict(schema_version=1, classes=['benign','cancer'], input_dimensions=d, model_id='fixture-linear',
                checkpoint_sha256='a'*64, embedding_model=dict(name='fixture',revision='v1',checkpoint_sha256='a'*64,
                    normalized=True,projection=True,preprocessing='fixture-only'),source_kind='fixture',
                top_k=5, kind='linear_probe', feature_rule='mean')


def test_pooling_is_order_invariant_and_small_slide_uses_all_tiles():
    x=np.array([[1.,2.,3.],[3.,4.,0.]])
    expected=np.r_[x.mean(0),x.max(0),x.mean(0)]
    np.testing.assert_array_equal(slide_vector(x,'mean_max_topk',5),expected)
    np.testing.assert_array_equal(slide_vector(x[::-1],'mean_max_topk',5),expected)
    with pytest.raises(ValueError):slide_vector(np.empty((0,3)))
    with pytest.raises(ValueError):slide_vector([[np.nan]])


def test_pickle_free_roundtrip_hash_and_checkpoint(tmp_path):
    model=FrozenPredictor(common(),dict(coef=np.array([1.,0.,-1.]),mean=np.zeros(3),scale=np.ones(3),intercept=np.array([.25])))
    model.save(tmp_path/'model'); loaded=load_predictor(tmp_path/'model')
    x=np.array([[2.,1.,0.]])
    assert loaded(x)==model(x)
    assert loaded(x)['prediction']=='cancer'
    with pytest.raises(ValueError,match='checkpoint'):
        loaded.score_slide(SimpleNamespace(feats=x,metadata={'model':{'checkpoint_sha256':'b'*64},'source_kind':'fixture'}))
    m=dict(common()['embedding_model'])
    assert loaded.score_slide(SimpleNamespace(feats=x,metadata={'model':m,'source_kind':'fixture'}))==loaded(x)
    with pytest.raises(ValueError,match='preprocessing'):
        loaded.score_slide(SimpleNamespace(feats=x,metadata={'model':dict(m,preprocessing='different'),'source_kind':'fixture'}))
    with pytest.raises(ValueError,match='source'):
        loaded.score_slide(SimpleNamespace(feats=x,metadata={'model':m,'source_kind':'real'}))
    with pytest.raises(ValueError,match='dimension'):
        loaded.score_slide(SimpleNamespace(feats=np.ones((1,4)),metadata={'model':m,'source_kind':'fixture'}))
    path=tmp_path/'model'/'parameters.npz';path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='hash'):load_predictor(tmp_path/'model')


def test_zero_shot_is_exact_legacy_pooling():
    from floater_finder.scoring import pool
    x=np.array([[1.,0.,0.],[0.,1.,0.]],dtype=np.float32)
    text=x.copy()
    for rule in ('mean','top1pct','top5pct'):
        m=FrozenPredictor(dict(common(),kind='zero_shot',pooling=rule),{'text':text})
        expected=pool(np.einsum('id,cd->ic',x,text,optimize=False),rule)
        assert m(x)['scores']==dict(zip(['benign','cancer'],map(float,expected)))
        assert m(x)['prediction']=='benign'
        assert m(x)['positive_probability'] is None


def test_final_test_rejected_before_reading_any_input(tmp_path):
    with pytest.raises(ValueError,match='Final test'):
        load_development(tmp_path/'notread',None,None,None,'test')


def test_nested_cv_disjoint_groups_and_portable_fit_matches_sklearn():
    pytest.importorskip('sklearn')
    from floater_finder.predictors.evaluation import fit_linear, portable
    rng=np.random.default_rng(4);y=np.repeat([0,1],12)
    feats=[rng.normal(size=(5,3))+int(i)*2 for i in y]
    slides=[SimpleNamespace(feats=f,metadata={'slide_id':str(i)}) for i,f in enumerate(feats)]
    config=dict(top_k=5,c_grid=[.01,.1,1.],outer_folds=4,inner_folds=3,seed=17,maximum_iterations=1000,tolerance=1e-6)
    groups=np.array([str(i//2) for i in range(24)])
    rows,model,audit=nested_linear(slides,y,groups,'mean',config,common())
    assert len(rows)==24 and len(audit['outer'])==4
    for a in audit['outer']:
        train={int(i)//2 for i in a['training_ids']};valid={int(i)//2 for i in a['validation_ids']}
        assert not train&valid
    x=np.array([slide_vector(f) for f in feats]); fit,_=fit_linear(x,y,.1,config);p=portable(fit,'mean',common())
    np.testing.assert_allclose([p(f)['margin'] for f in feats],fit.decision_function(x),rtol=1e-10,atol=1e-10)
    assert metrics(rows,['benign','cancer'],17)['slides']==24


def test_fold_standardization_does_not_fit_validation_outlier():
    pytest.importorskip('sklearn')
    from floater_finder.predictors.evaluation import fit_linear
    x=np.array([[0.],[1.],[2.],[3.],[10000.]])
    fit,_=fit_linear(x[:4],np.array([0,0,1,1]),.1,dict(maximum_iterations=1000,tolerance=1e-6,seed=3))
    np.testing.assert_array_equal(fit.steps[0][1].mean_,[1.5])
    assert fit.decision_function(x[-1:]).shape==(1,)


def test_fixture_run_freezes_primary_before_opening_known_calibration(tmp_path, monkeypatch):
    pytest.importorskip('sklearn')
    import floater_finder.predictors.run as runner
    rng=np.random.default_rng(7); output=tmp_path/'outputs'
    def sources(n,prefix):
        result=[]
        for grade,offset in [(0,-1.),(1,0.),(4,1.)]:
            for i in range(n):
                sid=f'{prefix}-{grade}-{i}'; feats=rng.normal(size=(5,3))*.1+offset
                metadata=dict(slide_id=sid,isup_grade=grade,cohort_split=prefix,model=common()['embedding_model'],source_kind='fixture',
                    panda={'pyramid_dimensions':[[100,100]],'mask_available':True},measured_mpp_xy=[.5,.5],
                    extraction={'sampled_tissue_grid_fraction':.7,'eligible_tissue_cells':7})
                annotations=[dict(area_mm2='0.01',gleason3_fraction='0',gleason4_fraction='0',gleason5_fraction='0') for _ in range(5)]
                result.append(dict(slide=SimpleNamespace(feats=feats,metadata=metadata),
                    text=SimpleNamespace(feats=np.array([[-1.,0.,0.],[1.,0.,0.],[-1.,0.,0.],[1.,0.,0.]]),classes=['benign','cancer','low_grade','high_grade']),
                    annotations=annotations,group=sid,identity={'software_fixture':True}))
        return result
    train,cal=sources(12,'train'),sources(2,'calibration');opened=[]
    def load(*args):
        split=args[-1];opened.append(split)
        if split=='calibration':
            assert (output/'selection_frozen.json').exists()
            frozen=json.loads((output/'selection_frozen.json').read_text())
            assert frozen['calibration_opened_for_selection'] is False
        return (train if split=='train' else cal),{'text_fingerprint':'fixture-only'}
    monkeypatch.setattr(runner,'load_development',load)
    monkeypatch.setenv('SLURM_JOB_ID','software-fixture');monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    config_path=__import__('pathlib').Path(__file__).parents[1]/'configs/panda_predictor_research_v1.json'
    manifest=tmp_path/'manifest';manifest.write_text('software fixture, no real slides')
    tasks=runner.run(manifest,'unused','unused',manifest,config_path,output)
    assert opened==['train','calibration']
    assert set(tasks)=={'benign_cancer','low_high'}
    assert all(len(t['all_models'])==5 for t in tasks.values())
    assert json.loads((output/'completion.json').read_text())['test_slides_scored'] is False
