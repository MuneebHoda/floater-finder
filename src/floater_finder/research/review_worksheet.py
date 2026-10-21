"""Blank human-review records for the existing unblinded training audit."""
from copy import deepcopy
import json
from pathlib import Path
import re

from ..experiments import file_sha256
from .context_safety import read_sealed
from .contracts import canonical

JUDGMENTS={
    'display_adequacy':('sufficient_for_limited_tile_comparison','insufficient'),
    'native_context_consistency':('compatible','discordant','cannot_assess'),
    'host_context_consistency':('compatible','discordant','cannot_assess'),
    'review_recommendation':('additional_review','no_additional_review','cannot_assess'),
    'needs_more_context':(True,False),
    'rationale':None,
}
REVIEWER=dict(pseudonym=None,role=None,prior_exposure=None,human_entry_attested=False)


def make_worksheet(references,source,source_kind):
    """Project source identities only; never derive human judgments from labels/scores."""
    if (source_kind not in ('fixture','real') or len(references)!=24 or
            len({r['host_id'] for r in references})!=24 or len({r['donor_id'] for r in references})!=16):
        raise ValueError('Exactly 24 training pairs /16 donor slides required')
    for r in references:
        if (any(not re.fullmatch('[a-f0-9]{32}',r[k]) for k in ('host_id','donor_id')) or
                r['audit_page']!='../paired-control-audit-v1/pairs/'+r['host_id']+'.html' or
                any(not re.fullmatch('[a-f0-9]{64}',r[k]) for k in ('audit_pair_sha256','audit_page_sha256'))):
            raise ValueError('Bound local audit-page and source identities required')
    return dict(schema_version=1,purpose='qualitative_development_review',source_kind=source_kind,
        blindness='unblinded_source_truth_and_saved_predictions_visible',source=deepcopy(source),reviewer=deepcopy(REVIEWER),
        physical_isolation_assessment='not_evaluable_from_unassembled_tile_galleries',
        detector_validation=False,clinical_validation=False,final_test_ready=False,automatic_tissue_action='none',
        cases=[dict(review_id=f'P{i+1:02d}',source=deepcopy(r),review_status='not_reviewed',judgments=dict.fromkeys(JUDGMENTS))
            for i,r in enumerate(sorted(references,key=lambda r:r['host_id']))])


def validate_responses(template,responses):
    """Check recording completeness/provenance, never correctness or qualifications."""
    fixed=lambda r:{k:v for k,v in r.items() if k not in ('reviewer','cases')}
    if (set(responses)!=set(template) or canonical(fixed(responses))!=canonical(fixed(template)) or
            len(responses['cases'])!=24 or set(responses['reviewer'])!=set(REVIEWER)):
        raise ValueError('Immutable worksheet scope/source and complete case list required')
    completed=[]
    for blank,row in zip(template['cases'],responses['cases']):
        if (set(row)!=set(blank) or any(row[k]!=blank[k] for k in ('review_id','source')) or set(row['judgments'])!=set(JUDGMENTS)):
            raise ValueError('Original case order, identity and judgment fields required')
        values=row['judgments']
        if row['review_status']=='not_reviewed':
            if any(v is not None for v in values.values()):raise ValueError('Unreviewed cases must have blank judgments')
        elif row['review_status']=='reviewed':
            for key,allowed in JUDGMENTS.items():
                value=values[key]
                if key=='rationale':
                    if not isinstance(value,str) or not 1<=len(value.strip())<=4000:raise ValueError('Reviewer rationale required')
                elif key=='needs_more_context':
                    if type(value) is not bool:raise ValueError('Explicit context request required')
                elif value not in allowed:raise ValueError('Explicit review answer or cannot_assess required')
            completed.append(row)
        else:raise ValueError('Known review status required')
    reviewer=responses['reviewer']
    if reviewer!=REVIEWER or completed:
        if (not isinstance(reviewer['pseudonym'],str) or not 1<=len(reviewer['pseudonym'].strip())<=80 or
                reviewer['role'] not in ('pathologist','pathology_trainee','other') or
                reviewer['prior_exposure'] not in ('has_seen_source_truth_or_predictions','unknown') or
                reviewer['human_entry_attested'] is not True):raise ValueError('Self-reported reviewer identity/role/exposure and human-entry attestation required')
    return dict(status='not_reviewed' if not completed else 'review_record_complete' if len(completed)==24 else 'partially_reviewed',
        recorded_cases=len(completed),pending_cases=24-len(completed),
        cases_requesting_more_context=sum(r['judgments']['needs_more_context'] for r in completed),
        native_context_cannot_assess=sum(r['judgments']['native_context_consistency']=='cannot_assess' for r in completed),
        host_context_cannot_assess=sum(r['judgments']['host_context_consistency']=='cannot_assess' for r in completed),
        correctness_or_reviewer_qualifications_verified=False,detector_validation=False,clinical_validation=False,final_test_ready=False)


def preflight(config_path,expected_sha256,project):
    if file_sha256(config_path)!=expected_sha256:raise ValueError('Review worksheet protocol changed')
    c=json.loads(Path(config_path).read_text());project=Path(project)
    if (c['schema_version']!=1 or c['id']!='panda_expert_review_worksheet_v1' or c['pairs']!=24 or c['split']!='train' or
            c['blindness']!='unblinded_source_truth_and_saved_predictions_visible' or c['human_judgments_generated'] is not False or
            c['new_predictions'] is not False or c['slurm_jobs']!=0 or c['gpu_jobs']!=0):raise ValueError('Fixed blank unblinded training-review scope required')
    required={'src/floater_finder/research/review_worksheet.py','scripts/panda_review_worksheet.py',c['guide'],
        'src/floater_finder/research/context_safety.py','src/floater_finder/research/contracts.py','src/floater_finder/experiments.py'}
    if not required.issubset(c['source_files']):raise ValueError('Complete source/guide freeze required')
    for name,digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name)!=digest:raise ValueError('Frozen worksheet source differs')
    if set(c['inputs'])!={'run.json','seal.json','checkpoints/summary.json'}:raise ValueError('Pinned audit receipts required')
    return c


def source_template(c,protocol_sha256):
    root=Path(c['audit_root'])
    if any(file_sha256(root/name)!=digest for name,digest in c['inputs'].items()):raise ValueError('Pinned original audit receipts differ')
    run,artifacts=read_sealed(root)
    if (run['experiment_id']!='panda_paired_control_audit_v1' or run['source_commit']!=c['audit_source_commit'] or run['split']!='train'):
        raise ValueError('Verified original training audit required')
    summary=json.loads((root/'checkpoints/summary.json').read_text());references=[]
    for name in sorted(artifacts):
        if name=='checkpoints/summary.json':continue
        row=json.loads((root/name).read_text());hid=row['host_id'];public='pairs/'+hid+'.json';page='pairs/'+hid+'.html'
        if (name!='checkpoints/pair-'+hid+'.json' or row['source_kind']!='real' or row['category']!='truth_revealed_saved_control_audit' or
                row['review_alert'] is not None or row['foreignness'] is not None or row['automatic_tissue_action']!='none' or
                row['new_predictions_computed'] is not False or row['saved_oracle_verified'] is not True or
                file_sha256(root/public)!=summary['rendered_file_sha256'][public] or json.loads((root/public).read_text())!=row or
                file_sha256(root/page)!=summary['rendered_file_sha256'][page]):raise ValueError('Saved audit case/page differs')
        references.append(dict(host_id=hid,donor_id=row['donor_id'],case_id=row['case_id'],audit_page='../paired-control-audit-v1/'+page,
            audit_pair_sha256=summary['rendered_file_sha256'][public],audit_page_sha256=summary['rendered_file_sha256'][page]))
    if summary['pairs']!=24 or summary['final_test_ready'] is not False:raise ValueError('Exact completed development audit required')
    return make_worksheet(references,dict(audit_root=str(root),audit_source_commit=c['audit_source_commit'],
        audit_receipts=c['inputs'],worksheet_protocol_sha256=protocol_sha256),'real')


def prepare(config_path,expected_sha256,project,source_commit):
    c=preflight(config_path,expected_sha256,project);out=Path(c['output'])
    if not re.fullmatch('[a-f0-9]{40}',source_commit):raise ValueError('Exact pushed source commit required')
    template=source_template(c,expected_sha256);result=validate_responses(template,template)
    if not out.parent.is_dir() or out.resolve().parent!=Path(c['audit_root']).resolve().parent:
        raise ValueError('Verified sibling output parent required')
    out.mkdir(mode=0o700)  # Existing or partial packets are never replaced.
    with (out/'worksheet.blank.json').open('x') as handle:handle.write(canonical(template)+'\n')
    with (out/'review_guide.md').open('xb') as handle:handle.write((Path(project)/c['guide']).read_bytes())
    if source_template(c,expected_sha256)!=template:raise ValueError('Audit changed during administrative preparation')
    receipt=dict(status='blank_worksheet_prepared',source_commit=source_commit,protocol_sha256=expected_sha256,
        files={name:file_sha256(out/name) for name in ('worksheet.blank.json','review_guide.md')},review_status=result,
        metadata_only=True,new_predictions=False,slurm_jobs_submitted=0,gpu_jobs_submitted=0,human_judgments_generated=0)
    with (out/'preparation.json').open('x') as handle:handle.write(canonical(receipt)+'\n')
    return receipt


def validate_packet(config_path,expected_sha256,project,responses_path):
    c=preflight(config_path,expected_sha256,project);out=Path(c['output']);receipt=json.loads((out/'preparation.json').read_text())
    if (receipt['protocol_sha256']!=expected_sha256 or set(receipt['files'])!={'worksheet.blank.json','review_guide.md'} or
            any(file_sha256(out/name)!=digest for name,digest in receipt['files'].items())):raise ValueError('Original blank packet changed')
    template=json.loads((out/'worksheet.blank.json').read_text())
    if canonical(template)!=canonical(source_template(c,expected_sha256)):raise ValueError('Blank source references changed')
    return validate_responses(template,json.loads(Path(responses_path).read_text()))
