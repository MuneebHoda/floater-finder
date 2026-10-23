"""Frozen-threshold, training-only audit of existing paired-placement cases."""
from functools import lru_cache
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
from ..artifacts import write_json
from ..panda_review import prediction, summarize
from ..predictors import load_predictor
from ..predictors.data import load_development
from ..research.acceptance import _occupancy
from ..research.contracts import canonical, fingerprint, slide_identity, ExperimentRun, InterventionSpec
from ..research.engine import apply_intervention
from ..research.registry import Registry, file_hash
from .calibration import shortlisted
from .contextual_similarity import METHODS, unit_mean
from .placement import memberships, map_components, review_features, annotation_arrays, evaluate, paired_groups
from .training import host_interval


def _spec(row):
    values = dict(row['intervention_audit']['spec'])
    for key in ('donor_indices','replacement_indices'):
        values[key] = tuple(values[key])
    if values['placement_anchor_um'] is not None:
        values['placement_anchor_um'] = tuple(values['placement_anchor_um'])
    return InterventionSpec(**values)


def _same_prediction(actual, expected):
    if (actual['prediction'] != expected['prediction'] or set(actual['scores']) != set(expected['scores']) or
            not all(np.isclose(actual['scores'][k],v,rtol=1e-12,atol=1e-12) for k,v in expected['scores'].items())):
        raise RuntimeError('Saved prediction reconstruction differs; stop')


def _scorer(source, task, improved):
    if task == 's2': return improved
    text = source['text']
    columns = [text.classes.index(k) for k in ('benign','cancer')]
    # Preserve the historical float32 contraction/layout, including all prompt columns.
    return lambda feats: prediction(np.einsum('id,cd->ic',feats,text.feats,optimize=False)[:,columns])


def _case_summary(group):
    positive = [dict(r,one=1) for r in group if r['foreign_tiles']]
    native_correct = sum(r['unmodified_correct'] for r in group)
    damage = sum(r['hypothetical_clean_damage'] for r in group)
    return dict(metrics=summarize(group),cases=len(group),
        unique_host_slides=len({r['host_id'] for r in group}),
        unique_donor_slides=len({r['donor_id'] for r in group if r['donor_id']}),
        originally_correct=sum(r['originally_correct'] for r in group),
        initially_incorrect=sum(r['initially_incorrect'] for r in group),
        alerted_cases=sum(r['alerted'] for r in group),
        alert_rate=sum(r['alerted'] for r in group)/len(group) if group else None,
        alerts=sum(r['alerts'] for r in group),
        mean_components_per_case=sum(r['alerts'] for r in group)/len(group) if group else None,
        abstentions=sum(r['topology_abstained'] for r in group),
        genuine_cancer_components=sum(r['genuine_cancer_components'] for r in group),
        genuine_cancer_components_flagged=sum(r['genuine_cancer_components_flagged'] for r in group),
        native_originally_correct=native_correct,hypothetical_native_damage=damage,
        hypothetical_native_damage_rate=damage/native_correct if native_correct else None,
        fragment_recall_conditional_host_bootstrap95=host_interval(positive,'fragment_hit','one',2000,20261023))


def _aggregate(rows):
    result = []
    fields = ('task','mode','control','condition','requested_percent')
    for key in sorted({tuple(r[k] for k in fields) for r in rows}):
        group = [r for r in rows if tuple(r[k] for k in fields) == key]
        result.append(dict(zip(fields,key),**_case_summary(group)))
    return result


def _paired_summary(groups, rows):
    byid = {r['case_id']:r for r in rows}; result = []
    strata = ('task','condition','control','requested_percent')
    for key in sorted({tuple(g[k] for k in strata) for g in groups}):
        selected = [g for g in groups if tuple(g[k] for k in strata)==key and g['complete_triplet']]
        for mode in ('near_tissue','within_region_context'):
            pairs = [(byid[g['cases']['append_legacy']],byid[g['cases'][mode]]) for g in selected]
            positive = [(a,b) for a,b in pairs if a['foreign_tiles']]
            differences = [dict(host_id=a['host_id'],delta=int(b['fragment_hit'])-int(a['fragment_hit']),one=1) for a,b in positive]
            result.append(dict(zip(strata,key),comparison='append_legacy vs '+mode,
                complete_triplets=len(pairs),unique_host_slides=len({a['host_id'] for a,b in pairs}),
                positive_pairs=len(positive),append_hits=sum(a['fragment_hit'] for a,b in positive),
                placed_hits=sum(b['fragment_hit'] for a,b in positive),
                append_only_hits=sum(a['fragment_hit'] and not b['fragment_hit'] for a,b in positive),
                placed_only_hits=sum(b['fragment_hit'] and not a['fragment_hit'] for a,b in positive),
                append_abstentions=sum(a['topology_abstained'] for a,b in pairs),
                placed_abstentions=sum(b['topology_abstained'] for a,b in pairs),
                append_alerts=sum(a['alerts'] for a,b in pairs),placed_alerts=sum(b['alerts'] for a,b in pairs),
                append=_case_summary([a for a,b in pairs]),placed=_case_summary([b for a,b in pairs]),
                recall_difference_conditional_host_bootstrap95=host_interval(differences,'delta','one',2000,20261023)))
    return result


def run(manifest, directories, encoded, verification, engine_run, cases, protocol, predictor, output, source_commit):
    if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Real placement analysis requires CPU Slurm, no GPU')
    config = json.loads(Path(protocol).read_text())
    if config['split'] != 'train' or tuple(config['methods']) != METHODS or config['primary'] != 'robust_nn5':
        raise ValueError('Frozen training-only method/configuration required')
    project = Path(__file__).resolve().parents[3]
    def verified(path, digest):
        if file_hash(path) != digest: raise ValueError('Frozen input hash differs: '+str(path))
        return json.loads(Path(path).read_text())
    trials = verified(project/config['trials'],config['trials_sha256'])
    threshold_report = verified(project/config['threshold_report'],config['threshold_sha256'])
    prior_cases = verified(cases,config['old_components_sha256'])
    old_metadata = json.loads((Path(engine_run)/'run.json').read_text())
    if old_metadata['identity'] != config['engine_identity']: raise ValueError('Wrong source registry')
    old = Registry(engine_run,ExperimentRun(**old_metadata['run']))
    if old.report()['status'] != 'verified': raise ValueError('Engine source is not sealed/verified')
    saved = [old.load_checkpoint(e['key']) for e in old.events() if e['kind']=='checkpoint' and e['key'].startswith(('s1-','s2-'))]
    if sum(bool(r.get('excluded')) for r in saved) != 327:
        raise ValueError('Historical exclusions changed')
    if sorted(fingerprint(r) for r in saved if not r.get('excluded')) != sorted(map(fingerprint,trials)):
        raise ValueError('Published trials differ from sealed source checkpoints')
    positive = [dict(r,case_id='case-'+fingerprint({k:r[k] for k in ('task','condition','control','host_id','donor_id','seed','requested_percent','mode')})[:24])
                for r in trials if r['requested_percent'] > 0]
    if len(positive) != 825 or len(trials)-len(positive) != 192: raise ValueError('Historical eligibility changed')
    records, receipt = load_development(manifest,directories,encoded,verification,'train')
    sources = {r['slide'].metadata['slide_id']:r for r in records}
    if len(sources) != 72: raise ValueError('Expected original training split')
    if threshold_report['identities']['manifest_sha256'] != file_hash(manifest):
        raise ValueError('Threshold fitting cohort differs')
    improved = load_predictor(predictor)
    for name,digest in config['predictor_files'].items():
        if file_hash(Path(predictor)/name) != digest: raise ValueError('Frozen predictor differs')
    if any(s['slide'].metadata['model'] != improved.spec['embedding_model'] for s in sources.values()):
        raise ValueError('Predictor embedding-space provenance differs')
    identity = dict(config=config,protocol_sha256=file_hash(protocol),manifest_sha256=file_hash(manifest),
        directories_sha256=file_hash(directories),verification_sha256=file_hash(verification),
        input_identities={sid:slide_identity(s['slide']) for sid,s in sources.items()})
    registry = Registry(output,ExperimentRun('panda-detector-placement-v1',config['hypothesis'],source_commit,
        canonical(identity),identity['manifest_sha256'],'train',records[0]['slide'].metadata['model']['checkpoint_sha256'],
        receipt['text_fingerprint'],canonical(dict(cpus=2,memory_gb=8,maximum_minutes=20,gpu=0))))
    state = registry.report()['status']
    if state == 'verified': return registry.load_checkpoint('summary')
    if state is None: registry.status('planned')
    registry.status('running',slurm_job_id=os.environ['SLURM_JOB_ID'])
    try:
        geometries = {}; clean_maps = {}; mappings = {}; used_pngs = {}
        hosts = sorted({r['host_id'] for r in positive})
        old_clean = {c['host_id']:c for c in prior_cases if c['kind']=='unmodified' and c['split']=='train'}
        for sid in hosts:
            source = sources[sid]
            if old.load_checkpoint('geometry-'+sid) is None:
                raise ValueError('Missing cached geometry; no new WSI reads permitted')
            occupancy,_ = _occupancy(source,old,None,None)
            geometries[sid] = occupancy
            parts,quality = map_components(occupancy.mask(),source['slide'].coords*source['slide'].metadata['microns_per_unit'],
                source['slide'].metadata['tile_size'],occupancy.pixel_um,'clean')
            if (memberships(parts) != memberships(old_clean[sid]['components']) or
                    quality['mapping_fraction'] != old_clean[sid]['mapping_fraction']):
                raise RuntimeError('Clean RGB topology parity failed')
            clean_maps[sid] = dict(components=parts,quality=quality)
        @lru_cache(maxsize=1024)
        def png(sid,index):
            source = sources[sid]; row = source['annotations'][index]; path = source['directory']/row['path']
            completion = json.loads((Path(encoded)/sid/'completion.json').read_text())
            expected = completion['input_identity']['png_sha256'][row['tile_id']]
            if path.resolve().parent != source['directory'].resolve() or file_hash(path) != expected:
                raise ValueError('Changed donor PNG')
            used_pngs[str(path)] = expected
            with Image.open(path) as image:
                if image.size != (224,224): raise ValueError('Expected canonical saved 224-pixel RGB tiles')
                return np.asarray(image.convert('RGB'))
        def reconstruct(row):
            result = apply_intervention(sources[row['host_id']]['slide'],sources[row['donor_id']]['slide'],_spec(row),occupancy=geometries[row['host_id']])
            if slide_identity(result.slide) != row['intervention_audit']['result_identity']:
                raise RuntimeError('Exact intervention identity reconstruction failed')
            return result
        # Finish/hash all geometry and paired eligibility before measuring any detector score.
        for number,row in enumerate(positive):
            result = reconstruct(row); slide = result.slide; occ = geometries[row['host_id']]
            altered = row['intervention_audit']['altered_indices']
            rgbs = [] if row['mode']=='replacement' else [png(row['donor_id'],i) for i in row['donor_indices']]
            parts,quality = map_components(occ.mask(),slide.coords*slide.metadata['microns_per_unit'],slide.metadata['tile_size'],
                occ.pixel_um,row['mode'],altered,rgbs)
            if row['mode']=='replacement' and memberships(parts) != memberships(clean_maps[row['host_id']]['components']):
                raise RuntimeError('Native replacement carrier mapping changed')
            mappings[row['case_id']] = dict(components=parts,quality=quality)
            registry.checkpoint('mapping-'+row['case_id'],mappings[row['case_id']])
            if number%50==0: print(json.dumps(dict(stage='mapping',cases=number+1)),flush=True)
        groups = paired_groups(positive)
        registry.checkpoint('eligibility',dict(groups=groups,old_exclusions_retained=327,zero_cases_reuse_clean_anchors=192,
            used_pngs=used_pngs,clean_mapping_parity=len(hosts),policy='All old eligible positive-dose cases retained; mapping abstentions are misses'))
        centers = {sid:unit_mean(s['slide'].feats) for sid,s in sources.items()}
        metrics = {m:[] for m in METHODS}; details = []
        fold_records = {}
        for row in threshold_report['folds']:
            for sid in row['held_ids']:
                if sid in row['fit_ids']: raise ValueError('Host leaked into fitting reference')
                fold_records[(sid,row['method'])] = row
        tasks = {'s1':('benign','cancer'),'s2':('low_grade','high_grade')}
        work = []
        for sid in hosts:
            anchor = next(r for r in positive if r['host_id']==sid)
            work.append(dict(anchor,case_id='clean-'+sid,kind='unmodified',mode='clean',condition='native',control='native',
                donor_id=None,requested_percent=0,realized_percent=0,seed=0))
        work += [dict(r,kind='sham' if r['control']=='same_source_sham' else 'synthetic') for r in positive]
        for number,row in enumerate(work):
            sid = row['host_id']; source = sources[sid]; task = row['task']; scorer = _scorer(source,task,improved)
            clean = scorer(source['slide'].feats); _same_prediction(clean,row['baseline'])
            if row['kind']=='unmodified':
                slide = source['slide']; mapping = clean_maps[sid]; altered = []; donor_indices = []; donor_rows = source['annotations']
            else:
                result = reconstruct(row); slide = result.slide; mapping = mappings[row['case_id']]
                _same_prediction(scorer(slide.feats),row['contaminated'])
                original = result.restore()
                if slide_identity(original) != slide_identity(source['slide']): raise RuntimeError('Oracle identity failed')
                altered = row['intervention_audit']['altered_indices']; donor_indices = row['donor_indices']; donor_rows = sources[row['donor_id']]['annotations']
            refs = fold_records[(sid,'cohort_centroid5')]['fit_ids']
            before,parts = review_features(slide.feats,slide.coords*slide.metadata['microns_per_unit'],mapping['components'],
                [centers[k] for k in refs if centers[k] is not None],scorer,tasks[task])
            known,cancer = annotation_arrays(source['annotations'],donor_rows,altered,donor_indices,len(slide.feats))
            record = {k:row[k] for k in ('case_id','task','condition','control','host_id','donor_id','mode','kind','seed','requested_percent','realized_percent')}
            record.update(components=parts,quality=mapping['quality'],baseline=clean,contaminated=before,
                foreign_mask=slide.foreign_mask.tolist(),annotation_known=known.tolist(),annotated_cancer=cancer.tolist())
            registry.checkpoint(row['case_id'],record); details.append(record)
            for method in METHODS:
                fold = fold_records[(sid,method)]
                flags = shortlisted([p['scores'][method] for p in parts],fold['threshold'],mapping['quality']['mapping_fraction'])
                metric = evaluate(slide.feats,parts,flags,slide.foreign_mask,known,cancer,scorer,clean,before,row['host_truth'],mapping['quality']['mapping_fraction'])
                metric.update({k:record[k] for k in ('case_id','task','condition','control','host_id','donor_id','mode','kind','seed','requested_percent')})
                metric.update(threshold=fold['threshold'],fold=fold['fold'],donor_in_reference=row['donor_id'] in refs)
                metrics[method].append(metric)
            if number%50==0: print(json.dumps(dict(stage='features',cases=number+1)),flush=True)
        summary = dict(schema_version=1,source_kind='real',source_commit=source_commit,slurm_job_id=os.environ['SLURM_JOB_ID'],
            primary=config['primary'],identities=identity,counts=dict(clean_anchors=len(hosts),positive_dose_cases=len(positive),
                foreign_cases=sum(r['control']!='same_source_sham' for r in positive),native_shams=sum(r['control']=='same_source_sham' for r in positive),
                old_geometry_exclusions=327,reused_zero_dose_instances=192,verified_pngs=len(used_pngs),
                complete_triplets=sum(g['complete_triplet'] for g in groups)),
            methods={m:dict(groups=_aggregate(rows),paired=_paired_summary(groups,rows)) for m,rows in metrics.items()},
            limitations=config['limitations'],final_test_predictions_computed=False,calibration_predictions_computed=False,
            thresholds_refit=False,clinical_validity_verified=False,patient_independence_verified=False)
        write_json(Path(output)/'metrics_by_case.json',metrics)
        write_json(Path(output)/'component_records.json',details)
        registry.checkpoint('summary',summary)
        registry.checkpoint('outputs',dict(artifacts={name:file_hash(Path(output)/name) for name in ('metrics_by_case.json','component_records.json')}))
        registry.status('verified',validation=True,interpretation='Paired development engineering audit; no independent validation',limitations=config['limitations'])
        return summary
    except BaseException as exc:
        registry.status('failed',interpretation=type(exc).__name__+': '+str(exc))
        raise
