"""Artificial embeddings and saved-score records only, never real study outcomes."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest

from floater_finder.detectors import stable_context as study
from floater_finder.experiments import file_sha256
from floater_finder.panda_review import prediction
from floater_finder.research.contracts import slide_identity
from floater_finder.research.context_safety import read_sealed
from test_panda_stress import slide

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_stable_context_v1.json'


def test_reference_support_consensus_and_truth_boundary_are_fixed():
    f=np.tile([1.,0.],(64,1));f[-4:]=[0.,1.];xy=np.c_[np.arange(64),np.zeros(64)]
    p=[dict(indices=list(range(60))),dict(indices=[60,61,62,63],foreign=True,grade=0)]
    rows=study.stable_features(f,xy,p)
    assert rows[0]['stable_score'] is None and 'candidate_is_majority_of_sampled_bag' in rows[0]['eligibility_reasons']
    assert rows[1]['stable_score']==100. and len(rows[1]['context_samples'])==3
    for sample in rows[1]['context_samples']:
        assert len(sample['reference_indices'])==32 and not set(sample['reference_indices'])&set(p[1]['indices'])
    assert rows==study.stable_features(f,xy+10000,[dict(indices=q['indices']) for q in p])
    assert np.array_equal(f[-4:],np.tile([0.,1.],(4,1)))


def test_small_context_abstains_without_downsizing_or_invented_scores():
    f=np.tile([1.,0.],(33,1));xy=np.zeros((33,2))
    rows=study.stable_features(f,xy,[dict(indices=[0]),dict(indices=[1,2])])
    assert rows[0]['distinct_reference_subsets']==1  # All 32 references reused under each seed.
    assert rows[1]['stable_score'] is None and rows[1]['context_samples']==[]
    assert rows[1]['eligibility_reasons']==['fewer_than_32_comparison_tiles']
    with pytest.raises(ValueError,match='normalized'):study.stable_features(f*2,xy,[dict(indices=[0])])
    with pytest.raises(ValueError,match='Disjoint'):study.stable_features(f,xy,[dict(indices=[0]),dict(indices=[0])])


def test_every_reused_donor_and_host_stay_in_one_fold():
    ids=[str(i) for i in range(12)];trials=[dict(host_id='0',donor_id='2'),dict(host_id='1',donor_id='2'),dict(host_id='2',donor_id='3')]
    a,groups=study.source_folds(ids,trials,3,1)
    assert a['0']==a['1']==a['2']==a['3'] and groups['0']==groups['3']
    assert (a,groups)==study.source_folds(list(reversed(ids)),list(reversed(trials)),3,1)
    with pytest.raises(ValueError,match='Distinct'):study.source_folds(ids,[dict(host_id='0',donor_id='missing')])


def records(sid,scores,parts,cancer=False,foreign=None):
    n=len(scores);base=prediction(scores);components=[]
    for ix in parts:
        keep=sorted(set(range(n))-set(ix));counter=prediction(np.asarray(scores)[keep]) if keep else None
        influence=base['scores']['cancer']-base['scores']['benign']-(counter['scores']['cancer']-counter['scores']['benign']) if counter else None
        components.append(dict(indices=ix,component_id=str(ix[0]),counterfactual=counter,influence=influence,
            decision_change=counter['prediction']!=base['prediction'] if counter else None))
    return dict(case_id=sid,host_id=sid,split='train',kind='unmodified',requested_percent=0,components=components,baseline=base,
        clean_prediction=base['prediction'],host_truth='cancer' if cancer else 'benign',tile_scores=np.asarray(scores).tolist(),
        annotation_known=[True]*n,annotated_cancer=[cancer]*n,foreign_mask=foreign if foreign is not None else [False]*n,mapping_fraction=1.)


def test_genuine_positive_damage_and_host_only_label_returns_are_not_recovery():
    c=records('genuine',[[.8,.2]]*60+[[.1,.9]]*4,[list(range(60)),list(range(60,64))],True)
    r=study.metric_row(c,[1],'genuine');assert r['hypothetical_clean_damage'] and r['genuine_cancer_components_flagged']==1
    assert r['fragment_hit'] is None and not r['source_exact_error_recovery']
    mixed=records('host',[[.8,.2]]*64+[[.1,.9]]*4,[[0,64,65,66,67],list(range(1,64))],foreign=[False]*64+[True]*4)
    mixed.update(kind='synthetic',donor_id='donor',requested_percent=5,clean_prediction='benign')
    row=study.metric_row(mixed,[0],'host')
    assert row['recovered_new_error'] and row['host_tiles_flagged']==1 and not row['source_exact_error_recovery']
    mixed['components']=[dict(mixed['components'][0],indices=[64,65,66,67]),dict(mixed['components'][1],indices=list(range(64)))]
    assert study.metric_row(mixed,[0],'host')['source_exact_error_recovery']
    mixed['clean_prediction']='cancer'
    assert not study.metric_row(mixed,[0],'host')['source_exact_error_recovery']


def test_matched_baseline_uses_the_same_eligibility_and_gate_is_not_validation():
    f=[dict(eligibility_reasons=['fewer_than_32_comparison_tiles'],stable_score=None),dict(eligibility_reasons=[],stable_score=4.)]
    old=[dict(scores=dict(robust_nn5=100.)),dict(scores=dict(robust_nn5=2.))]
    assert study.method_scores(f,old,'stable32_min3')==[None,4.]
    assert study.method_scores(f,old,'matched_full_context')==[None,2.]
    with pytest.raises(ValueError):study.method_scores(f,old,'choose_the_best')


def test_source_preflight_and_cpu_gate(tmp_path):
    c=study.preflight(CONFIG,file_sha256(CONFIG),PROJECT);assert c['reference_tiles']==32 and c['positive_cases']==24
    c['reference_tiles']=6;p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='scope'):study.preflight(p,file_sha256(p),PROJECT)
    with pytest.raises(RuntimeError,match='CPU Slurm'):study.run(*([None]*5),execute=False)


@pytest.mark.parametrize('oracle_failed',[False,True])
def test_full_72_clean_24_mixture_artificial_runner_keeps_donors_out_of_fit(tmp_path,monkeypatch,oracle_failed):
    c=json.loads(CONFIG.read_text());sources={};clean={};cache={};ids=[f'{i:032x}' for i in range(72)]
    for i,sid in enumerate(ids):
        s=slide(sid,0 if i<24 else 4,64);s.feats=np.tile([1.,0.] if i<24 else [0.,1.],(64,1))
        scores=np.tile([.8,.2] if i<24 else [.1,.9],(64,1));small=5 if i<29 else 4
        parts=[[j] for j in range(small)]+[list(range(small,64))];case=records(sid,scores,parts,i>=24)
        annotations=[dict(mask_available='True',gleason3_fraction=.5 if i>=24 else 0.,gleason4_fraction=0.,gleason5_fraction=0.) for _ in range(64)]
        sources[sid]=dict(slide=s,annotations=annotations);clean[sid]=case
        cache[sid]=[dict(scores=dict(robust_nn5=0.)) for _ in parts]
    trials=[];positives=[]
    for i in range(24):
        hid=ids[i];did=ids[24+i%16];host=clean[hid];scores=host['tile_scores']+clean[did]['tile_scores'][:4]
        parts=[p['indices'][:] for p in host['components']]
        if i==0:parts[0]+=[64,65,66,67]
        else:parts.append([64,65,66,67])
        case=records(hid,scores,parts,False,[False]*64+[True]*4);case.update(case_id=hid+'-5',kind='synthetic',donor_id=did,
            requested_percent=5,clean_prediction='benign',annotated_cancer=[False]*64+[True]*4)
        positives.append(case);cache[case['case_id']]=[dict(scores=dict(robust_nn5=100. if any(j>=64 for j in ix) else 0.)) for ix in parts]
        trials.append(dict(host_id=hid,donor_id=did,split='train',requested_percent=5,donor_indices=[0,1,2,3],donor_tile_ids=['t0','t1','t2','t3'],
            host_tiles=64,foreign_tiles=4,oracle_exact_recovery=True,oracle={},baseline={},synthetic_injection=dict(translation_um=[10000.,0.])))
    assert sum(len(case['components']) for case in list(clean.values())+positives)==556
    if oracle_failed:trials[0]['oracle_exact_recovery']=False
    payloads=dict(cases=list(clean.values())+positives,trials=trials,features=dict(source_kind='real',config_sha256=c['old_feature_config_sha256'],features=cache),manifest={},directories=[],verification={})
    c['inputs']={}
    for key,value in payloads.items():
        path=tmp_path/(key+'.json');path.write_text(json.dumps(value));c['inputs'][key]=dict(path=str(path),sha256=file_sha256(path))
    path=tmp_path/'feature_completion.json';path.write_text(json.dumps(dict(status='verified',artifacts={'feature_checkpoint.json':c['inputs']['features']['sha256']})))
    c['inputs']['feature_completion']=dict(path=str(path),sha256=file_sha256(path));c['output']=str(tmp_path/'out')
    before={sid:slide_identity(s['slide']) for sid,s in sources.items()}
    def load(*args):
        assert args[-1]=='train'
        return list(sources.values()),dict(text_fingerprint='fixture')
    monkeypatch.setattr(study,'load_development',load);monkeypatch.setattr(study,'preflight',lambda *a,**k:c)
    monkeypatch.setenv('SLURM_JOB_ID','software-fixture');monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    if oracle_failed:
        with pytest.raises(RuntimeError,match='oracle receipt'):study.run(CONFIG,'fixture',PROJECT,c['output'],'c'*40,execute=True)
        assert not (Path(c['output'])/'seal.json').exists()
        assert json.loads(sorted((Path(c['output'])/'events').glob('*.json'))[-1].read_text())['status']=='failed'
        assert before=={sid:slide_identity(s['slide']) for sid,s in sources.items()}
        return
    result=study.run(CONFIG,'fixture',PROJECT,c['output'],'c'*40,execute=True)
    assert len(read_sealed(c['output'])[1])==97 and not result['final_test_ready'] and not result['independent_validation']
    assert result['feature_estimates']==1380 and result['source_groups']==48
    for fold in result['folds']:
        assert not set(fold['fit_ids'])&(set(fold['held_ids'])|set(fold['held_donor_ids']))
    for method in study.METHODS:
        m=result['methods'][method]['metrics'];assert m['fragment_hits']==24 and m['source_exact_error_recoveries']==23
        assert m['unmodified_alerts']==0 and m['training_candidate_gate_passed']
    assert before=={sid:slide_identity(s['slide']) for sid,s in sources.items()}
    assert not result['new_model_inference'] and not result['new_contamination_draws'] and result['new_oracle_executions']==0
