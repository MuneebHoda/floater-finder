"""Contract tests using software arrays, without any real slide inference."""
import importlib.util
from pathlib import Path
import numpy as np
from floater_finder.artifacts import Slide,TextEmbeddings,normalize
from floater_finder.panda_stress import binary_predictions
from conftest import MODEL

spec=importlib.util.spec_from_file_location('panda_piece_dev',Path(__file__).resolve().parents[1]/'scripts/panda_piece_development.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_piece_scorer_exactly_matches_saved_feature_binary_pooling():
    rng=np.random.default_rng(37)
    features=normalize(rng.normal(size=(100,512)).astype(np.float32))
    metadata=dict(slide_id='fixture',patient_id='unknown',project='PANDA',organ='prostate',
                  coordinate_units='microns',split='dev',source_kind='fixture',model=MODEL)
    slide=Slide(features,np.c_[np.arange(100),np.zeros(100)],np.array([str(i) for i in range(100)]),metadata)
    phrases={c:[c+' fixture '+str(i) for i in range(3)] for c in ('benign','cancer','low_grade','high_grade')}
    text=TextEmbeddings(normalize(rng.normal(size=(4,512)).astype(np.float32)),list(phrases),phrases,MODEL,'fixture')
    assert module.make_scorer(text)(slide.feats,slide.coords)==binary_predictions(slide,text)['top5pct']


def test_empty_counterfactual_cases_do_not_become_non_alert_denominators():
    rows=[dict(evaluable_pieces=0,any_decisive=False),dict(evaluable_pieces=2,any_decisive=True)]
    result=module.dependence_counts(rows)
    assert result['unmodified_evaluable_slides']==1 and result['unmodified_unevaluable_slides']==1
    assert result['unmodified_decision_dependence_rate']==1
    assert module.dependence_counts(rows[:1])['unmodified_decision_dependence_rate'] is None
