"""Read-only dependence reports from saved predictions, without foreignness labels."""
from copy import deepcopy
from html import escape
import math
import re

from .detectors.context_eligibility import assess_context


def saved_prediction(value):
    if not isinstance(value, dict) or set(value) != {'prediction', 'scores'}:
        raise ValueError('Saved two-class prediction required')
    scores = value['scores']
    if (set(scores) != {'benign', 'cancer'} or any(type(v) not in (int, float) or
            not math.isfinite(v) for v in scores.values()) or
            value['prediction'] != ('cancer' if scores['cancer'] > scores['benign'] else 'benign')):
        raise ValueError('Finite saved cosine scores with original tie rule required')
    return deepcopy(value)


def evidence_from_case(case):
    """Allowlist excludes annotation, host grade, tile scores and foreign truth."""
    fields = ('component_id', 'indices', 'bbox_um', 'observed_tissue_area_mm2',
        'isolation_bbox_lower_bound_mm', 'status', 'counterfactual', 'decision_change',
        'cancer_decision_change', 'influence')
    return dict(host_id=case['host_id'], case_id=case['case_id'], baseline=deepcopy(case['baseline']),
        components=[{k:deepcopy(p[k]) for k in fields} for p in case['components']])


def build_report(evidence, topology, safety, provenance):
    """Do not suppress saved decision dependence when visual context abstains."""
    if (provenance['source_kind'] not in ('real', 'fixture') or
            set(evidence) != {'host_id', 'case_id', 'baseline', 'components'} or
            evidence['host_id'] != topology['host_id'] or evidence['host_id'] != safety['host_id'] or
            topology['source_identity'] != safety['source_identity'] or
            safety['review_alert'] is not None or safety['foreignness'] is not None or
            safety['automatic_tissue_action'] != 'none'):
        raise ValueError('Aligned truth-free saved evidence and abstention provenance required')
    baseline = saved_prediction(evidence['baseline']); n = topology['tiles']
    raw = evidence['components']; geometry = topology['components']['rgb_cached']; gates = safety['components']['rgb_cached']
    if len(raw) != len(geometry) or len(raw) != len(gates):
        raise ValueError('Exact cached RGB component alignment required')
    parts = []
    for index, (p, g, s) in enumerate(zip(raw, geometry, gates)):
        gate = assess_context(g['tile_count'], n, g['score'])
        bbox = p['bbox_um']; isolation = p['isolation_bbox_lower_bound_mm']
        if (p['indices'] != g['indices'] or len(p['indices']) != g['tile_count'] or
                g['component_index'] != index or s['component_index'] != index or s['eligibility'] != gate or
                p['observed_tissue_area_mm2'] != g['observed_rgb_tissue_area_mm2'] or
                g['observed_rgb_tissue_area_mm2'] != s['observed_rgb_tissue_area_mm2'] or
                g['occupied_area_mm2'] != s['occupied_area_mm2'] or
                not math.isfinite(g['occupied_area_mm2']) or g['occupied_area_mm2'] <= 0 or
                not math.isfinite(p['observed_tissue_area_mm2']) or p['observed_tissue_area_mm2'] <= 0 or
                len(bbox) != 4 or any(not math.isfinite(v) or v < 0 for v in bbox) or
                bbox[2] <= bbox[0] or bbox[3] <= bbox[1] or
                isolation is not None and (not math.isfinite(isolation) or isolation < 0)):
            raise ValueError('Saved membership, physical geometry or context gate differs')
        remaining = n-g['tile_count']; empty = remaining == 0
        if empty:
            if (p['status'] != 'not_evaluable_empty_counterfactual' or
                    any(p[k] is not None for k in ('counterfactual', 'decision_change', 'cancer_decision_change', 'influence'))):
                raise ValueError('Empty exclusion must stay unevaluable')
            counter = None; influence = None; changes = None
        else:
            counter = saved_prediction(p['counterfactual'])
            changes = counter['prediction'] != baseline['prediction']
            influence = (baseline['scores']['cancer']-baseline['scores']['benign'] -
                (counter['scores']['cancer']-counter['scores']['benign']))
            if (p['status'] != 'evaluable' or type(p['decision_change']) is not bool or
                    p['decision_change'] != changes or type(p['cancer_decision_change']) is not bool or
                    p['cancer_decision_change'] != (baseline['prediction'] == 'cancer' and counter['prediction'] == 'benign') or
                    type(p['influence']) not in (int, float) or not math.isfinite(p['influence']) or
                    not math.isclose(influence, p['influence'], rel_tol=1e-10, abs_tol=1e-12)):
                raise ValueError('Saved decision dependence differs from cached predictions')
        unknown_candidate = g['unassigned_rgb_tiles_in_candidate']
        unknown_context = g['unassigned_rgb_tiles_in_remaining_context']
        if (unknown_candidate != s['unassigned_rgb_tiles_in_candidate'] or
                unknown_context != s['unassigned_rgb_tiles_in_comparison']):
            raise ValueError('Unknown mapping counts differ')
        parts.append(dict(component_index=index, component_id=p['component_id'],
            tile_indices=list(p['indices']), tile_count=g['tile_count'], bbox_um=list(bbox),
            occupied_tile_area_mm2=g['occupied_area_mm2'], observed_rgb_area_mm2=p['observed_tissue_area_mm2'],
            isolation_bbox_lower_bound_mm=isolation, context=gate,
            unassigned_rgb_candidate_tiles=unknown_candidate, unassigned_rgb_comparison_tiles=unknown_context,
            counterfactual=dict(status='not_evaluable_empty_exclusion' if empty else 'saved_prediction',
                remaining_tile_count=remaining, result=counter), decision_change=changes,
            signed_cancer_margin_influence=influence, review_alert=None, foreignness=None,
            automatic_tissue_action='none'))
    return dict(schema_version=1, category='review_only_dependence_report', source_kind=provenance['source_kind'],
        host_id=evidence['host_id'], case_id=evidence['case_id'], scorer=deepcopy(provenance['scorer']),
        baseline=baseline, tile_count=n, topology='cached_rgb_220_chroma10_proxy', components=parts,
        component_order='original_cached_order_no_ranking', provenance=deepcopy(provenance),
        review_alert=None, foreignness=None, automatic_tissue_action='none', new_predictions_computed=False,
        limitations=['Decision dependence does not establish foreignness; genuine cancer can be decisive.',
            'Numeric context support is not validated score stability or biological reference suitability.',
            'RGB bounds and isolation lower bounds do not verify complete physical pieces.',
            'No image panels or calibrated review policy; no automatic tissue exclusion.',
            'Historical zero-shot cosine scores are not probabilities or clinical diagnoses.'])


def _page(title, body):
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<title>'+escape(title)+'</title><style>body{font:16px system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#172b3a}'
        'table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{text-align:left;border-bottom:1px solid #c9d4dd;padding:.6rem}'
        'aside{padding:1rem;background:#edf3f6}details{border:1px solid #c9d4dd;padding:1rem;margin:1rem 0}'
        'summary{cursor:pointer}code{overflow-wrap:anywhere}</style><body><h1>'+escape(title)+'</h1>'+body+'</body></html>')


def render_html(report):
    """No scripts, remote resources, truth panels, removal actions or hidden ranking."""
    e = lambda value: escape(str(value))
    baseline = report['baseline']
    body = '<aside><strong>Research report. Preserve all tissue.</strong> Foreignness is not established; review decisions are unset.'
    if report['source_kind'] == 'fixture': body += ' <strong>Artificial software fixture; no scientific evidence.</strong>'
    body += '</aside><p>Scorer: '+e(report['scorer']['name'])+'. Cosine scores are not probabilities.</p>'
    body += '<p>Saved baseline: <strong>'+e(baseline['prediction'])+'</strong> (benign '+e(baseline['scores']['benign'])+', cancer '+e(baseline['scores']['cancer'])+').</p>'
    for p in report['components']:
        change = 'Unevaluable empty exclusion' if p['decision_change'] is None else 'Decision changes' if p['decision_change'] else 'No saved decision change'
        g = p['context']; result = p['counterfactual']['result']
        body += '<details><summary>Component '+e(p['component_id'])+' — '+change+'; '+e(p['tile_count'])+' tiles</summary>'
        body += '<p>Hypothetical exclusion: '+(e(result['prediction']) if result else 'unevaluable; no prediction')+'. Original tissue and baseline preserved.</p>'
        if result: body += '<p>Saved counterfactual cosine scores: benign '+e(result['scores']['benign'])+', cancer '+e(result['scores']['cancer'])+'.</p>'
        body += '<p>Numeric comparison: '+e(g['status'])+'. '+e(', '.join(g['reasons']))+'</p>'
        body += '<p>Outside tiles: '+e(g['comparison_tiles'])+'; unknown RGB assignments in comparison: '+e(p['unassigned_rgb_comparison_tiles'])+'.</p>'
        body += '<p>Diagnostic morphology score: '+e(g['diagnostic_score'])+'; supported comparison score: '+e(g['comparison_score'])+'. Score stability remains unvalidated.</p>'
        body += '<p>RGB bounding box in µm (not a verified boundary): '+e(p['bbox_um'])+'.</p>'
        body += '<p>Occupied tile footprint: '+e(p['occupied_tile_area_mm2'])+' mm²; observed RGB area: '+e(p['observed_rgb_area_mm2'])+' mm²; isolation lower bound: '+e(p['isolation_bbox_lower_bound_mm'])+' mm.</p></details>'
    if not report['components']: body += '<p>No mapped RGB component; dependence is unavailable. This is not a negative finding.</p>'
    body += '<h2>Limitations</h2><ul>'+''.join('<li>'+e(v)+'</li>' for v in report['limitations'])+'</ul>'
    return _page('Floater Finder — '+report['host_id'], body)


def render_index(reports):
    body = '<aside>Research dependence summaries only. No calibrated review alerts, no foreignness labels, and no tissue removal.</aside>'
    body += '<table><tr><th>Slide</th><th>Saved baseline</th><th>Decision-changing components</th><th>Numeric abstentions</th></tr>'
    for r in reports:
        if not re.fullmatch('[A-Za-z0-9_-]+', r['host_id']):
            raise ValueError('Safe report file identity required')
        sid = escape(r['host_id']); parts = r['components']
        body += '<tr><td><a href="reports/'+sid+'.html">'+sid+'</a></td><td>'+escape(r['baseline']['prediction'])+'</td><td>'+str(sum(p['decision_change'] is True for p in parts))+'</td><td>'+str(sum(not p['context']['eligible_for_numeric_comparison'] for p in parts))+'</td></tr>'
    return _page('Floater Finder — saved training dependence', body+'</table>')
