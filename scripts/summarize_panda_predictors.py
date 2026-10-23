#!/usr/bin/env python3
"""Reproduce a concise research checkpoint from immutable predictor result JSON."""
import argparse
import json
from pathlib import Path
import numpy as np
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256


def summarize(directory, output, coverage_receipt, adapter_verification=None, cached_native=None):
    directory, output = Path(directory), Path(output)
    selection=json.loads((directory/'selection_frozen.json').read_text())
    known=json.loads((directory/'known_calibration_metrics.json').read_text())['metrics']
    cases=json.loads((directory/'clean_error_case_studies.json').read_text())
    execution=json.loads((directory/'execution.json').read_text())
    acceptance=None
    if adapter_verification:
        adapter=Path(adapter_verification)
        acceptance=json.loads((adapter/'verification.json').read_text())
        fixed=json.loads((adapter/'exact_zero_shot_predictions.json').read_text())
        fixed={(r['image_id'],r['task'],r['split'],'zero_shot_'+r['pooling']):r for r in fixed}
        for r in cases:
            key=(r['image_id'],r['task'],r['split'],r['model'])
            if key in fixed:
                if (r['prediction'],r['truth'])!=(fixed[key]['prediction'],fixed[key]['truth']):
                    raise ValueError('Adapter acceptance changed a class label')
                r.update({k:fixed[key][k] for k in ('margin','scores')})
    receipt=json.loads(Path(coverage_receipt).read_text()); permitted={r['image_id'] for r in cases}
    annotations={r['image_id']:r for r in receipt['records'] if r['image_id'] in permitted and r['split'] in ('train','calibration')}
    if set(annotations)!=permitted:
        raise ValueError('Every development case needs a matching old annotation receipt; no test joins allowed')
    cached={r['image_id']:r for r in json.loads(Path(cached_native).read_text())['records']} if cached_native else {}
    if cached_native and set(cached)!=permitted:raise ValueError('Cached native annotations must contain development IDs only')
    joined=[]; native_correlations=[]
    for r in cases:
        a=annotations[r['image_id']]
        if a['split']!=r['split'] or a['isup_grade']!=r['diagnostic']['isup_grade']:
            raise ValueError('Annotation receipt identity differs')
        d={k:a[k] for k in ('mask_usable','native_gp45_area_mm2','captured_gp45_area_mm2','gp45_annotation_capture_fraction')}
        c=cached.get(r['image_id'],{})
        native=c.get('native_cancer_area_mm2') if c.get('status')=='verified_cached_audit' else None
        if native is not None and not np.isclose(c['native_gp45_area_mm2'],a['native_gp45_area_mm2'],atol=1e-8,rtol=1e-8):
            raise ValueError('Native GP4/5 receipts disagree')
        d.update(native_cancer_area_mm2=native,native_cancer_audit_status=c.get('status','not_checked'),
            native_cancer_capture_fraction=r['diagnostic']['sampled_cancer_area_mm2']/native if native else None)
        joined.append(dict(r,native_annotation_diagnostic=d))
    from scipy.stats import spearmanr
    for task,t in selection['tasks'].items():
        for name in t['all_models']:
            for split in ('train','calibration'):
                for truth in ['all',*t['all_models'][name]['classes']]:
                    subset=[r for r in joined if r['task']==task and r['model']==name and r['split']==split and (truth=='all' or r['truth']==truth)]
                    for feature in ('native_gp45_area_mm2','captured_gp45_area_mm2','gp45_annotation_capture_fraction','native_cancer_area_mm2','native_cancer_capture_fraction'):
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
    margins=[];paired=[]
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
        'Fresh development-validation remains necessary.']
    for task,baseline in [('benign_cancer','zero_shot_top5pct'),('low_high','zero_shot_mean')]:
        selected=selection['tasks'][task]['primary']
        for split in ('train','calibration'):
            a={r['image_id']:r for r in cases if (r['task'],r['model'],r['split'])==(task,selected,split)}
            b={r['image_id']:r for r in cases if (r['task'],r['model'],r['split'])==(task,baseline,split)}
            if set(a)!=set(b):raise ValueError('Paired comparison requires identical unique slide IDs')
            grouped=[]
            for cls in selection['tasks'][task]['all_models'][selected]['classes']:
                grouped.append(np.array([int(a[s]['correct'])-int(b[s]['correct']) for s in a if a[s]['truth']==cls]))
            rng=np.random.default_rng(20261021)
            draws=[np.mean([rng.choice(x,len(x),replace=True).mean() for x in grouped]) for _ in range(2000)]
            paired.append(dict(task=task,primary=selected,baseline=baseline,split=split,slides=len(a),
                balanced_accuracy_difference=float(np.mean([x.mean() for x in grouped])),
                paired_stratified_slide_bootstrap95=np.quantile(draws,[.025,.975]).tolist(),
                repetitions=2000,seed=20261021,conditional_on_fixed_predictions=True,
                caveat='Does not include CV refitting/model-selection uncertainty; known calibration is not independent validation'))
    lines += ['', 'The benign/cancer primary has higher training OOF balanced accuracy than the original top-5% scorer, '
        'but lower balanced accuracy on known calibration. This is not a validated benign/cancer improvement. '
        'The low/high primary improves both descriptive point estimates, but improves known-cal high-grade recall by only one slide '
        '(5/8 versus 4/8); uncertainty and repeated calibration use prevent an independent-success claim. '
        'Raw cosine margins and logistic margins have different scales and are compared within model only.','',
        '## Clean error diagnosis','',
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
        f"Native GP3+4+5 annotated areas are available for {sum(r.get('status')=='verified_cached_audit' for r in cached.values())}/96 "
        'development slides from existing hash-verified mask-audit JSON, with no WSI reread. Three original profile slides lack '
        'standalone cached audits and one corrupt mask remains unknown. This is native annotation area, not independently verified cancer burden. '
        'Case JSON separates full-native GP3+4+5, native GP4/5 and sampled GP3+4+5 areas. '
        'Slide grade never assigns a label to every tile. Missing masks remain unknown.','',
        '## Diagnostic associations','',
        'The companion JSON reports every per-model/per-split/per-class margin/error Spearman association with tile count, '
        'sampling density, source area, tissue-grid coverage and sampled annotation area. '
        'These diagnostics are post-selection, exploratory and uncorrected for multiplicity; annotations are not predictor features.','',
        '## Probability quality and complexity','']
    native_find=lambda model,split,feature,outcome: next(r for r in native_correlations if
        (r['task'],r['model'],r['split'],r['truth_class'],r['feature'],r['outcome'])==
        ('low_high',model,split,'high_grade',feature,outcome))
    capture_train=native_find('zero_shot_mean','train','gp45_annotation_capture_fraction','error')
    capture_cal=native_find('zero_shot_mean','calibration','gp45_annotation_capture_fraction','error')
    lines[-2:-2]=[
        f"Original mean grade-error association with GP4/5 capture is rho={capture_train['spearman_rho']:.3f} "
        f"across {capture_train['slides']} high-grade training slides and rho={capture_cal['spearman_rho']:.3f} "
        f"across {capture_cal['slides']} usable-mask high-grade known-cal slides. "
        'This is compatible with sampling contributing to some errors, without establishing the cause. '
        'Known-cal slide aa9be7d9f82e983d21e2746078b877d9 is missed by original mean despite 99.79% native GP4/5 capture '
        'and full eligible-grid sampling; selected-probe error 8d96e24f96029fb89ad33d017f1fbcfc has 99.64% capture and full grid sampling. '
        'Thus missed predictions cannot all be attributed to sampling.', '']
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
        f"Recorded model failures: `{selection['failures']}`. Every attempted C/fold is in `run/fold_audit.json`.", '',
        '## Reproducibility and limits','',
        'The JSON/NPZ predictors contain all scaler/linear coefficients and fixed feature transforms; inference uses NumPy only. '
        'Every result, model parameter and input receipt is hash-recorded. Frozen model selection uses train-only grouped nested CV. '
        'Grouping is by known patient if available, otherwise slide ID; true patient independence remains unknown. '
        'Repeated donors, contamination outcomes and calibration results did not select these models. '
        'The original S2 result is immutable; a changed scorer defines a new experiment.']
    if acceptance:
        lines += ['', '## Strict historical adapter acceptance','',
            f"The initial research adapter matched all 480 historical zero-shot labels/predictions but {acceptance['previous_roundoff_vectors']}/480 "
            f"score vectors differed by at most {acceptance['previous_maximum_absolute_cosine_difference']:.9g}. "
            'The cause was float32 reduction strides after reducing text classes too early. '
            'The corrected adapter preserves all four text classes and legacy column-indexing before pooling. '
            f"Separate CPU job {acceptance['slurm_job_id']} verified {acceptance['historical_exact_comparisons']}/480 historical score vectors exactly, "
            f"plus {acceptance['linear_known_calibration_predictions_exact']} frozen linear known-cal predictions exactly. "
            'No linear probe was retrained and no primary was changed. Initial job artifacts remain immutable; '
            'the margin distributions and native-annotation case studies here use corrected zero-shot margins. '
            'The copied initial `run/diagnostic_correlations.json` remains explicitly associated with the original numerical adapter.']
    output.mkdir(parents=True,exist_ok=False)
    (output/'report.md').write_text('\n'.join(lines)+'\n')
    write_json(output/'margin_distributions.json',margins)
    write_json(output/'paired_model_comparisons.json',paired)
    write_json(output/'native_annotation_case_studies.json',joined)
    write_json(output/'native_annotation_correlations.json',native_correlations)
    write_json(output/'provenance.json',dict(files={str(p.relative_to(directory)):file_sha256(p) for p in directory.rglob('*') if p.is_file()},
        coverage_receipt_sha256=file_sha256(coverage_receipt), joined_slides=len(permitted),
        adapter_verification_sha256=file_sha256(Path(adapter_verification)/'verification.json') if adapter_verification else None,
        cached_native_annotations_sha256=file_sha256(cached_native) if cached_native else None,
        report_generator_sha256=file_sha256(__file__),
        source_commit=execution['source_commit'],test_slides_scored=False,clinical_validity_verified=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p.add_argument('--coverage-receipt',required=True)
    p.add_argument('--adapter-verification')
    p.add_argument('--cached-native-annotations')
    a=p.parse_args();summarize(a.input,a.output,a.coverage_receipt,a.adapter_verification,a.cached_native_annotations)
