#!/usr/bin/env python3
"""Exact historical score acceptance only; never retrain or select any model."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256
from floater_finder.predictors.data import load_development
from floater_finder.predictors.linear_probe import FrozenPredictor, load_predictor
from floater_finder.predictors.run import task_sources


def run(manifest,directories,encoded,verification,baseline,previous,output):
    if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Bounded CPU Slurm required')
    previous,output=Path(previous),Path(output);output.mkdir(parents=True,exist_ok=False)
    prior=json.loads(Path(baseline).read_text());historical={(r['image_id'],r['task'],r['pooling']):r for r in prior}
    selection=json.loads((previous/'selection_frozen.json').read_text());rows=[];changed=0;maximum=0.;linear_checked=0
    for split in ('train','calibration'):
        sources,_=load_development(manifest,directories,encoded,verification,split)
        for task,t in selection['tasks'].items():
            for source in task_sources(sources,task):
                slide,text=source['slide'],source['text'];sid=slide.metadata['slide_id']
                for rule in ('mean','top1pct','top5pct'):
                    name='zero_shot_'+rule;old=load_predictor(previous/'models'/task/name)
                    spec=dict(old.spec,text_classes=text.classes,source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'),
                        original_adapter_source_commit=old.spec['source_commit'])
                    fixed=FrozenPredictor(spec,dict(text=text.feats));r=fixed.score_slide(slide);expected=historical[(sid,task,rule)]
                    if r['prediction']!=expected['prediction'] or r['scores']!=expected['scores']:
                        raise RuntimeError('Corrected adapter does not recover exact historical zero-shot scores')
                    suffix='oof' if split=='train' else 'known_calibration'
                    earlier=next(v for v in json.loads((previous/f'{task}_{name}_{suffix}.json').read_text()) if v['image_id']==sid)
                    if earlier['prediction']!=r['prediction'] or earlier['truth']!=expected['truth']:
                        raise RuntimeError('Prediction/label changed; inspect rather than silently update')
                    difference=max(abs(r['scores'][c]-earlier['scores'][c]) for c in spec['classes'])
                    changed+=int(difference>0);maximum=max(maximum,difference)
                    rows.append(dict(image_id=sid,task=task,split=split,pooling=rule,truth=expected['truth'],**r))
                    modeldir=output/'corrected_models'/task/name
                    if not modeldir.exists():fixed.save(modeldir)
            # Frozen linear coefficients are unchanged; verify actual inference against saved known-cal outputs.
            for name in ('linear_mean','linear_mean_max_topk'):
                p=load_predictor(previous/'models'/task/name)
                if split=='calibration':
                    saved={r['image_id']:r for r in json.loads((previous/f'{task}_{name}_known_calibration.json').read_text())}
                    for source in task_sources(sources,task):
                        r=p.score_slide(source['slide']);v=saved[source['slide'].metadata['slide_id']]
                        if r['prediction']!=v['prediction'] or r['margin']!=v['margin'] or r['scores']!=v['scores']:
                            raise RuntimeError('Frozen linear inference changed')
                        linear_checked+=1
    write_json(output/'exact_zero_shot_predictions.json',rows)
    write_json(output/'verification.json',dict(source_commit=os.environ.get('FLOATER_SOURCE_COMMIT'),slurm_job_id=os.environ['SLURM_JOB_ID'],
        historical_exact_comparisons=len(rows),previous_roundoff_vectors=changed,previous_maximum_absolute_cosine_difference=maximum,
        linear_known_calibration_predictions_exact=linear_checked,primary_unchanged=True,models_retrained=False,
        selection_sha256=file_sha256(previous/'selection_frozen.json'),historical_sha256=file_sha256(baseline),
        original_completion_sha256=file_sha256(previous/'completion.json'),test_slides_scored=False,
        correction='Preserve all four text classes and original advanced-indexed score strides before float32 pooling'))
    write_json(output/'completion.json',dict(files={str(p.relative_to(output)):file_sha256(p) for p in output.rglob('*') if p.is_file()}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','directories','encoded','verification','baseline','previous','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();run(a.manifest,a.directories,a.encoded,a.verification,a.baseline,a.previous,a.output)
