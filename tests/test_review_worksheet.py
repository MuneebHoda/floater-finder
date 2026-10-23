"""Artificial administrative records; no tissue images or expert assessments."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import pytest
from PIL import Image

from floater_finder.artifacts import Slide
from floater_finder.experiments import file_sha256
from floater_finder.research import review_worksheet as worksheet
from floater_finder.research.contracts import ExperimentRun,canonical
from floater_finder.research.registry import Registry

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_expert_review_worksheet_v1.json'


def references():
    return [dict(host_id=f'{i:032x}',donor_id=f'{100+i%16:032x}',case_id=f'fixture-{i}',
        audit_page=f'../paired-control-audit-v1/pairs/{i:032x}.html',audit_pair_sha256='a'*64,audit_page_sha256='b'*64) for i in range(24)]


def blank():return worksheet.make_worksheet(references(),dict(artificial_fixture=True),'fixture')


def reviewed(template,number=1):
    r=deepcopy(template);r['reviewer']=dict(pseudonym='fixture-reviewer',role='other',prior_exposure='unknown',human_entry_attested=True)
    for row in r['cases'][:number]:
        row.update(review_status='reviewed',judgments=dict(display_adequacy='insufficient',native_context_consistency='cannot_assess',
            host_context_consistency='cannot_assess',review_recommendation='cannot_assess',needs_more_context=True,rationale='Artificial answer: more context needed.'))
    return r


def test_blank_records_never_turn_saved_truth_into_human_judgments():
    b=blank();assert all(row['review_status']=='not_reviewed' and all(v is None for v in row['judgments'].values()) for row in b['cases'])
    result=worksheet.validate_responses(b,b)
    assert result['status']=='not_reviewed' and result['recorded_cases']==0 and result['pending_cases']==24
    assert result['detector_validation'] is result['clinical_validation'] is result['final_test_ready'] is False


def test_cannot_assess_is_complete_and_partial_records_keep_denominators():
    b=blank();result=worksheet.validate_responses(b,reviewed(b))
    assert result['status']=='partially_reviewed' and result['recorded_cases']==1 and result['pending_cases']==23
    assert result['cases_requesting_more_context']==result['native_context_cannot_assess']==result['host_context_cannot_assess']==1
    assert not result['correctness_or_reviewer_qualifications_verified']


def test_all_recorded_answers_still_leave_scientific_gates_closed():
    b=blank();result=worksheet.validate_responses(b,reviewed(b,24))
    assert result['status']=='review_record_complete' and result['recorded_cases']==24
    assert not any(result[k] for k in ('detector_validation','clinical_validation','final_test_ready','correctness_or_reviewer_qualifications_verified'))


@pytest.mark.parametrize('damage',['source','missing_case','order','blinding','detector_claim','typed_claim','rationale','attestation','answer','unreviewed','missing_role'])
def test_invalid_or_misleading_records_are_rejected(damage):
    b=blank();r=reviewed(b)
    if damage=='source':r['cases'][0]['source']['audit_pair_sha256']='c'*64
    elif damage=='missing_case':r['cases'].pop()
    elif damage=='order':r['cases'][0],r['cases'][1]=r['cases'][1],r['cases'][0]
    elif damage=='blinding':r['blindness']='blinded'
    elif damage=='detector_claim':r['detector_validation']=True
    elif damage=='typed_claim':r['clinical_validation']=0
    elif damage=='rationale':r['cases'][0]['judgments']['rationale']=' '
    elif damage=='attestation':r['reviewer']['human_entry_attested']=False
    elif damage=='answer':r['cases'][0]['judgments']['host_context_consistency']='foreign'
    elif damage=='missing_role':r['reviewer']['role']=None
    else:r['cases'][0]['review_status']='not_reviewed'
    with pytest.raises(ValueError):worksheet.validate_responses(b,r)


@pytest.mark.parametrize('damage',['remote_url','path_escape','hash','host_reuse','donor_count'])
def test_reference_paths_and_cohort_identity_are_fixed(damage):
    refs=references()
    if damage=='remote_url':refs[0]['audit_page']='https://example.com/track'
    elif damage=='path_escape':refs[0]['host_id']='../escape'
    elif damage=='hash':refs[0]['audit_page_sha256']='bogus'
    elif damage=='host_reuse':refs[0]['host_id']=refs[1]['host_id']
    else:refs[0]['donor_id']='f'*32
    with pytest.raises(ValueError):worksheet.make_worksheet(refs,{},'fixture')


def audit_fixture(tmp_path):
    c=json.loads(CONFIG.read_text());root=tmp_path/'paired-control-audit-v1';(root/'pairs').mkdir(parents=True)
    registry=Registry(root,ExperimentRun('panda_paired_control_audit_v1','Artificial administrative fixture',c['audit_source_commit'],canonical({}),
        'fixture-dataset','train','fixture-checkpoint','fixture-text',canonical({})))
    registry.status('planned');registry.status('running');rendered={}
    for ref in references():
        hid=ref['host_id']
        row=dict(host_id=hid,donor_id=ref['donor_id'],case_id=ref['case_id'],source_kind='real',category='truth_revealed_saved_control_audit',
            review_alert=None,foreignness=None,automatic_tissue_action='none',new_predictions_computed=False,saved_oracle_verified=True)
        # Simulate historical real-input trust markers; all fixture records remain artificial.
        for ext,text in [('json',canonical(row)),('html','<p>Artificial audit page; no image.</p>')]:
            path=root/'pairs'/(hid+'.'+ext);path.write_text(text);rendered['pairs/'+path.name]=file_sha256(path)
        registry.checkpoint('pair-'+hid,row)
    registry.checkpoint('summary',dict(pairs=24,final_test_ready=False,rendered_file_sha256=rendered));registry.status('verified',validation=True)
    c.update(audit_root=str(root),output=str(tmp_path/'expert-review-worksheet-v1'),inputs={n:file_sha256(root/n) for n in c['inputs']})
    config=tmp_path/'config.json';config.write_text(json.dumps(c));return c,config


def test_administrative_packet_has_no_image_array_job_or_human_work(tmp_path,monkeypatch):
    c,config=audit_fixture(tmp_path);original={str(p):p.read_bytes() for p in Path(c['audit_root']).rglob('*') if p.is_file()}
    fail=lambda *a,**k:pytest.fail('No image/array, subprocess/job, or expert assessment allowed')
    monkeypatch.setattr(Slide,'load',fail);monkeypatch.setattr(Image,'open',fail);monkeypatch.setattr(subprocess,'run',fail);monkeypatch.setattr(subprocess,'check_output',fail)
    result=worksheet.prepare(config,file_sha256(config),PROJECT,'c'*40);out=Path(c['output'])
    assert result['status']=='blank_worksheet_prepared' and result['human_judgments_generated']==result['slurm_jobs_submitted']==result['gpu_jobs_submitted']==0
    assert result['review_status']['recorded_cases']==0 and result['review_status']['pending_cases']==24
    template=json.loads((out/'worksheet.blank.json').read_text());response=out/'worksheet.fixture.json';response.write_text(canonical(reviewed(template)))
    assert worksheet.validate_packet(config,file_sha256(config),PROJECT,response)['recorded_cases']==1
    before={p.name:p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):worksheet.prepare(config,file_sha256(config),PROJECT,'c'*40)
    assert before=={p.name:p.read_bytes() for p in out.iterdir()}
    assert original=={str(p):p.read_bytes() for p in Path(c['audit_root']).rglob('*') if p.is_file()}


def test_changed_blank_packet_or_audit_stops_validation(tmp_path):
    c,config=audit_fixture(tmp_path);worksheet.prepare(config,file_sha256(config),PROJECT,'c'*40);out=Path(c['output'])
    response=out/'worksheet.fixture.json';response.write_text((out/'worksheet.blank.json').read_text())
    with (out/'worksheet.blank.json').open('a') as f:f.write(' ')
    with pytest.raises(ValueError,match='blank packet'):worksheet.validate_packet(config,file_sha256(config),PROJECT,response)
    with (Path(c['audit_root'])/'pairs'/('0'*32+'.html')).open('a') as f:f.write('changed')
    with pytest.raises(ValueError,match='case/page'):worksheet.source_template(c,file_sha256(config))


def test_frozen_source_preflight_and_new_scope_guard(tmp_path):
    c=worksheet.preflight(CONFIG,file_sha256(CONFIG),PROJECT);assert c['slurm_jobs']==c['gpu_jobs']==0
    c['human_judgments_generated']=True;p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='blank unblinded'):worksheet.preflight(p,file_sha256(p),PROJECT)
