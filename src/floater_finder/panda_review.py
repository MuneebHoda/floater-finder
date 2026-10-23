"""Frozen-CONCH component review signals. Annotation and injection truth enter metrics only."""
import hashlib
from statistics import NormalDist
import numpy as np
from .scoring import pool


def prediction(scores):
    values=pool(np.asarray(scores),'top5pct');names=('benign','cancer')
    return dict(prediction=names[int(np.argmax(values))],scores=dict(zip(names,values.tolist())))


def component_features(features,scores,components):
    features=np.asarray(features);scores=np.asarray(scores)
    if features.ndim!=2 or scores.shape!=(len(features),2) or not np.isfinite(features).all():raise ValueError('Aligned finite features/scores required')
    baseline=prediction(scores);margin=baseline['scores']['cancer']-baseline['scores']['benign'];records=[]
    for component in components:
        indices=np.asarray(component['indices'],dtype=int)
        record=dict(component)
        if not len(indices) or len(set(indices))!=len(indices) or np.any(indices<0) or np.any(indices>=len(features)):raise ValueError('Invalid component indices')
        keep=np.ones(len(features),bool);keep[indices]=False
        if not keep.any():
            record.update(status='not_evaluable_empty_counterfactual',visual=None,influence=None,decision_change=None,cancer_decision_change=None,counterfactual=None)
        else:
            reference=features[keep];k=min(5,len(reference));distances=[]
            for start in range(0,len(indices),64):
                similarity=np.einsum('id,jd->ij',features[indices[start:start+64]],reference,optimize=False)
                nearest=np.partition(similarity,len(reference)-k,axis=1)[:,-k:]
                distances.extend((1-np.clip(nearest,-1,1).mean(axis=1)).tolist())
            counter=prediction(scores[keep]);counter_margin=counter['scores']['cancer']-counter['scores']['benign']
            record.update(status='evaluable',visual=float(np.median(distances)),reference_neighbors=k,
                influence=float(margin-counter_margin),decision_change=baseline['prediction']!=counter['prediction'],
                cancer_decision_change=baseline['prediction']=='cancer' and counter['prediction']=='benign',counterfactual=counter)
        records.append(record)
    return baseline,records


def flagged_components(case,rule):
    if case['mapping_fraction']<.9:return []
    flags=[]
    for i,p in enumerate(case['components']):
        if p['status']!='evaluable':continue
        visual=p['visual']>rule.get('visual_threshold',float('inf'))
        influence=p['cancer_decision_change'] if rule.get('influence')=='flip' else p['influence']>=rule.get('influence',float('inf'))
        spatial=p['observed_tissue_area_mm2']<=rule.get('max_area_mm2',float('inf')) and p['isolation_bbox_lower_bound_mm'] is not None and p['isolation_bbox_lower_bound_mm']>=rule.get('min_isolation_mm',float('inf'))
        kind=rule['kind']
        if ((kind=='visual' and visual) or (kind=='decision' and p['decision_change']) or
                (kind=='spatial' and spatial) or (kind=='combined' and visual and influence and spatial)):
            flags.append(i)
    return flags


def matched_draws(case,flags,repeats=20,seed=20261021):
    bins=[.05,.25,1.]
    valid=[i for i,p in enumerate(case['components']) if p['status']=='evaluable']
    result=[]
    for draw in range(repeats):
        digest=hashlib.sha256(f"{seed}/{case['case_id']}/{draw}".encode()).digest();rng=np.random.default_rng(int.from_bytes(digest[:8],'little'));selected=[]
        for index in flags:
            size_bin=np.searchsorted(bins,case['components'][index]['observed_tissue_area_mm2'])
            eligible=[j for j in valid if j not in selected and np.searchsorted(bins,case['components'][j]['observed_tissue_area_mm2'])==size_bin]
            if not eligible:raise ValueError('Matched control cannot preserve component burden')
            selected.append(int(rng.choice(eligible)))
        result.append(selected)
    return result


def evaluate_flags(case,flags):
    n=len(case['tile_scores']);removed=np.zeros(n,bool)
    for i in flags:removed[case['components'][i]['indices']]=True
    truth=np.asarray(case['foreign_mask'],bool);known=np.asarray(case['annotation_known'],bool);cancer=np.asarray(case['annotated_cancer'],bool)
    after=prediction(np.asarray(case['tile_scores'])[~removed]) if (~removed).any() else None
    clean=case['clean_prediction'];before=case['baseline']['prediction'];host_truth=case['host_truth']
    originally_correct=clean==host_truth;induced=originally_correct and before!=host_truth and truth.any()
    real_cancer_components=[i for i,p in enumerate(case['components']) if np.any(cancer[p['indices']]&known[p['indices']]&~truth[p['indices']])]
    return dict(alerted=bool(flags),alerts=len(flags),foreign_tiles=int(truth.sum()),foreign_flagged=int((truth&removed).sum()),
        fragment_hit=bool((truth&removed).any()) if truth.any() else None,
        complete_fragment=bool((truth&removed).sum()==truth.sum()) if truth.any() else None,
        host_tiles=int((~truth).sum()),host_tiles_flagged=int((~truth&removed).sum()),
        genuine_cancer_components=len(real_cancer_components),genuine_cancer_components_flagged=sum(i in flags for i in real_cancer_components),
        genuine_cancer_tiles_flagged=int((removed&cancer&known&~truth).sum()),
        mask_known=bool(known.any()),annotated_cancer_present=bool((known&cancer&~truth).any()),
        originally_correct=bool(originally_correct),initially_incorrect=not bool(originally_correct),
        newly_induced_error=bool(induced),prediction_changed=before!=clean,
        recovered_new_error=bool(induced and after is not None and after['prediction']==host_truth),
        hypothetical_clean_damage=bool(not truth.any() and originally_correct and (after is None or after['prediction']!=host_truth)),
        unmodified_correct=bool(not truth.any() and originally_correct),empty_after_hypothetical_filter=after is None,
        baseline_prediction=before,clean_prediction=clean,filtered_prediction=after['prediction'] if after else None,
        flagged_component_indices=list(flags),topology_abstained=case['mapping_fraction']<.9)


def ratio(a,b):return a/b if b else None


def summarize(rows):
    clean=[r for r in rows if r['kind']=='unmodified'];positive=[r for r in rows if r['foreign_tiles']>0]
    genuine=[r for r in clean if r['annotated_cancer_present']]
    induced=[r for r in positive if r['newly_induced_error']]
    return dict(unmodified_slides=len(clean),unmodified_alerts=sum(r['alerted'] for r in clean),
        unmodified_alert_rate=ratio(sum(r['alerted'] for r in clean),len(clean)),
        mean_components_per_unmodified_slide=ratio(sum(r['alerts'] for r in clean),len(clean)),
        maximum_components_per_unmodified_slide=max((r['alerts'] for r in clean),default=0),
        genuine_cancer_slides=len(genuine),genuine_cancer_slides_flagged=sum(r['genuine_cancer_components_flagged']>0 for r in genuine),
        genuine_cancer_slide_flag_rate=ratio(sum(r['genuine_cancer_components_flagged']>0 for r in genuine),len(genuine)),
        genuine_cancer_components=sum(r['genuine_cancer_components'] for r in clean),
        genuine_cancer_components_flagged=sum(r['genuine_cancer_components_flagged'] for r in clean),
        positive_trials=len(positive),foreign_tiles=sum(r['foreign_tiles'] for r in positive),foreign_tiles_flagged=sum(r['foreign_flagged'] for r in positive),
        foreign_tile_recall=ratio(sum(r['foreign_flagged'] for r in positive),sum(r['foreign_tiles'] for r in positive)),
        fragment_recall=ratio(sum(r['fragment_hit'] for r in positive),len(positive)),
        complete_fragment_recall=ratio(sum(r['complete_fragment'] for r in positive),len(positive)),
        new_errors=len(induced),new_error_recoveries=sum(r['recovered_new_error'] for r in induced),
        new_error_recovery_rate=ratio(sum(r['recovered_new_error'] for r in induced),len(induced)),
        clean_originally_correct=sum(r['unmodified_correct'] for r in clean),
        clean_hypothetical_damage=sum(r['hypothetical_clean_damage'] for r in clean),
        clean_damage_rate=ratio(sum(r['hypothetical_clean_damage'] for r in clean),sum(r['unmodified_correct'] for r in clean)),
        host_tiles_flagged=sum(r['host_tiles_flagged'] for r in positive),
        unmodified_topology_abstentions=sum(r['topology_abstained'] for r in clean))


def acceptable(metrics,budgets):
    return (metrics['unmodified_alert_rate'] is not None and metrics['unmodified_alert_rate']<=budgets['unmodified_alert_rate'] and
        metrics['mean_components_per_unmodified_slide']<=budgets['components_per_slide'] and
        (metrics['genuine_cancer_slide_flag_rate'] or 0)<=budgets['genuine_cancer_slide_flag_rate'] and
        (metrics['clean_damage_rate'] or 0)<=budgets['clean_damage_rate'])


def wilson(successes,total):
    if not total:return None
    z=NormalDist().inv_cdf(.975);p=successes/total;d=1+z*z/total
    c=(p+z*z/(2*total))/d;h=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [float(max(0,c-h)),float(min(1,c+h))]
