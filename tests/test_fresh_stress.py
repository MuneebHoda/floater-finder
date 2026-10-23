"""Temporary artificial arrays only; these checks never produce scientific results."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest

from test_panda_stress import slide
from floater_finder.artifacts import Slide
from floater_finder.experiments import file_sha256
from floater_finder.predictors.linear_probe import FrozenPredictor
from floater_finder.research import fresh_stress as followup
from floater_finder.research.contracts import ExperimentRun
from floater_finder.research.registry import Registry

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_fresh_s1_v1.json'


class FixtureScorer:
    spec=dict(model_id='artificial-decisive-region',kind='zero_shot')

    def __call__(self, features):
        margin=float(features[:,1].max()*2-1)
        return dict(prediction='cancer' if margin>0 else 'benign',scores=dict(benign=-margin/2,cancer=margin/2),
            margin=margin,positive_probability=None,model_id=self.spec['model_id'])

    def score_slide(self, slide):
        return self(slide.feats)


def fixtures():
    sources={}
    for sid,grade in [('fixture-host',0),('fixture-donor',4)]:
        s=slide(sid,grade);s.metadata.update(cohort_split='engineering',selection_manifest_sha256='a'*64)
        s.feats[:]=0;s.feats[:,int(grade>0)]=1
        rows=[dict(tile_id=t,area_mm2=.01,gleason3_fraction=0,gleason4_fraction=.5 if grade else 0,gleason5_fraction=0) for t in s.tile_ids]
        sources[sid]=dict(slide=s,grade=grade,rows=rows)
    config=json.loads(CONFIG.read_text())
    config.update(seeds=[7],counterfactual_seed=7,percentages=[5,10],manifest_sha256='a'*64,
        baseline_protocol_sha256='b'*64,excluded_ids=[],text_fingerprint='artificial-fixture-text')
    return sources,dict(primary=FixtureScorer(),historical=FixtureScorer()),config


def test_preflight_never_scores_or_opens_slide_arrays(monkeypatch):
    def forbidden(*a,**k):raise AssertionError('metadata-only preflight')
    monkeypatch.setattr(FrozenPredictor,'__call__',forbidden)
    monkeypatch.setattr(Slide,'load',forbidden)
    c,p,rows,models=followup.preflight(CONFIG,file_sha256(CONFIG),PROJECT)
    assert len(rows)==60 and set(models)=={'primary','historical'}
    assert c['maximum_interventions']==1200 and c['maximum_counterfactual_bags']==140
    assert c['alert_policy'] is None and c['approval_required']
    with pytest.raises(ValueError,match='protocol changed'):followup.preflight(CONFIG,'wrong',PROJECT)


def test_unsafe_scope_or_source_freeze_fails_preflight(tmp_path):
    c=json.loads(CONFIG.read_text());c['modes'].append('near_tissue')
    p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='bounded'):followup.preflight(p,file_sha256(p),PROJECT)
    c=json.loads(CONFIG.read_text());c['source_files']['src/floater_finder/research/engine.py']='0'*64
    p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='source changed'):followup.preflight(p,file_sha256(p),PROJECT)
    c=json.loads(CONFIG.read_text());c['excluded_ids']=[];p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='membership'):followup.preflight(p,file_sha256(p),PROJECT)


def test_saved_baseline_check_allows_only_tiny_numeric_noise_and_no_decision_drift():
    p=FixtureScorer()(np.eye(2,512));saved=deepcopy(p)
    saved['scores']=dict(reversed(list(saved['scores'].items())))
    followup.same_prediction(p,saved)
    saved['margin']+=1e-13;followup.same_prediction(p,saved)
    saved['margin']+=.01
    with pytest.raises(RuntimeError,match='scores differ'):followup.same_prediction(p,saved)
    saved=deepcopy(p);saved['prediction']='benign'
    with pytest.raises(RuntimeError,match='decision differs'):followup.same_prediction(p,saved)


def test_fixture_interventions_use_shared_engine_and_preserve_sources_and_null_shams(tmp_path):
    sources,models,c=fixtures();before={sid:s['slide'].feats.copy() for sid,s in sources.items()}
    out=tmp_path/'fixture-only'
    result=followup.experiment(sources,models,c,'fixture-source-only',out)
    assert result['source_kind']=='fixture' and result['eligible_model_trial_records']==16 and result['exclusions']==0
    assert result['original_final_test_predictions_computed'] is False and result['review_alert_rate'] is None
    for metric in result['metrics']:
        assert metric['oracle_exact_passes']==metric['eligible_instances']
        assert metric['new_original_host_label_errors']==(metric['eligible_instances'] if metric['control']=='foreign_cancer' else 0)
    assert all(np.array_equal(before[sid],s['slide'].feats) for sid,s in sources.items())
    assert len(result['counterfactual_counts'])==12
    assert all(r['evaluable_slides']==0 and r['unevaluable_slides']==2 for r in result['unmodified_dependence'])
    with pytest.raises(FileExistsError):followup.experiment(sources,models,c,'fixture-source-only',out)


def test_capacity_exclusions_keep_unknown_realized_dose_and_correct_denominators(tmp_path):
    sources,models,c=fixtures();sources['fixture-donor']['slide'].coords[:,0]=np.arange(20)*400.
    result=followup.experiment(sources,models,c,'fixture-source-only',tmp_path/'capacity')
    assert result['exclusions']==2 and result['eligible_model_trial_records']==12
    metric=next(r for r in result['metrics'] if r['role']=='primary' and r['control']=='foreign_cancer' and r['mode']=='append_legacy' and r['requested_percent']==10)
    assert metric['planned_instances']==1 and metric['excluded_instances']==1 and metric['originally_correct_planned']==1
    assert metric['originally_correct_eligible']==0 and metric['induced_error_interval']['estimate'] is None


def test_genuine_small_positive_component_is_decisive_without_foreign_alert():
    sources,_,_=fixtures();source=sources['fixture-donor'];s=source['slide'].subset([0,1])
    s.coords[:,0]=[0,300];s.feats[:]=0;s.feats[0,0]=1;s.feats[1,1]=1
    report=followup.counterfactual(s,FixtureScorer(),np.array([0.,.01]),dict(mode='clean'))
    assert report['geometry']['connectivity']==8 and report['geometry']['max_gap_tiles']==0
    decisive=[p for p in report['pieces'] if p['decision_changing']]
    assert len(decisive)==1 and decisive[0]['evaluation_only_genuine_cancer_area_mm2']==.01
    assert decisive[0]['evaluation_only_foreign_tiles']==0 and decisive[0]['area_mm2']==.01
    assert decisive[0]['counterfactual']['result']['prediction']=='benign'
    assert not report['alerts_evaluated'] and report['alerts']==[]


def test_prediction_change_initial_error_and_induced_error_denominators_are_distinct():
    _,_,c=fixtures();rows=[]
    for sid,correct in [('correct-fixture',True),('incorrect-fixture',False)]:
        rows.append(dict(role='primary',control='foreign_cancer',mode='append_legacy',requested_percent=5,
            host_id=sid,donor_id='donor-fixture',seed=7,originally_correct=correct,prediction_changed=True,
            new_original_host_error=correct,margin_shift=1.,oracle_exact=True,contaminated=dict(prediction='cancer' if correct else 'benign')))
    excluded=[dict(control='foreign_cancer',mode='append_legacy',requested_percent=5,originally_correct=dict(primary=True,historical=True))]
    result=followup.summarize(rows,excluded,[],[],c)
    m=next(r for r in result['metrics'] if r['role']=='primary' and r['control']=='foreign_cancer' and r['mode']=='append_legacy' and r['requested_percent']==5)
    assert m['planned_instances']==3 and m['originally_correct_planned']==2
    assert m['eligible_instances']==2 and m['originally_correct_eligible']==1 and m['initially_incorrect_eligible']==1
    assert m['prediction_changes']==2 and m['new_original_host_label_errors']==1


def test_oracle_failure_stops_and_preserves_failed_registry(tmp_path,monkeypatch):
    sources,models,c=fixtures();original=followup.apply_intervention
    def broken(*args,**kwargs):
        result=original(*args,**kwargs)
        def fail(*a):raise RuntimeError('fixture oracle failure')
        return SimpleNamespace(slide=result.slide,audit_json=result.audit_json,verify=fail)
    monkeypatch.setattr(followup,'apply_intervention',broken);out=tmp_path/'failed-fixture'
    with pytest.raises(RuntimeError,match='oracle failure'):followup.experiment(sources,models,c,'fixture-source-only',out)
    metadata=json.loads((out/'run.json').read_text());registry=Registry(out,ExperimentRun(**metadata['run']))
    assert registry.report()['status']=='failed' and registry.load_checkpoint('summary') is None
    with pytest.raises(FileExistsError):followup.experiment(sources,models,c,'fixture-source-only',out)


def test_real_execution_requires_cpu_slurm_and_predeclared_workload(monkeypatch,tmp_path):
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='CPU Slurm'):followup.run(*([None]*5),execute=True)
    sources,models,c=fixtures();c['maximum_interventions']=1
    with pytest.raises(ValueError,match='bound exceeded'):followup.experiment(sources,models,c,'fixture-source-only',tmp_path/'bound')
    assert not (tmp_path/'bound').exists()
    sources,models,c=fixtures()
    for s in sources.values():s['slide'].metadata['source_kind']='real'
    with pytest.raises(RuntimeError,match='CPU Slurm'):followup.experiment(sources,models,c,'fixture-source-only',tmp_path/'real-forbidden')
