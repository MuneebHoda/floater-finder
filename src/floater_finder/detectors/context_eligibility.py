"""Truth-free numeric comparison eligibility, never a foreign-tissue classifier."""
import math


def assess_context(candidate_tiles, total_tiles, diagnostic_score):
    """A conservative engineering gate; six references do not establish stability.

    The majority veto concerns saved tile occupancy, not actual biopsy area.
    Supported comparisons still abstain from foreignness/review decisions.
    """
    if (type(candidate_tiles) is not int or type(total_tiles) is not int or
            not 0 < candidate_tiles <= total_tiles):
        raise ValueError('Valid nonempty candidate and saved tile counts required')
    remaining = total_tiles-candidate_tiles
    if (diagnostic_score is not None and
            (type(diagnostic_score) not in (int, float) or not math.isfinite(diagnostic_score)) or
            (diagnostic_score is None) != (remaining < 2)):
        raise ValueError('Finite diagnostic score availability must match NN5 support')
    reasons = []
    if remaining < 6:
        reasons.append('fewer_than_six_comparison_tiles')
    if 2*candidate_tiles > total_tiles:
        reasons.append('candidate_is_majority_of_sampled_bag')
    eligible = not reasons
    return dict(schema_version=1, contract='numeric_context_eligibility_v1',
        candidate_tiles=candidate_tiles, comparison_tiles=remaining,
        status='supported_numeric_comparison' if eligible else 'abstain', reasons=reasons,
        eligible_for_numeric_comparison=eligible,
        diagnostic_score=diagnostic_score, comparison_score=diagnostic_score if eligible else None,
        score_stability_validated=False, physical_boundaries_verified=False,
        review_status='abstain_unvalidated_foreignness_policy', review_alert=None,
        foreignness=None, automatic_tissue_action='none')
