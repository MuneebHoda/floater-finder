"""Artificial contract checks; never measured PANDA results."""
from copy import deepcopy
import json
import numpy as np
import pytest
from test_panda_stress import slide
from floater_finder.research import FollowupCohort, InterventionSpec, apply_intervention
from floater_finder.research.contracts import slide_identity


def inputs():
    h,d = slide('fixture-h',0),slide('fixture-d',4)
    for s in (h,d):
        s.metadata.update(cohort_split='engineering',selection_manifest_sha256='a'*64)
    scope = FollowupCohort('a'*64,'b'*64,tuple((s.metadata['slide_id'],slide_identity(s)) for s in (h,d)),('original-test',))
    return h,d,scope


def test_new_scope_does_not_retag_or_relax_default_development_guard():
    h,d,scope=inputs();before=deepcopy(h.metadata)
    spec=InterventionSpec('s1','cancer','append_legacy',10,1,(0,1))
    with pytest.raises(ValueError,match='development'):apply_intervention(h,d,spec)
    result=apply_intervention(h,d,spec,cohort=scope)
    assert h.metadata==before and result.slide.metadata['cohort_split']=='engineering'
    assert result.verify().metadata==before
    assert np.array_equal(result.restore().feats,h.feats)
    d.metadata['cohort_split']='test'
    with pytest.raises(ValueError,match='whitelist'):apply_intervention(h,d,spec,cohort=scope)


def test_whitelist_full_identity_manifest_and_explicit_exclusions_bind_sources():
    h,d,scope=inputs()
    with pytest.raises(ValueError,match='disjoint'):
        FollowupCohort('a'*64,'b'*64,scope.members,('fixture-d',))
    d.feats=np.roll(d.feats,1,axis=1)
    with pytest.raises(ValueError,match='whitelist'):scope.validate(d)
    h.metadata['selection_manifest_sha256']='c'*64
    with pytest.raises(ValueError,match='whitelist'):scope.validate(h)
    with pytest.raises(TypeError,match='FollowupCohort'):
        apply_intervention(h,d,InterventionSpec('s1','cancer','append_legacy',10,1,(0,1)),cohort={})


def test_known_patient_rejection_and_unknown_patient_disclosure_survive_followup():
    h,d,scope=inputs()
    for s in (h,d):s.metadata.update(patient_id_known=True,patient_id='same-fixture-patient')
    scope=FollowupCohort('a'*64,'b'*64,tuple((s.metadata['slide_id'],slide_identity(s)) for s in (h,d)),())
    with pytest.raises(ValueError,match='same-patient'):
        apply_intervention(h,d,InterventionSpec('s1','cancer','append_legacy',10,1,(0,1)),cohort=scope)
    h,d,scope=inputs()
    result=apply_intervention(h,d,InterventionSpec('s1','cancer','append_legacy',10,1,(0,1)),cohort=scope)
    assert result.slide.metadata['patient_id']=='unknown'
    assert result.slide.metadata['injection']['patient_independence_verified'] is False


def test_fresh_shams_record_actual_append_and_replacement_retains_native_state():
    h,_,scope=inputs()
    appended=apply_intervention(h,h,InterventionSpec('s1','same_source_sham','append_legacy',10,1,(0,1)),cohort=scope)
    assert 'three x-grid steps' in appended.slide.metadata['injection']['placement']
    assert appended.slide.metadata['injection']['occupancy_source_sha256'] is None
    assert not appended.slide.foreign_mask.any()
    replaced=apply_intervention(h,h,InterventionSpec('s1','same_source_sham','replacement',10,1,(0,1),replacement_indices=(0,1)),cohort=scope)
    assert np.array_equal(replaced.slide.feats,h.feats)
    assert json.loads(replaced.audit_json)['altered_count']==2
    assert replaced.restore().metadata==h.metadata
