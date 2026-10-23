"""Truth-blind component mapping and model-agnostic review of saved interventions."""
import numpy as np
from ..panda_topology import add_observed_tiles, overview_components
from .contextual_similarity import anomaly_features


def memberships(parts):
    """Compare tile membership, not raster component labels which can renumber."""
    return sorted(tuple(sorted(p['indices'])) for p in parts)


def map_components(mask, coords_um, size_um, pixel_um, mode, altered=(), rgbs=()):
    if mode not in ('clean', 'append_legacy', 'near_tissue', 'within_region_context', 'replacement'):
        raise ValueError('Unknown mapping mode')
    if mode in ('append_legacy', 'near_tissue', 'within_region_context'):
        mask = add_observed_tiles(mask, np.asarray(coords_um)[list(altered)], size_um, pixel_um, rgbs)
    elif len(rgbs):
        raise ValueError('Native carrier mapping does not render donor pixels')
    return overview_components(mask, coords_um, size_um, pixel_um, purity=.8)


def review_features(feats, coords_um, parts, references, scorer, labels):
    """No annotations, source identity, foreign mask or altered-index input."""
    features = anomaly_features(feats, coords_um, parts, references, distant_um=500.)
    before = scorer(feats)
    margin = before['scores'][labels[1]]-before['scores'][labels[0]]
    records = []
    for part, feature in zip(parts, features):
        keep = np.ones(len(feats), bool); keep[part['indices']] = False
        counter = scorer(feats[keep]) if keep.any() else None
        records.append(dict(part, **{k:v for k,v in feature.items() if k != 'centroid'},
            counterfactual=counter,
            influence=None if counter is None else float(margin-counter['scores'][labels[1]]+counter['scores'][labels[0]]),
            decision_change=None if counter is None else before['prediction'] != counter['prediction']))
    return before, records


def annotation_arrays(host_rows, donor_rows, altered, donor_indices, n):
    """Follow the actual vector's source annotation, including native shams."""
    def values(rows):
        known = [str(r['mask_available']).lower() == 'true' for r in rows]
        cancer = [k and sum(float(r['gleason'+str(g)+'_fraction']) for g in (3,4,5)) > 0
                  for r,k in zip(rows,known)]
        return known, cancer
    hk, hc = values(host_rows); dk, dc = values(donor_rows)
    if n < len(hk) or len(altered) != len(donor_indices):
        raise ValueError('Aligned annotation provenance required')
    known = np.zeros(n,bool); cancer = np.zeros(n,bool)
    known[:len(hk)] = hk; cancer[:len(hc)] = hc
    known[list(altered)] = np.asarray(dk)[list(donor_indices)]
    cancer[list(altered)] = np.asarray(dc)[list(donor_indices)]
    return known, cancer


def evaluate(feats, parts, flags, foreign, known, cancer, scorer, clean, before, truth, mapping):
    """Truth enters only here, after mapping, feature construction and shortlisting."""
    foreign, known, cancer = (np.asarray(a,bool) for a in (foreign,known,cancer))
    if any(a.shape != (len(feats),) for a in (foreign,known,cancer)):
        raise ValueError('Aligned evaluation arrays required')
    removed = np.zeros(len(feats),bool)
    for i in flags: removed[parts[i]['indices']] = True
    after = scorer(feats[~removed]) if (~removed).any() else None
    correct = clean['prediction'] == truth
    induced = bool(correct and foreign.any() and before['prediction'] != truth)
    native = known & cancer & ~foreign
    genuine = [i for i,p in enumerate(parts) if native[p['indices']].any()]
    return dict(alerted=bool(flags), alerts=len(flags), foreign_tiles=int(foreign.sum()),
        foreign_flagged=int((foreign & removed).sum()), fragment_hit=bool((foreign & removed).any()) if foreign.any() else None,
        complete_fragment=bool((foreign & removed).sum() == foreign.sum()) if foreign.any() else None,
        host_tiles=int((~foreign).sum()), host_tiles_flagged=int((~foreign & removed).sum()),
        genuine_cancer_components=len(genuine), genuine_cancer_components_flagged=sum(i in flags for i in genuine),
        genuine_cancer_tiles_flagged=int((native & removed).sum()), annotated_cancer_present=bool(native.any()),
        originally_correct=correct, initially_incorrect=not correct, newly_induced_error=induced,
        prediction_changed=before['prediction'] != clean['prediction'],
        recovered_new_error=bool(induced and after is not None and after['prediction'] == truth),
        unmodified_correct=bool(not foreign.any() and correct),
        hypothetical_clean_damage=bool(not foreign.any() and correct and (after is None or after['prediction'] != truth)),
        empty_after_hypothetical_filter=after is None, flagged_component_indices=list(flags),
        filtered_prediction=None if after is None else after['prediction'], topology_abstained=mapping < .9)


PAIR_FIELDS = ('task','condition','control','host_id','donor_id','seed','requested_percent')


def paired_groups(rows):
    """Eligibility uses recorded case keys only, before any detector scores exist."""
    groups = {}
    for row in rows:
        if row['mode'] == 'replacement': continue
        key = tuple(row[k] for k in PAIR_FIELDS)
        group = groups.setdefault(key,{})
        if row['mode'] in group: raise ValueError('Duplicate placement in paired group')
        group[row['mode']] = row['case_id']
    modes = {'append_legacy','near_tissue','within_region_context'}
    return [dict(zip(PAIR_FIELDS,key),cases=value,complete_triplet=set(value)==modes)
            for key,value in sorted(groups.items())]
