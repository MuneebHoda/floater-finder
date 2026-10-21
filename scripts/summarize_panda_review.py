#!/usr/bin/env python3
"""Describe saved development measurements; never load embeddings or test inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
from floater_finder.experiments import file_sha256
from floater_finder.panda_final import clustered_ratio_interval
from floater_finder.panda_review import wilson


def summarize(selection, metrics, topology, cases, output):
    selected=json.loads(Path(selection).read_text());rows=json.loads(Path(metrics).read_text())
    observed=json.loads(Path(topology).read_text())
    if file_sha256(cases)!=selected['component_cases_sha256']:raise ValueError('Measurement identity differs')
    measurements=json.loads(Path(cases).read_text())
    if any(c['split'] not in ('train','calibration') for c in measurements):raise ValueError('Development only')
    rule=selected['selected_rule'];result={}
    for split in ('train','calibration'):
        methods={}
        for name,all_rows in rows.items():
            group=[r for r in all_rows if r['split']==split];clean=[r for r in group if r['kind']=='unmodified'];positive=[r for r in group if r['foreign_tiles']]
            m=selected['comparison'][name][split];dose=[]
            for percent in (.5,1,2,5,10):
                d=[r for r in positive if r['requested_percent']==percent];n=sum(r['originally_correct'] for r in d);errors=sum(r['newly_induced_error'] for r in d)
                dose.append(dict(percent=percent,unique_hosts=len(d),originally_correct=n,initially_incorrect=len(d)-n,
                    prediction_changes=sum(r['prediction_changed'] for r in d),new_errors=errors,new_error_rate=errors/n if n else None,
                    new_error_wilson95=wilson(errors,n),fragment_hits=sum(bool(r['fragment_hit']) for r in d),
                    fragment_hit_wilson95=wilson(sum(bool(r['fragment_hit']) for r in d),len(d))))
            methods[name]=dict(unmodified_alert_wilson95=wilson(m['unmodified_alerts'],m['unmodified_slides']),
                clean_damage_wilson95=wilson(m['clean_hypothetical_damage'],m['clean_originally_correct']),
                genuine_cancer_slide_flag_wilson95=wilson(m['genuine_cancer_slides_flagged'],m['genuine_cancer_slides']),
                clean_mask_unknown_slides=sum(not r['mask_known'] for r in clean),unique_positive_hosts=len({r['host_id'] for r in positive}),
                unique_new_error_hosts=len({r['host_id'] for r in positive if r['newly_induced_error']}),
                fragment_recall_host_bootstrap=clustered_ratio_interval([r|{'trial':1} for r in positive],'fragment_hit','trial'),
                tile_recall_host_bootstrap=clustered_ratio_interval(positive,'foreign_flagged','foreign_tiles'),
                recovery_host_bootstrap=clustered_ratio_interval(positive,'recovered_new_error','newly_induced_error'),by_dose=dose)
        mixed=[c for c in measurements if c['split']==split and c['kind']=='synthetic']
        funnel={key:0 for key in ('positive_trials','mapped_foreign_component','visual_pass','visual_and_influence_pass','combined_pass')}
        for c in mixed:
            funnel['positive_trials']+=1
            if c['mapping_fraction']<.9:continue
            foreign=np.asarray(c['foreign_mask'],bool)
            parts=[p for p in c['components'] if p['status']=='evaluable' and foreign[p['indices']].any()]
            visual=[p for p in parts if p['visual']>rule['visual_threshold']]
            influence=[p for p in visual if p['influence']>=rule['influence']]
            combined=[p for p in influence if p['observed_tissue_area_mm2']<=rule['max_area_mm2'] and p['isolation_bbox_lower_bound_mm'] is not None and p['isolation_bbox_lower_bound_mm']>=rule['min_isolation_mm']]
            for name,items in [('mapped_foreign_component',parts),('visual_pass',visual),('visual_and_influence_pass',influence),('combined_pass',combined)]:funnel[name]+=bool(items)
        t=[r for r in observed if r['split']==split]
        result[split]=dict(methods=methods,foreign_truth_diagnostic_funnel=funnel,topology=dict(slides=len(t),
            old_single_component=sum(r['old_sampled_components']==1 for r in t),new_single_component=sum(r['new_observed_components']==1 for r in t),
            formerly_single_now_multiple=sum(r['old_sampled_components']==1 and r['new_observed_components']>1 for r in t),
            mapping_abstentions=sum(r['mapping_fraction']<.9 for r in t),minimum_mapping=min(r['mapping_fraction'] for r in t),
            mean_mapping=float(np.mean([r['mapping_fraction'] for r in t])),
            minimum_sensitivity_agreement=min(r['sensitivity_pairwise_membership_agreement'] for r in t),
            mean_sensitivity_agreement=float(np.mean([r['sensitivity_pairwise_membership_agreement'] for r in t]))))
    payload=dict(source_kind='real',category='Development-only description of frozen saved measurements',test_predictions_computed=False,
        patient_independence_verified=False,selection_changed=False,splits=result,
        confidence_interpretation='Slide/host resampling conditional on fixed donors. Repeated doses and random controls are not independent patients. Zero observed alerts do not establish a population rate below 10%.',
        source_sha256={str(p):file_sha256(p) for p in (selection,metrics,topology,cases)},script_sha256=file_sha256(__file__))
    target=Path(output)
    with target.open('x') as f:json.dump(payload,f,indent=2);f.write('\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('selection','metrics','topology','cases','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();summarize(a.selection,a.metrics,a.topology,a.cases,a.output)
