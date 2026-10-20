#!/usr/bin/env python3
"""Real calibration-only piece dependence, with no calibrated alert or foreignness claim."""
import argparse,csv,json,os
from pathlib import Path
import numpy as np
from floater_finder.artifacts import Slide,TextEmbeddings,write_json
from floater_finder.experiments import file_sha256
from floater_finder.fragment_dependence import analyze_fragment_dependence
from floater_finder.panda_stress import inject_development_s1
from floater_finder.scoring import pool


def make_scorer(text):
    classes=('benign','cancer');indices=[text.classes.index(c) for c in classes]
    def scorer(features,coords):
        scores=np.einsum('id,cd->ic',features,text.feats,optimize=False)[:,indices]
        values=pool(scores,'top5pct')
        return dict(prediction=classes[int(np.argmax(values))],scores=dict(zip(classes,values.tolist())))
    return scorer


def dependence_counts(clean):
    evaluable=[r for r in clean if r['evaluable_pieces']>0]
    return dict(unmodified_evaluable_slides=len(evaluable),unmodified_unevaluable_slides=len(clean)-len(evaluable),
        unmodified_slides_with_decisive_components=sum(r['any_decisive'] for r in evaluable),
        unmodified_decision_dependence_rate=sum(r['any_decisive'] for r in evaluable)/len(evaluable) if evaluable else None)


def run(manifest,directories,encoded,verification,stress,output):
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Real piece analysis requires bounded CPU Slurm')
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a fresh piece-analysis output')
    with Path(manifest).open(newline='') as f:cohort={r['image_id']:r for r in csv.DictReader(f)}
    receipt=json.loads(Path(verification).read_text());stress=Path(stress)
    summary=json.loads((stress/'summary.json').read_text());trials=json.loads((stress/'trials.json').read_text())
    assert receipt['manifest_sha256']==file_sha256(manifest)==summary['manifest_sha256']
    by_id={r['image_id']:r for r in receipt['records']};slides={};texts={};tile_rows={};records=[]
    for directory in map(Path,json.loads(Path(directories).read_text())):
        meta=json.loads((directory/'metadata.json').read_text());sid=meta['slide_id']
        if cohort[sid]['split']!='calibration':continue
        root=Path(encoded)/sid
        assert file_sha256(root/'completion.json')==by_id[sid]['completion_sha256']
        for name,digest in by_id[sid]['artifact_sha256'].items():assert file_sha256(root/name)==digest
        assert file_sha256(directory/'tiles.csv')==summary['input_sha256'][sid]['tile_manifest_sha256']
        s,t=Slide.load(root/'slide.npz'),TextEmbeddings.load(root/'text.npz')
        assert s.metadata['source_kind']=='real' and s.metadata['cohort_split']=='calibration'
        assert s.metadata['slide_id']==sid and s.metadata['isup_grade']==int(cohort[sid]['isup_grade'])
        assert t.fingerprint()==receipt['text_fingerprint']
        slides[sid]=s;texts[sid]=t
        with (directory/'tiles.csv').open(newline='') as f:tile_rows[sid]=list(csv.DictReader(f))
    assert len(slides)==24 and len(cohort)==120
    output.mkdir(parents=True,exist_ok=False)
    def analyze(slide,name,kind,percent=None,expected_baseline=None):
        sid=slide.metadata['slide_id'];text=texts[sid];scorer=make_scorer(text)
        report=analyze_fragment_dependence(slide.feats,slide.coords,scorer,tile_step=slide.metadata['tile_step'],
            tile_size=slide.metadata['tile_size'],coordinate_units=slide.metadata['coordinate_units'],
            microns_per_unit=slide.metadata['microns_per_unit'],source_kind='real',
            scorer_id='PANDA fixed morphology v1 benign/cancer top5pct; development candidate',
            tile_ids=slide.tile_ids,max_gap_tiles=0,alert_policy=None)
        assert report['alerts_evaluated'] is False
        if expected_baseline is not None:assert report['baseline']==expected_baseline
        for piece in report['pieces']:
            indices=np.array(piece['tile_indices'],dtype=int)
            piece['evaluation_only_synthetic_foreign_tiles']=int(slide.foreign_mask[indices].sum())
            if kind=='unmodified' and slide.metadata['panda']['mask_available']:
                piece['evaluation_only_annotated_cancer_area_mm2']=sum(float(tile_rows[sid][i]['area_mm2'])*
                    sum(float(tile_rows[sid][i][f'gleason{g}_fraction']) for g in (3,4,5)) for i in indices)
            else:piece['evaluation_only_annotated_cancer_area_mm2']=None
        decisive=[p for p in report['pieces'] if p['decision_changing']]
        report['development_provenance']=dict(slide_id=sid,cohort_split='calibration',original_isup_grade=int(cohort[sid]['isup_grade']),
            kind=kind,requested_percent=percent,embedding_completion_sha256=by_id[sid]['completion_sha256'],
            manifest_sha256=receipt['manifest_sha256'],text_fingerprint=receipt['text_fingerprint'],
            patient_independence_verified=False,complete_biopsy_topology_verified=False,clinical_validity_verified=False,
            annotation_fields_are_evaluation_only=True,slurm_job_id=os.environ['SLURM_JOB_ID'])
        write_json(output/(name+'.json'),report)
        records.append(dict(file=name+'.json',slide_id=sid,kind=kind,original_isup_grade=int(cohort[sid]['isup_grade']),
            requested_percent=percent,baseline_prediction=report['baseline']['prediction'],pieces=report['piece_count'],
            evaluable_pieces=sum(p['counterfactual']['status']=='scored' for p in report['pieces']),
            decisive_pieces=len(decisive),any_decisive=bool(decisive),
            decisive_pure_foreign_components=sum(p['evaluation_only_synthetic_foreign_tiles']==p['tile_count'] for p in decisive),
            decisive_host_components=sum(p['evaluation_only_synthetic_foreign_tiles']==0 for p in decisive),
            decisive_annotated_cancer_components=sum((p['evaluation_only_annotated_cancer_area_mm2'] or 0)>0 for p in decisive)))
    for sid,slide in sorted(slides.items()):analyze(slide,sid+'-unmodified','unmodified')
    for trial in trials:
        if trial['split']!='calibration' or trial['requested_percent']==0:continue
        sid=trial['host_id'];mixed=inject_development_s1(slides[sid],slides[trial['donor_id']],
            np.array(trial['donor_indices'],dtype=int),trial['requested_percent'],summary['protocol']['seed'])
        analyze(mixed,sid+'-p'+str(trial['requested_percent']).replace('.','p'),'synthetic_mixture',trial['requested_percent'],trial['contaminated']['top5pct'])
    clean=[r for r in records if r['kind']=='unmodified'];assert len(records)==64 and len(clean)==24
    write_json(output/'summary.json',dict(source_kind='real',category='PANDA calibration sampled-component dependence diagnostic',
        slurm_job_id=os.environ['SLURM_JOB_ID'],pooling='top5pct',connectivity=8,max_gap_tiles=0,
        unmodified_slides=24,synthetic_mixtures=40,distinct_mixture_host_slides=8,
        **dependence_counts(clean),
        alert_policy=None,review_alert_rate=None,alerts_evaluated=False,test_slides_scored=False,
        patient_independence_verified=False,clinical_validity_verified=False,complete_biopsy_topology_verified=False,
        records=records,manifest_sha256=receipt['manifest_sha256'],stress_summary_sha256=file_sha256(stress/'summary.json'),
        limitations=['Sampled components do not establish complete biopsy-piece boundaries.',
            'Decision dependence can arise from genuine cancer and does not establish foreign tissue.',
            'No calibrated alert thresholds or final-test evaluation; repeated mixtures are not independent patients.']))
    return dict(unmodified=24,mixtures=40,clean_decisive=sum(r['any_decisive'] for r in clean))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','tiling-directories','encoded-root','verification','stress','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(run(a.manifest,a.tiling_directories,a.encoded_root,a.verification,a.stress,a.output)))
