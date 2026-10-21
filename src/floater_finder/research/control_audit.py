"""Truth-revealed saved-control audit, separate from blind reviewer reports."""
from copy import deepcopy
import csv
import hashlib
from html import escape
import io
import json
import math
import os
from pathlib import Path
import re
import statistics
from PIL import Image

from ..detectors.context_eligibility import assess_context
from ..experiments import file_sha256
from ..review_previews import select_examples
from ..review_report import saved_prediction, _page
from .context_safety import read_sealed
from .contracts import ExperimentRun, canonical
from .preview_export import tile_source
from .registry import Registry


def same_prediction(a,b):
    saved_prediction(a);saved_prediction(b)
    if a['prediction']!=b['prediction'] or any(not math.isclose(a['scores'][k],b['scores'][k],abs_tol=1e-7,rel_tol=1e-6) for k in ('benign','cancer')):
        raise ValueError('Saved prediction provenance differs')


def component_audit(case,features):
    """Retain cached dependence and diagnostics; provenance truth is evaluation only."""
    baseline=saved_prediction(case['baseline']);n=len(case['tile_scores']);seen=set();rows=[]
    if (len(features)!=len(case['components']) or any(len(case[k])!=n for k in ('foreign_mask','annotation_known','annotated_cancer'))):
        raise ValueError('Aligned saved case/features/annotation vectors required')
    for p,f in zip(case['components'],features):
        ix=p['indices']
        if not ix or any(type(i) is not int or not 0<=i<n for i in ix) or len(set(ix))!=len(ix) or seen.intersection(ix):
            raise ValueError('Disjoint original component membership required')
        seen.update(ix);remaining=n-len(ix);counter=p['counterfactual']
        if remaining:
            counter=saved_prediction(counter)
            change=counter['prediction']!=baseline['prediction']
            influence=baseline['scores']['cancer']-baseline['scores']['benign']-(counter['scores']['cancer']-counter['scores']['benign'])
            if (p['status']!='evaluable' or type(p['decision_change']) is not bool or p['decision_change']!=change or
                    not math.isclose(p['influence'],influence,rel_tol=1e-10,abs_tol=1e-12)):
                raise ValueError('Cached component dependence differs')
        elif (p['status']!='not_evaluable_empty_counterfactual' or counter is not None or p['decision_change'] is not None):
            raise ValueError('Empty exclusion must remain unevaluable')
        gate=assess_context(len(ix),n,f['scores']['robust_nn5'])
        donor=sum(case['foreign_mask'][i] for i in ix)
        rows.append(dict(component_id=p['component_id'],indices=ix,tiles=len(ix),cached_counterfactual=counter,
            decision_change=p['decision_change'],context=gate,bbox_um=p['bbox_um'],
            observed_rgb_area_mm2=p['observed_tissue_area_mm2'],
            evaluation_appended_donor_tiles=donor,evaluation_host_tiles=len(ix)-donor,
            evaluation_native_cancer_tiles=sum(case['annotation_known'][i] and case['annotated_cancer'][i] and not case['foreign_mask'][i] for i in ix),
            review_alert=None,foreignness=None,automatic_tissue_action='none'))
    if not math.isclose(len(seen)/n,case['mapping_fraction'],rel_tol=0,abs_tol=1e-12):
        raise ValueError('Saved mapping coverage differs')
    return rows


def assemble_pair(mixed,host,donor,trial,features,host_source,donor_source):
    """Validate the old append experiment without materializing embeddings or rerunning it."""
    hr,hm=host_source['rows'],host_source['metadata'];dr,dm=donor_source['rows'],donor_source['metadata']
    n=len(hr);ix=trial['donor_indices'];k=len(ix);injection=trial['synthetic_injection']
    if (trial['oracle_exact_recovery'] is not True or trial['oracle']!=trial['baseline']):
        raise RuntimeError('Saved oracle recovery receipt failed; stop audit')
    if (any(c['split']!='train' for c in (mixed,host,donor)) or trial['split']!='train' or mixed['kind']!='synthetic' or
            any(c['kind']!='unmodified' or any(c['foreign_mask']) for c in (host,donor)) or
            mixed['host_id']!=host['host_id'] or mixed['donor_id']!=donor['host_id'] or
            trial['host_id']!=host['host_id'] or trial['donor_id']!=donor['host_id'] or host['host_id']==donor['host_id'] or
            hm['isup_grade']!=0 or dm['isup_grade'] not in (1,4,5) or
            float(mixed['requested_percent'])!=5 or float(trial['requested_percent'])!=5 or
            len(host['tile_scores'])!=n or len(donor['tile_scores'])!=len(dr) or
            not ix or any(type(i) is not int or not 0<=i<len(dr) for i in ix) or len(set(ix))!=k or k!=(5*n+99)//100 or
            trial['host_tiles']!=n or trial['foreign_tiles']!=k or
            mixed['foreign_mask']!=[False]*n+[True]*k or mixed['tile_scores']!=host['tile_scores']+[donor['tile_scores'][i] for i in ix] or
            mixed['annotation_known']!=host['annotation_known']+[donor['annotation_known'][i] for i in ix] or
            mixed['annotated_cancer']!=host['annotated_cancer']+[donor['annotated_cancer'][i] for i in ix] or
            trial['donor_tile_ids']!=[dr[i]['tile_id'] for i in ix]):
        raise ValueError('Exact old 5-percent training source/append provenance required')
    for key in ('tile_size','tile_step','coordinate_units','microns_per_unit'):
        if hm[key]!=dm[key]:raise ValueError('Host/donor recorded physical geometry differs')
    if (injection['kind']!='synthetic_PANDA_S1_embedding_contamination' or injection['donor_indices']!=ix or
            injection['donor_tile_ids']!=trial['donor_tile_ids'] or injection['donor_slide_id']!=donor['host_id'] or
            injection['foreign_count']!=k or injection['original_host_count']!=n or injection['patient_independence_verified'] is not False or
            not math.isclose(trial['realized_percent'],100*k/n,abs_tol=1e-12,rel_tol=0)):
        raise ValueError('Recorded synthetic intervention provenance differs')
    cells={(int(dr[i]['grid_x']),int(dr[i]['grid_y'])) for i in ix};seen={next(iter(cells))};queue=list(seen)
    while queue:
        x,y=queue.pop()
        for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if q in cells and q not in seen:seen.add(q);queue.append(q)
    if len(cells)!=k or seen!=cells:raise ValueError('Original donor selection must stay four-connected')
    sy=min(float(r['y']) for r in hr);step=hm['tile_step'];ys=[float(r['y']) for r in hr]
    expected=[max(float(r['x']) for r in hr)+3*step[0]-min(float(dr[i]['x']) for i in ix),
        sy+round((statistics.median(ys)-sy)/step[1])*step[1]-min(float(dr[i]['y']) for i in ix)]
    translation=injection['translation_um']
    if len(translation)!=2 or any(not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8) for a,b in zip(translation,expected)):
        raise ValueError('Recorded synthetic translation differs from original placement rule')
    fractions=[]
    for i in ix:
        value=sum(float(dr[i][f'gleason{g}_fraction']) for g in (3,4,5))
        if not donor['annotation_known'][i] or not donor['annotated_cancer'][i] or not math.isfinite(value) or not .1<=value<=1+1e-10:
            raise ValueError('Selected original donor requires verified native cancer-rich annotation')
        fractions.append(value)
    area=dm['tile_size'][0]*dm['tile_size'][1]/1e6
    if (not math.isclose(trial['foreign_footprint_area_mm2'],k*area,rel_tol=1e-9,abs_tol=1e-12) or
            not math.isclose(trial['annotated_cancer_area_mm2'],sum(fractions)*area,rel_tol=1e-9,abs_tol=1e-12)):
        raise ValueError('Original physical/annotated donor areas differ')
    same_prediction(host['baseline'],trial['baseline']['top5pct']);same_prediction(mixed['baseline'],trial['contaminated']['top5pct'])
    native=component_audit(donor,features[donor['case_id']]);synthetic=component_audit(mixed,features[mixed['case_id']])
    overlap=[dict(p,evaluation_selected_fragment_overlap=len(set(p['indices'])&set(ix))) for p in native if set(p['indices'])&set(ix)]
    hostxy=[(float(r['x']),float(r['y'])) for r in hr];donorxy=[(float(r['x']),float(r['y'])) for r in dr]
    examples=select_examples(ix,donorxy)
    return dict(category='truth_revealed_saved_control_audit',host_id=host['host_id'],donor_id=donor['host_id'],case_id=mixed['case_id'],
        native_host_baseline=deepcopy(host['baseline']),native_donor_baseline=deepcopy(donor['baseline']),synthetic_baseline=deepcopy(mixed['baseline']),
        requested_percent=5,realized_percent=trial['realized_percent'],host_tiles=n,donor_tiles=k,donor_indices=ix,
        saved_translation_um=translation,synthetic_donor_bag_indices=list(range(n,n+k)),
        native_donor_overlap_components=overlap,synthetic_components=synthetic,
        evaluation_unmapped_donor_tiles=k-sum(p['evaluation_appended_donor_tiles'] for p in synthetic),
        evaluation_native_fragment_unmapped_tiles=k-sum(p['evaluation_selected_fragment_overlap'] for p in overlap),
        originally_correct_host=host['baseline']['prediction']=='benign',
        prediction_changed=mixed['baseline']['prediction']!=host['baseline']['prediction'],
        newly_induced_host_label_error=host['baseline']['prediction']=='benign' and mixed['baseline']['prediction']=='cancer',
        saved_oracle_verified=True,new_oracle_executed=False,
        gallery_indices=dict(native_fragment=examples,synthetic_fragment=examples,
            native_context=select_examples(set(range(len(dr)))-set(ix),donorxy),host_context=select_examples(range(n),hostxy)),
        review_alert=None,foreignness=None,automatic_tissue_action='none',new_predictions_computed=False,
        limitations=['Known provenance is disclosed for an audit, not inferred by a detector.',
            'Synthetic append/translation is an embedding-coordinate construction, not a real contaminated WSI or an image composite.',
            'Overlapping native RGB components may contain more tissue than the selected donor fragment; their exclusions are not fragment-only oracle removals.',
            'Annotations and slide grades have different scopes. Distinct slides are not verified distinct patients.',
            'Galleries are geometry-only source examples, not spatial reconstructions or complete biopsy coverage.'])


def copy_tile(source,index,output,assets,budget):
    """Small audit-specific copier keeps the previously frozen preview helper unchanged."""
    row=source['rows'][index];directory=source['directory'].resolve();path=directory/row['path'];sid=source['metadata']['slide_id']
    if not re.fullmatch('[a-f0-9]{32}',sid):raise ValueError('Bound original source slide ID required')
    name=f'tiles/{sid}-t{index:04d}.png';expected=source['hashes'][row['tile_id']]
    if name in assets:
        if assets[name]['sha256']!=expected:raise ValueError('Reused source PNG identity differs')
        return dict(asset_path=name,source_tile_id=row['tile_id'],source_index=index,sha256=expected,
            source_xy_um=[float(row['x']),float(row['y'])],field_um_xy=source['metadata']['tile_size'])
    if Path(row['path']).name!=row['path'] or path.resolve().parent!=directory or path.suffix!='.png':raise ValueError('Bound source PNG path required')
    with path.open('rb') as handle:data=handle.read(1024*1024+1)
    if len(data)>1024*1024 or hashlib.sha256(data).hexdigest()!=expected or sum(p['bytes'] for p in assets.values())+len(data)>budget:
        raise ValueError('Source PNG checksum/byte budget differs')
    with Image.open(io.BytesIO(data)) as image:
        pixels=source['metadata']['export_pixels']
        if type(pixels) is not int or not 1<=pixels<=512 or image.format!='PNG' or image.mode!='RGB' or image.size!=(pixels,pixels):
            raise ValueError('Bounded recorded PNG format/shape required')
        image.load()
    with (output/name).open('xb') as handle:handle.write(data)
    assets[name]=dict(sha256=expected,bytes=len(data),source_path=str(path.resolve()))
    return copy_tile(source,index,output,assets,budget)


def render_pair(pair):
    e=lambda v:escape(str(v))
    def gallery(role):
        if any(not re.fullmatch(r'tiles/[a-f0-9]{32}-t[0-9]{4}\.png',t['asset_path']) for t in pair['galleries'][role]):
            raise ValueError('Safe local PNG paths required')
        return '<div class="gallery">'+''.join('<figure><img loading="lazy" width="224" height="224" src="../'+e(t['asset_path'])+'" alt="Unchanged source tile '+e(t['source_index'])+'"><figcaption>Source tile '+e(t['source_index'])+'; x/y µm '+e(t['source_xy_um'])+'; field µm '+e(t['field_um_xy'])+'</figcaption></figure>' for t in pair['galleries'][role])+'</div>'
    def table(parts):
        body='<table><tr><th>RGB proxy</th><th>Tiles</th><th>Saved exclusion</th><th>Decision change</th><th>Numeric context</th><th>Known appended donor tiles</th></tr>'
        for p in parts:
            body+='<tr><td>'+e(p['component_id'])+'</td><td>'+e(p['tiles'])+'</td><td>'+e(p['cached_counterfactual']['prediction'] if p['cached_counterfactual'] else 'unevaluable')+'</td><td>'+e(p['decision_change'])+'</td><td>'+e(p['context']['status'])+'</td><td>'+e(p['evaluation_appended_donor_tiles'])+'</td></tr>'
        return body+'</table>'
    body='<aside><strong>Known provenance shown for a research audit.</strong> Source labels are not detector predictions. Preserve all tissue.</aside>'
    body+='<p>Same donor PNGs are shown in both contexts. This is an embedding-coordinate construction, not an observed contaminated WSI or a spatial image reconstruction.</p>'
    body+='<p>Requested/realized dose: '+e(pair['requested_percent'])+'% / '+e(pair['realized_percent'])+'%; '+e(pair['donor_tiles'])+' appended donor tiles. Review/foreignness decisions remain unset.</p><div class="contexts"><section><h2>Native donor context</h2><p>Saved baseline: '+e(pair['native_donor_baseline']['prediction'])+'.</p>'+gallery('native_fragment')
    body+='<h3>Other native source examples</h3>'+gallery('native_context')+'<h3>Native components overlapping the chosen donor set</h3>'+table(pair['native_donor_overlap_components'])+'</section>'
    body+='<section><h2>Known synthetic context</h2><p>Host baseline → saved mixture: '+e(pair['native_host_baseline']['prediction'])+' → '+e(pair['synthetic_baseline']['prediction'])+'.</p>'+gallery('synthetic_fragment')
    body+='<h3>Host source examples</h3>'+gallery('host_context')+'<h3>All saved mixture components</h3>'+table(pair['synthetic_components'])+'<p>Unmapped appended donor tiles: '+e(pair['evaluation_unmapped_donor_tiles'])+'.</p></section></div>'
    body+='<ul>'+''.join('<li>'+e(v)+'</li>' for v in pair['limitations'])+'</ul>'
    return _page('Known-provenance comparison — '+pair['host_id'],body).replace('</style>','.contexts{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1rem}.gallery{display:flex;flex-wrap:wrap;gap:.5rem}.gallery figure{width:130px;margin:0}.gallery img{width:130px;height:auto;max-width:100%}.gallery figcaption{font-size:.75rem;overflow-wrap:anywhere}table{font-size:.8rem}</style>',1)


def summarize(pairs):
    native={(p['donor_id'],r['component_id']):r for p in pairs for r in p['native_donor_overlap_components']}
    synthetic=[r for p in pairs for r in p['synthetic_components']]
    return dict(pairs=len(pairs),unique_host_slides=len({p['host_id'] for p in pairs}),unique_donor_slides=len({p['donor_id'] for p in pairs}),
        originally_correct_hosts=sum(p['originally_correct_host'] for p in pairs),initially_incorrect_hosts=sum(not p['originally_correct_host'] for p in pairs),
        prediction_changes=sum(p['prediction_changed'] for p in pairs),newly_induced_host_label_errors=sum(p['newly_induced_host_label_error'] for p in pairs),
        saved_oracle_receipts_verified=sum(p['saved_oracle_verified'] for p in pairs),new_oracle_executions=0,
        unique_overlapping_native_components=len(native),unique_decisive_overlapping_native_components=sum(p['decision_change'] is True for p in native.values()),
        synthetic_rgb_components=len(synthetic),synthetic_decisive_components=sum(p['decision_change'] is True for p in synthetic),
        decisive_components_with_appended_donor=sum(p['decision_change'] is True and p['evaluation_appended_donor_tiles']>0 for p in synthetic),
        decisive_components_without_appended_donor=sum(p['decision_change'] is True and p['evaluation_appended_donor_tiles']==0 for p in synthetic),
        appended_donor_tile_instances=sum(p['donor_tiles'] for p in pairs),unmapped_appended_donor_tile_instances=sum(p['evaluation_unmapped_donor_tiles'] for p in pairs),
        new_predictions_computed=False,thresholds_fitted=False,detector_recall=None,review_alert_rate=None,patient_independence_verified=False,
        final_test_ready=False,interpretation='Known-provenance saved-training control audit; no new inference, contamination draw, policy fit or independent validation')


def preflight(config_path,expected_sha256,project,check_inputs=False):
    if file_sha256(config_path)!=expected_sha256:raise ValueError('Frozen paired-control protocol changed')
    c=json.loads(Path(config_path).read_text());project=Path(project)
    if (c['schema_version']!=1 or c['experiment_id']!='panda_paired_control_audit_v1' or c['split']!='train' or
            c['percent']!=5 or c['pairs']!=24 or c['unique_donors']!=16 or c['maximum_image_references']!=384 or
            c['maximum_png_bytes']!=64*1024*1024 or c['new_predictions'] or c['fit_thresholds'] or
            c['resources']!=dict(cpus=2,memory_gb=4,maximum_minutes=5,gpu=0)):
        raise ValueError('Fixed original-training saved-control scope required')
    required={'src/floater_finder/'+p for p in ('research/control_audit.py','review_report.py','review_previews.py',
        'research/preview_export.py','research/context_safety.py','research/contracts.py','research/registry.py','detectors/context_eligibility.py')}
    required|={'scripts/panda_paired_controls.py','scripts/slurm/panda_paired_controls.sbatch','reports/panda_s1_trials_23065666.json'}
    if not required.issubset(c['source_files']):raise ValueError('Incomplete paired-control source freeze')
    for name,digest in c['source_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or file_sha256(project/name)!=digest:raise ValueError('Frozen audit source differs: '+name)
    if c['inputs']['trials']['sha256']!=c['source_files']['reports/panda_s1_trials_23065666.json']:
        raise ValueError('Original committed stress-trial identity required')
    for key,relative in [('native_run','run.json'),('native_seal','seal.json'),('native_summary','checkpoints/summary.json')]:
        if Path(c['inputs'][key]['path'])!=Path(c['native_root'])/relative:raise ValueError('Pinned native gallery receipt paths differ')
    if check_inputs:
        for e in c['inputs'].values():
            if file_sha256(e['path'])!=e['sha256']:raise ValueError('Pinned control-audit input differs')
        if Path(c['output']).exists():raise FileExistsError('Preserve old audit outputs')
        if not Path(c['output']).parent.is_dir():raise ValueError('Verified output parent required')
    return c


def run(config_path,expected_sha256,project,output,source_commit,execute=False):
    if not execute or not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):raise RuntimeError('Explicit bounded CPU Slurm execution required')
    c=preflight(config_path,expected_sha256,project,check_inputs=True);output=Path(output)
    if output.resolve()!=Path(c['output']).resolve():raise ValueError('Exact new control-audit output required')
    native_run,native_artifacts=read_sealed(c['native_root'])
    if native_run['experiment_id']!='panda_preview_export_v1' or native_run['split']!='train' or native_run['source_commit']!=c['native_source_commit']:
        raise ValueError('Exact verified native training gallery registry required')
    with Path(c['inputs']['manifest']['path']).open(newline='') as handle:training=[r['image_id'] for r in csv.DictReader(handle) if r['split']=='train']
    ids=set(training)
    if (len(training)!=len(ids) or any(not re.fullmatch('[a-f0-9]{32}',sid) for sid in ids) or
            set(native_artifacts)!={'checkpoints/slide-'+sid+'.json' for sid in ids}|{'checkpoints/summary.json'}):raise ValueError('Original training gallery coverage differs')
    all_cases=json.loads(Path(c['inputs']['cases']['path']).read_text())
    if any(r['split']=='test' for r in all_cases):raise ValueError('Final tests forbidden in case catalog')
    clean={r['host_id']:r for r in all_cases if r['split']=='train' and r['kind']=='unmodified'}
    selected=sorted((r for r in all_cases if r['split']=='train' and r['kind']=='synthetic' and float(r['requested_percent'])==5),key=lambda r:r['host_id'])
    trials=[r for r in json.loads(Path(c['inputs']['trials']['path']).read_text()) if r['split']=='train' and float(r['requested_percent'])==5]
    byhost={r['host_id']:r for r in trials}
    if (set(clean)!=ids or len(ids)!=72 or len(selected)!=24 or len(byhost)!=len(trials) or len(byhost)!=24 or
            {r['host_id'] for r in selected}!=set(byhost) or len({r['donor_id'] for r in selected})!=16):raise ValueError('Exact 24 saved training pairs required')
    features=json.loads(Path(c['inputs']['features']['path']).read_text());complete=json.loads(Path(c['inputs']['feature_completion']['path']).read_text())
    if (features['source_kind']!='real' or features['config_sha256']!=c['old_feature_config_sha256'] or complete['status']!='verified' or
            complete['artifacts']['feature_checkpoint.json']!=c['inputs']['features']['sha256']):raise ValueError('Verified cached robust features required')
    verification=json.loads(Path(c['inputs']['verification']['path']).read_text())
    if verification['manifest_sha256']!=c['inputs']['manifest']['sha256'] or native_run['dataset_identity']!=verification['manifest_sha256']:raise ValueError('Original manifest provenance differs')
    verified={r['image_id']:r for r in verification['records'] if r['image_id'] in ids};paths=[Path(p) for p in json.loads(Path(c['inputs']['directories']['path']).read_text())]
    registry=Registry(output,ExperimentRun(c['experiment_id'],c['hypothesis'],source_commit,canonical(c),native_run['dataset_identity'],'train',
        native_run['checkpoint_fingerprint'],native_run['embedding_fingerprint'],canonical(c['resources'])))
    registry.status('planned');registry.status('running',slurm_job_id=os.environ['SLURM_JOB_ID']);(output/'pairs').mkdir();(output/'tiles').mkdir()
    sources={};assets={};rendered={};pairs=[]
    def source(sid):
        if sid not in ids:raise ValueError('Only original training image sources allowed')
        if sid not in sources:
            matches=[p for p in paths if sid in p.parts];key='checkpoints/slide-'+sid+'.json'
            if len(matches)!=1 or key not in native_artifacts:raise ValueError('Unique verified native source required')
            report=json.loads((Path(c['native_root'])/key).read_text())['report']
            rows,metadata,hashes,receipt=tile_source(sid,matches[0],c['encoded_root'],verified[sid],report)
            if (metadata['slide_id']!=sid or metadata['coordinate_units']!='microns' or metadata['microns_per_unit']!=1 or
                    metadata['coordinate_reference']!='tile_top_left' or len({r['tile_id'] for r in rows})!=len(rows) or
                    any(r['image_id']!=sid for r in rows)):raise ValueError('Original source slide/physical provenance differs')
            same_prediction(report['baseline'],clean[sid]['baseline'])
            sources[sid]=dict(rows=rows,metadata=metadata,hashes=hashes,directory=matches[0],receipt=receipt)
        return sources[sid]
    try:
        for mixed in selected:
            hid,did=mixed['host_id'],mixed['donor_id'];hs,ds=source(hid),source(did)
            pair=assemble_pair(mixed,clean[hid],clean[did],byhost[hid],features['features'],hs,ds)
            pair['galleries']={role:[copy_tile(hs if role=='host_context' else ds,i,output,assets,c['maximum_png_bytes']) for i in indices]
                for role,indices in pair['gallery_indices'].items()}
            pair['source_kind']='real'
            pair['provenance']=dict(source_commit=source_commit,protocol_sha256=expected_sha256,trials_sha256=c['inputs']['trials']['sha256'],
                cases_sha256=c['inputs']['cases']['sha256'],features_sha256=c['inputs']['features']['sha256'],source_receipts={hid:hs['receipt'],did:ds['receipt']})
            pairs.append(pair)
            for extension,content in [('json',canonical(pair)+'\n'),('html',render_pair(pair))]:
                name='pairs/'+hid+'.'+extension
                with (output/name).open('x') as handle:handle.write(content)
                rendered[name]=file_sha256(output/name)
            registry.checkpoint('pair-'+hid,pair)
        references=sum(len(v) for p in pairs for v in p['galleries'].values())
        if references>384 or len(assets)>288:raise ValueError('Frozen image-reference/asset workload exceeded')
        links=''.join('<li><a href="pairs/'+p['host_id']+'.html">'+p['host_id']+'</a></li>' for p in pairs)
        with (output/'index.html').open('x') as handle:handle.write(_page('Known-provenance control audits','<p>Truth is disclosed for research auditing, not detector output. No clinical/foreignness validation.</p><ul>'+links+'</ul>'))
        rendered['index.html']=file_sha256(output/'index.html')
        for name,a in assets.items():rendered[name]=a['sha256']
        for s in sources.values():
            r=s['receipt']
            if (file_sha256(r['completion_path'])!=r['completion_sha256'] or file_sha256(Path(r['directory'])/'tiles.csv')!=r['manifest_sha256'] or
                    file_sha256(Path(r['directory'])/'metadata.json')!=r['metadata_sha256']):raise ValueError('Source metadata mutated')
        if (any(file_sha256(output/name)!=digest for name,digest in rendered.items()) or any(file_sha256(a['source_path'])!=a['sha256'] for a in assets.values()) or
                read_sealed(c['native_root'])!=(native_run,native_artifacts) or any(file_sha256(e['path'])!=e['sha256'] for e in c['inputs'].values())):raise ValueError('Audit source/output mutated')
        summary=summarize(pairs);summary.update(png_assets=assets,rendered_file_sha256=rendered,image_references=references,
            unique_png_assets=len(assets),copied_png_bytes=sum(a['bytes'] for a in assets.values()),source_receipts=[s['receipt'] for s in sources.values()])
        registry.checkpoint('summary',summary);registry.status('verified',validation=True,interpretation=summary['interpretation']);return summary
    except BaseException as exc:
        registry.status('failed',interpretation=type(exc).__name__+': '+str(exc));raise
