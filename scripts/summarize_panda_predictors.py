#!/usr/bin/env python3
"""Reproduce a concise research checkpoint from immutable predictor result JSON."""
import argparse
import json
from pathlib import Path
import numpy as np
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256


def summarize(directory, output, coverage_receipt):
    directory, output = Path(directory), Path(output)
    selection=json.loads((directory/'selection_frozen.json').read_text())
    known=json.loads((directory/'known_calibration_metrics.json').read_text())['metrics']
    cases=json.loads((directory/'clean_error_case_studies.json').read_text())
    correlations=json.loads((directory/'diagnostic_correlations.json').read_text())
    execution=json.loads((directory/'execution.json').read_text())
    receipt=json.loads(Path(coverage_receipt).read_text()); permitted={r['image_id'] for r in cases}
    annotations={r['image_id']:r for r in receipt['records'] if r['image_id'] in permitted and r['split'] in ('train','calibration')}
    if set(annotations)!=permitted:
        raise ValueError('Every development case needs a matching old annotation receipt; no test joins allowed')
    joined=[]; native_correlations=[]
    for r in cases:
        a=annotations[r['image_id']]
        if a['split']!=r['split'] or a['isup_grade']!=r['diagnostic']['isup_grade']:
            raise ValueError('Annotation receipt identity differs')
        joined.append(dict(r,native_annotation_diagnostic={k:a[k] for k in
            ('mask_usable','native_gp45_area_mm2','captured_gp45_area_mm2','gp45_annotation_capture_fraction')}))
    from scipy.stats import spearmanr
    for task,t in selection['tasks'].items():
        for name in t['all_models']:
            for split in ('train','calibration'):
                for truth in ['all',*t['all_models'][name]['classes']]:
                    subset=[r for r in joined if r['task']==task and r['model']==name and r['split']==split and (truth=='all' or r['truth']==truth)]
                    for feature in ('native_gp45_area_mm2','captured_gp45_area_mm2','gp45_annotation_capture_fraction'):
                        valid=[r for r in subset if r['native_annotation_diagnostic']['mask_usable'] and r['native_annotation_diagnostic'][feature] is not None]
                        x=[r['native_annotation_diagnostic'][feature] for r in valid]
                        for outcome in ('margin','error'):
                            y=[r['margin'] if outcome=='margin' else int(not r['correct']) for r in valid]
                            rho=float(spearmanr(x,y).statistic) if len(x)>=3 and len(set(x))>1 and len(set(y))>1 else None
                            native_correlations.append(dict(task=task,model=name,split=split,truth_class=truth,feature=feature,
                                outcome=outcome,slides=len(valid),spearman_rho=rho,posthoc_diagnostic_only=True))
    lines=['# Frozen-CONCH predictor research v1','',
        f"Real CPU job {execution['slurm_job_id']}; source `{execution['source_commit']}`. "
        'No new image inference, GPU use, dataset download or test prediction. '
        'The 24 known calibration slides are repeatedly inspected development data, not independent validation.','',
        '## Every evaluated model','',
        '| Task/model | Training OOF confusion | OOF BA | OOF recalls | Known-cal confusion | Known-cal BA | Known-cal recalls |',
        '|---|---|---:|---|---|---:|---|']
    margins=[]
    for task,t in selection['tasks'].items():
        for name,m in t['all_models'].items():
            c=known[f'{task}/{name}']
            lines.append(f"| {task}/{name} | {m['confusion_rows_truth_columns_prediction']} | {m['balanced_accuracy']:.3f} | {m['class_recall']} | {c['confusion_rows_truth_columns_prediction']} | {c['balanced_accuracy']:.3f} | {c['class_recall']} |")
            for split in ('train','calibration'):
                for cls in m['classes']:
                    values=[r['margin'] for r in cases if (r['task'],r['model'],r['split'],r['truth'])==(task,name,split,cls)]
                    margins.append(dict(task=task,model=name,split=split,truth=cls,slides=len(values),
                        quantiles_0_10_25_50_75_90_100=np.quantile(values,[0,.1,.25,.5,.75,.9,1]).tolist()))
    lines += ['', 'Confusion rows are true negative/positive class, columns predicted negative/positive. '
        'Benign/cancer uses 72 training and 24 known-cal slides (24/48 and 8/16 supports); '
        'low/high uses 48 training and 16 known-cal slides (24/24 and 8/8). '
        'All three original zero-shot poolers remain unchanged. Supervised training metrics are outer out-of-fold predictions, not resubstitution.','',
        '## Frozen primary and readiness','']
    for task,t in selection['tasks'].items():
        name=t['primary'];m=t['all_models'][name]
        lines.append(f"- **{task}: {name}**; train OOF BA {m['balanced_accuracy']:.3f}, recalls {m['class_recall']}; "
            f"95% conditional slide-bootstrap BA interval {m['balanced_accuracy_stratified_slide_bootstrap95']}; "
            f"preset engineering screen passes: {t['s2_engineering_readiness']}.")
    lines += ['', 'The primary was frozen before opening known-calibration arrays and before any new contamination outcomes. '
        'The screen (BA >=0.70, each recall >=0.60) is an engineering preset, not clinical validity or independent validation. '
        'Selection among five OOF results is optimistic; bootstrap intervals do not include refitting/model-selection uncertainty. '
        'Fresh development-validation remains necessary.','', '## Clean error diagnosis','',
        '| Task/primary | Split/slide | Truth → prediction | Margin | Tiles | Tissue-grid coverage | Sampled cancer annotation mm² | Native GP4/5 annotation mm² | GP4/5 capture |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for task,t in selection['tasks'].items():
        for r in cases:
            if r['task']!=task or r['model']!=t['primary'] or r['correct']:continue
            d=r['diagnostic'];coverage=d['tissue_grid_coverage'];area=d['sampled_cancer_area_mm2']
            a=annotations[r['image_id']]
            lines.append(f"| {task}/{t['primary']} | {r['split']}/{r['image_id']} | {r['truth']} → {r['prediction']} | {r['margin']:.4f} | {d['tiles']} | {coverage} | {area} | {a['native_gp45_area_mm2']} | {a['gp45_annotation_capture_fraction']} |")
    lines += ['', 'Annotation area is limited to exported tile footprints; no full-slide tumor-area claim is made. '
        'Source area is the rectangular image bounding area, not tissue area. Coverage is fraction of eligible RGB tissue-grid cells sampled. '
        'The separate native GP4/5 and capture measurements come from the earlier verified CPU mask receipt, joined only after the primary was frozen. '
        'Native GP3+4+5 total cancer area was not recorded and remains unknown; native GP4/5 cannot substitute for it. '
        'Slide grade never assigns a label to every tile. Missing masks remain unknown.','',
        '## Diagnostic associations','',
        'The companion JSON reports every per-model/per-split/per-class margin/error Spearman association with tile count, '
        'sampling density, source area, tissue-grid coverage and sampled annotation area. '
        'These diagnostics are post-selection, exploratory and uncorrected for multiplicity; annotations are not predictor features.','',
        '## Probability quality and complexity','']
    for task,t in selection['tasks'].items():
        for name in ('linear_mean','linear_mean_max_topk'):
            if name in t['all_models']:
                m=t['all_models'][name];c=known[f'{task}/{name}']
                lines.append(f"- {task}/{name}: OOF Brier {m['brier']:.4f}, ECE {m['ece_five_fixed_probability_bins']:.4f}; "
                    f"known-cal Brier {c['brier']:.4f}, ECE {c['ece_five_fixed_probability_bins']:.4f}.")
    lines += ['', 'Balanced logistic outputs are uncalibrated and class weighting changes class priors. '
        'No probability calibration mapping was fitted. Cosine similarities have no Brier score because they are not probabilities. '
        'Model 4 (attention/MIL) was deferred before execution: 48 grade training slides with unknown patient IDs do not support '
        'credible tuning of additional learned tile-weight parameters.','',
        f"Recorded model failures: `{selection['failures']}`. Every attempted C/fold is in `fold_audit.json`.", '',
        '## Reproducibility and limits','',
        'The JSON/NPZ predictors contain all scaler/linear coefficients and fixed feature transforms; inference uses NumPy only. '
        'Every result, model parameter and input receipt is hash-recorded. Frozen model selection uses train-only grouped nested CV. '
        'Grouping is by known patient if available, otherwise slide ID; true patient independence remains unknown. '
        'Repeated donors, contamination outcomes and calibration results did not select these models. '
        'The original S2 result is immutable; a changed scorer defines a new experiment.']
    output.mkdir(parents=True,exist_ok=False)
    (output/'report.md').write_text('\n'.join(lines)+'\n')
    write_json(output/'margin_distributions.json',margins)
    write_json(output/'native_annotation_case_studies.json',joined)
    write_json(output/'native_annotation_correlations.json',native_correlations)
    write_json(output/'provenance.json',dict(files={str(p.relative_to(directory)):file_sha256(p) for p in directory.rglob('*') if p.is_file()},
        coverage_receipt_sha256=file_sha256(coverage_receipt), joined_slides=len(permitted),
        source_commit=execution['source_commit'],test_slides_scored=False,clinical_validity_verified=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p.add_argument('--coverage-receipt',required=True)
    a=p.parse_args();summarize(a.input,a.output,a.coverage_receipt)
