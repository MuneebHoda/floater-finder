"""Training-only topology/context diagnostics; no predictions or policy selection."""
import json
import os
from pathlib import Path
import numpy as np

from ..detectors.contextual_similarity import anomaly_features
from ..detectors.placement import annotation_arrays
from ..experiments import file_sha256
from ..fragment_dependence import connected_pieces
from ..predictors.data import load_development
from .contracts import ExperimentRun, canonical, slide_identity
from .registry import Registry


def memberships(parts, n, complete=False):
    seen = set();groups = []
    for part in parts:
        ix = part['indices']
        if (not ix or any(type(i) is not int or not 0<=i<n for i in ix) or
                len(set(ix))!=len(ix) or seen.intersection(ix)):
            raise ValueError('Disjoint nonempty valid component indices required')
        seen.update(ix);groups.append(set(ix))
    if complete and seen!=set(range(n)):
        raise ValueError('Sampled components must cover every saved tile')
    return groups


def crosswalk(rgb, sampled, n):
    """Membership correspondence only; missing RGB assignments remain unknown."""
    r = memberships(rgb,n);s = memberships(sampled,n,complete=True)
    counts = [[len(a&b) for b in s] for a in r]
    mapped = set().union(*r) if r else set()
    return dict(rgb_components=len(r),sampled_components=len(s),mapped_tiles=len(mapped),unassigned_tiles=n-len(mapped),
        rgb_components_split_across_sampled=sum(sum(v>0 for v in row)>1 for row in counts),
        sampled_components_merging_rgb=sum(sum(row[j]>0 for row in counts)>1 for j in range(len(s))),
        exact_membership_pairs=sum(a==b for a in r for b in s),overlap_tile_counts=counts,
        complete_physical_piece_boundaries_verified=False)


def context_support(tiles, total):
    if type(tiles) is not int or type(total) is not int or not 0<tiles<=total:
        raise ValueError('Valid nonempty candidate and saved tile counts required')
    remaining = total-tiles
    # Background references exclude self; six outside tiles are needed for five neighbors.
    status = 'empty' if remaining==0 else 'singleton' if remaining==1 else 'partial_nn5' if remaining<6 else 'full_nn5'
    return dict(tile_count=tiles,remaining_tiles=remaining,occupied_fraction=tiles/total,
        majority_of_sampled_bag=tiles>total/2,context_status=status,
        candidate_neighbors=min(5,remaining),background_reference_neighbors=min(5,max(0,remaining-1)))


def describe(slide, parts, scores, kind):
    memberships(parts,len(slide.feats),complete=kind=='sampled')
    if len(parts)!=len(scores):raise ValueError('Cached score/component order differs')
    tile_area = float(np.prod(slide.metadata['tile_size'])/1e6)
    result = []
    for number,(part,score) in enumerate(zip(parts,scores)):
        support = context_support(len(part['indices']),len(slide.feats))
        if ((score is None)!=(support['remaining_tiles']<2) or score is not None and not np.isfinite(score)):
            raise ValueError('Robust-NN5 score availability differs from context support')
        if kind=='rgb_cached' and (not np.isfinite(part['observed_tissue_area_mm2']) or part['observed_tissue_area_mm2']<=0):
            raise ValueError('Finite positive cached RGB area required')
        result.append(dict(component_index=number,indices=part['indices'],score=score,**support,
            occupied_area_mm2=len(part['indices'])*tile_area,
            observed_rgb_tissue_area_mm2=part.get('observed_tissue_area_mm2') if kind=='rgb_cached' else None))
    return result


def ablations(slide, parts, scores, targets, seeds):
    """Largest geometry-defined candidate stays fixed; only outside context changes."""
    n = len(slide.feats);memberships(parts,n)
    selected = min(range(len(parts)),key=lambda i:(-len(parts[i]['indices']),tuple(sorted(parts[i]['indices'])))) if parts else None
    candidate = np.array(parts[selected]['indices'],int) if selected is not None else np.array([],int)
    outside = np.array(sorted(set(range(n))-set(candidate)),int)
    seen = set();rows = []
    for target in targets:
        for seed in seeds:
            row = dict(target_context_tiles=target,seed=seed,component_index=selected,
                full_context_tiles=len(outside),full_score=scores[selected] if selected is not None else None)
            if selected is None or target>len(outside):
                rows.append(dict(row,status='no_mapped_candidate' if selected is None else 'insufficient_context',
                    realized_context_tiles=None,score=None,delta=None,reference_indices=None,duplicate_reference_subset=None));continue
            reference = np.sort(np.random.default_rng(seed).permutation(outside)[:target])
            key = tuple(reference.tolist());duplicate = key in seen;seen.add(key)
            if target==len(outside):
                score = scores[selected];status = 'full_context_reused'
            else:
                ix = np.r_[candidate,reference]
                score = anomaly_features(slide.feats[ix],slide.coords[ix],
                    [dict(indices=list(range(len(candidate))))])[0]['scores']['robust_nn5']
                status = 'reference_subsampled'
            rows.append(dict(row,status=status,realized_context_tiles=target,score=score,
                delta=float(score-scores[selected]),reference_indices=reference.tolist(),duplicate_reference_subset=duplicate))
    return rows


def audit_slide(slide, rgb_case, cached, targets, seeds):
    """Feature construction precedes the evaluation-only annotation join."""
    m = slide.metadata
    if (m['coordinate_units']!='microns' or m['microns_per_unit']!=1 or
            np.shape(m['tile_size'])!=(2,) or np.shape(m['tile_step'])!=(2,) or
            not np.isfinite([m['tile_size'],m['tile_step']]).all() or
            np.any(np.asarray(m['tile_size'])<=0) or np.any(np.asarray(m['tile_step'])<m['tile_size'])):
        raise ValueError('Recorded nonoverlapping physical tile geometry required')
    n = len(slide.feats);rgb = [dict(indices=p['indices'],observed_tissue_area_mm2=p['observed_tissue_area_mm2']) for p in rgb_case['components']]
    rgb_groups = memberships(rgb,n)
    if (len(rgb_case['tile_scores'])!=n or len(rgb_case['foreign_mask'])!=n or len(cached)!=len(rgb) or any(rgb_case['foreign_mask']) or
            not np.isclose(sum(len(p) for p in rgb_groups)/n,rgb_case['mapping_fraction'],rtol=0,atol=1e-12)):
        raise ValueError('Original RGB mapping/cache alignment differs')
    sampled = [dict(indices=ix.tolist()) for ix in connected_pieces(slide.coords,m['tile_step'],max_gap_tiles=0)]
    sampled_features = anomaly_features(slide.feats,slide.coords,sampled)
    rgb_scores = [r['scores']['robust_nn5'] for r in cached]
    sampled_scores = [r['scores']['robust_nn5'] for r in sampled_features]
    descriptions = {kind:describe(slide,parts,scores,kind) for kind,parts,scores in
        [('rgb_cached',rgb,rgb_scores),('sampled',sampled,sampled_scores)]}
    unmapped=set(range(n))-(set().union(*rgb_groups) if rgb_groups else set())
    for parts in descriptions.values():
        for part in parts:
            inside=len(unmapped&set(part['indices']))
            part.update(unassigned_rgb_tiles_in_candidate=inside,unassigned_rgb_tiles_in_remaining_context=len(unmapped)-inside)
    thinned = {kind:ablations(slide,parts,scores,targets,seeds) for kind,parts,scores in
        [('rgb_cached',rgb,rgb_scores),('sampled',sampled,sampled_scores)]}
    return dict(tiles=n,mapping_fraction=rgb_case['mapping_fraction'],crosswalk=crosswalk(rgb,sampled,n),
        components=descriptions,context_ablations=thinned,classification_predictions_computed=False,
        complete_physical_piece_boundaries_verified=False)


def summarize(rows):
    topologies = [];sensitivity = []
    for kind in ('rgb_cached','sampled'):
        parts = [dict(p,host_id=r['host_id']) for r in rows for p in r['components'][kind]]
        by_status = []
        for status in ('empty','singleton','partial_nn5','full_nn5'):
            group = [p for p in parts if p['context_status']==status];scores = [p['score'] for p in group if p['score'] is not None]
            by_status.append(dict(status=status,components=len(group),unique_slides=len({p['host_id'] for p in group}),
                majority_components=sum(p['majority_of_sampled_bag'] for p in group),
                score_range=[min(scores),max(scores)] if scores else None))
        topologies.append(dict(topology=kind,slides=len(rows),components=len(parts),context=by_status,
            native_annotation_positive_components=sum(p['evaluation_native_annotation_positive_tiles']>0 for p in parts),
            annotation_unknown_components=sum(p['evaluation_annotation_known_tiles']<p['tile_count'] for p in parts)))
        targets=sorted({a['target_context_tiles'] for r in rows for a in r['context_ablations'][kind]})
        for target in targets:
            values = [dict(a,host_id=r['host_id']) for r in rows for a in r['context_ablations'][kind] if a['target_context_tiles']==target]
            eligible = [a for a in values if a['realized_context_tiles'] is not None]
            grouped = {}
            for a in eligible:grouped.setdefault(a['host_id'],[]).append(a['delta'])
            means = [float(np.mean(v)) for v in grouped.values()]
            sensitivity.append(dict(topology=kind,target_context_tiles=target,planned=len(values),eligible=len(eligible),
                excluded=len(values)-len(eligible),unique_slides=len(grouped),
                unique_reference_subsets=sum(not a['duplicate_reference_subset'] for a in eligible),
                full_context_reused=sum(a['status']=='full_context_reused' for a in eligible),
                mean_delta_equal_slide=float(np.mean(means)) if means else None,
                median_absolute_slide_mean_delta=float(np.median(np.abs(means))) if means else None))
    return dict(slides=len(rows),topologies=topologies,context_sensitivity=sensitivity,
        slides_rgb_split_by_grid=sum(r['crosswalk']['rgb_components_split_across_sampled']>0 for r in rows),
        slides_grid_merges_rgb=sum(r['crosswalk']['sampled_components_merging_rgb']>0 for r in rows),
        slides_with_unassigned_rgb_tiles=sum(r['crosswalk']['unassigned_tiles']>0 for r in rows),
        slides_below_old_rgb_mapping_coverage=sum(r['mapping_fraction']<.9 for r in rows),
        classification_predictions_computed=False,thresholds_fitted=False,component_rule_changed=False,
        final_test_predictions_computed=False,independent_validation=False,
        interpretation='Training-only geometry/context diagnostics; no foreignness or clinical performance estimate')


def preflight(config_path, expected_sha256, project, check_inputs=False):
    if file_sha256(config_path)!=expected_sha256:raise ValueError('Frozen topology-context protocol changed')
    c=json.loads(Path(config_path).read_text());project=Path(project)
    if (c['schema_version']!=1 or c['experiment_id']!='panda_topology_context_v1' or c['split']!='train' or
            c['slides']!=72 or c['context_sizes']!=[2,5,6,16,32] or c['seeds']!=[20261026,20261027,20261028] or
            c['maximum_ablation_records']!=2160 or c['classification_predictions'] or c['fit_thresholds'] or
            c['resources']!=dict(cpus=2,memory_gb=8,maximum_minutes=20,gpu=0)):
        raise ValueError('Fixed training-only context-audit scope required')
    for name,digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name)!=digest:
            raise ValueError('Frozen context-audit source differs: '+name)
    required={'src/floater_finder/'+n for n in ['research/topology_context.py','research/contracts.py','research/registry.py',
        'detectors/contextual_similarity.py','detectors/placement.py','fragment_dependence.py','predictors/data.py']}
    required|={'scripts/panda_topology_context.py','scripts/slurm/panda_topology_context.sbatch'}
    if not required.issubset(c['source_files']):raise ValueError('Incomplete context-audit source freeze')
    if check_inputs:
        for entry in c['inputs'].values():
            if file_sha256(entry['path'])!=entry['sha256']:raise ValueError('Pinned original development input changed')
        if not Path(c['encoded_root']).is_dir() or not Path(c['output']).parent.is_dir():
            raise ValueError('Verified original embedding and output roots required')
        if Path(c['output']).exists():raise FileExistsError('Preserve existing context-audit output')
    return c


def run(config_path, expected_sha256, project, output, source_commit, execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Explicit bounded CPU Slurm execution required')
    c=preflight(config_path,expected_sha256,project,check_inputs=True)
    if Path(output).resolve()!=Path(c['output']).resolve():raise ValueError('Exact new context-audit output required')
    inp={name:entry['path'] for name,entry in c['inputs'].items()}
    sources,receipt=load_development(inp['manifest'],inp['directories'],c['encoded_root'],inp['verification'],'train')
    if len(sources)!=72:raise ValueError('Exactly 72 original training slides required')
    all_cases=json.loads(Path(inp['cases']).read_text())
    if any(r['split']=='test' for r in all_cases):raise ValueError('Source case catalog must exclude final tests')
    clean=[r for r in all_cases if r['split']=='train' and r['kind']=='unmodified']
    cases={r['host_id']:r for r in clean};ids={s['slide'].metadata['slide_id'] for s in sources}
    if len(cases)!=len(clean) or set(cases)!=ids:raise ValueError('Exact training case membership required')
    cache=json.loads(Path(inp['features']).read_text())
    completion=json.loads(Path(inp['feature_completion']).read_text())
    if (cache['source_kind']!='real' or cache['config_sha256']!=c['old_feature_config_sha256'] or
            completion['status']!='verified' or completion['artifacts']['feature_checkpoint.json']!=c['inputs']['features']['sha256']):
        raise ValueError('Verified original feature cache required')
    identities={s['slide'].metadata['slide_id']:slide_identity(s['slide']) for s in sources}
    registry=Registry(output,ExperimentRun(c['experiment_id'],c['hypothesis'],source_commit,canonical(c),
        c['inputs']['manifest']['sha256'],'train',sources[0]['slide'].metadata['model']['checkpoint_sha256'],
        receipt['text_fingerprint'],canonical(c['resources'])))
    registry.status('planned');registry.status('running',slurm_job_id=os.environ['SLURM_JOB_ID']);rows=[]
    try:
        for source in sources:
            slide=source['slide'];sid=slide.metadata['slide_id'];case=cases[sid]
            result=audit_slide(slide,case,cache['features'][case['case_id']],c['context_sizes'],c['seeds'])
            known,cancer=annotation_arrays(source['annotations'],source['annotations'],[],[],len(slide.feats))
            if not np.array_equal(known,case['annotation_known']) or not np.array_equal(cancer,case['annotated_cancer']):
                raise ValueError('Native annotation evaluation provenance differs')
            for parts in result['components'].values():
                for part in parts:
                    part.update(evaluation_annotation_known_tiles=int(known[part['indices']].sum()),
                        evaluation_native_annotation_positive_tiles=int(cancer[part['indices']].sum()))
            result.update(host_id=sid,source_identity=identities[sid]);rows.append(result)
            registry.checkpoint('slide-'+sid,result)
            print(json.dumps(dict(stage='slide_audited',slides=len(rows))),flush=True)
        if sum(len(a) for r in rows for a in r['context_ablations'].values())!=c['maximum_ablation_records']:
            raise RuntimeError('Frozen context-audit workload changed')
        if any(slide_identity(s['slide'])!=identities[s['slide'].metadata['slide_id']] for s in sources):
            raise RuntimeError('Original source artifacts mutated')
        summary=summarize(rows);registry.checkpoint('summary',summary)
        registry.status('verified',validation=True,interpretation=summary['interpretation']);return summary
    except BaseException as exc:
        registry.status('failed',interpretation=type(exc).__name__+': '+str(exc));raise
