# Frozen-CONCH predictor research v1

Real CPU job 23068979; source `0f2fc5fa3413ac3c7c5d1cd81181fd9c57017140`. No new image inference, GPU use, dataset download or test prediction. The 24 known calibration slides are repeatedly inspected development data, not independent validation.

## Every evaluated model

| Task/model | Training OOF confusion | OOF BA | OOF recalls | Known-cal confusion | Known-cal BA | Known-cal recalls |
|---|---|---:|---|---|---:|---|
| benign_cancer/zero_shot_mean | [[15, 9], [7, 41]] | 0.740 | [0.625, 0.8541666666666666] | [[5, 3], [5, 11]] | 0.656 | [0.625, 0.6875] |
| benign_cancer/zero_shot_top1pct | [[9, 15], [5, 43]] | 0.635 | [0.375, 0.8958333333333334] | [[4, 4], [1, 15]] | 0.719 | [0.5, 0.9375] |
| benign_cancer/zero_shot_top5pct | [[18, 6], [5, 43]] | 0.823 | [0.75, 0.8958333333333334] | [[5, 3], [1, 15]] | 0.781 | [0.625, 0.9375] |
| benign_cancer/linear_mean | [[24, 0], [19, 29]] | 0.802 | [1.0, 0.6041666666666666] | [[7, 1], [6, 10]] | 0.750 | [0.875, 0.625] |
| benign_cancer/linear_mean_max_topk | [[23, 1], [13, 35]] | 0.844 | [0.9583333333333334, 0.7291666666666666] | [[6, 2], [5, 11]] | 0.719 | [0.75, 0.6875] |
| low_high/zero_shot_mean | [[22, 2], [11, 13]] | 0.729 | [0.9166666666666666, 0.5416666666666666] | [[8, 0], [4, 4]] | 0.750 | [1.0, 0.5] |
| low_high/zero_shot_top1pct | [[7, 17], [2, 22]] | 0.604 | [0.2916666666666667, 0.9166666666666666] | [[2, 6], [0, 8]] | 0.625 | [0.25, 1.0] |
| low_high/zero_shot_top5pct | [[8, 16], [2, 22]] | 0.625 | [0.3333333333333333, 0.9166666666666666] | [[3, 5], [0, 8]] | 0.688 | [0.375, 1.0] |
| low_high/linear_mean | [[20, 4], [7, 17]] | 0.771 | [0.8333333333333334, 0.7083333333333334] | [[6, 2], [4, 4]] | 0.625 | [0.75, 0.5] |
| low_high/linear_mean_max_topk | [[24, 0], [7, 17]] | 0.854 | [1.0, 0.7083333333333334] | [[8, 0], [3, 5]] | 0.812 | [1.0, 0.625] |

Confusion rows are true negative/positive class, columns predicted negative/positive. Benign/cancer uses 72 training and 24 known-cal slides (24/48 and 8/16 supports); low/high uses 48 training and 16 known-cal slides (24/24 and 8/8). All three original zero-shot poolers remain unchanged. Supervised training metrics are outer out-of-fold predictions, not resubstitution.

## Frozen primary and readiness

- **benign_cancer: linear_mean_max_topk**; train OOF BA 0.844, recalls [0.9583333333333334, 0.7291666666666666]; 95% conditional slide-bootstrap BA interval [0.7604166666666667, 0.9166666666666667]; preset engineering screen passes: True.
- **low_high: linear_mean_max_topk**; train OOF BA 0.854, recalls [1.0, 0.7083333333333334]; 95% conditional slide-bootstrap BA interval [0.75, 0.9375]; preset engineering screen passes: True.

The primary was frozen before opening known-calibration arrays and before any new contamination outcomes. The screen (BA >=0.70, each recall >=0.60) is an engineering preset, not clinical validity or independent validation. Selection among five OOF results is optimistic; bootstrap intervals do not include refitting/model-selection uncertainty. Fresh development-validation remains necessary.

The benign/cancer primary has higher training OOF balanced accuracy than the original top-5% scorer, but lower balanced accuracy on known calibration. This is not a validated benign/cancer improvement. The low/high primary improves both descriptive point estimates, but improves known-cal high-grade recall by only one slide (5/8 versus 4/8); uncertainty and repeated calibration use prevent an independent-success claim. Raw cosine margins and logistic margins have different scales and are compared within model only.

## Clean error diagnosis

| Task/primary | Split/slide | Truth → prediction | Margin | Tiles | Tissue-grid coverage | Sampled cancer annotation mm² | Native GP4/5 annotation mm² | GP4/5 capture |
|---|---|---|---:|---:|---:|---:|---:|---:|
| benign_cancer/linear_mean_max_topk | train/f0bb29042dfb17421aac02138f8e9d20 | benign → cancer | 0.2438 | 512 | 0.5156092648539778 | 0.0 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/a65a095302fbc94c8e21ae65e1ccd17e | cancer → benign | -0.2804 | 512 | 0.6274509803921569 | 0.6497399770815436 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/530d4ae320630f972f49d861a4724fb1 | cancer → benign | -0.1547 | 473 | 1.0 | 0.2232783263937663 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/d1088ba933bd7066a3a777f542f61fa6 | cancer → benign | -0.3239 | 376 | 1.0 | 0.40257041118951226 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/63080d06c66488c4c30285e0363ca0ad | cancer → benign | -6.2754 | 512 | 0.8951048951048951 | 0.153211035629998 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/a979f5e3d61ebeec3dcbe8943c9316ca | cancer → benign | -2.0754 | 512 | 0.5669988925802879 | 0.005209780340170879 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/46d067b212c4dda9e6f87c8b82f22d79 | cancer → benign | -0.0253 | 386 | 1.0 | 0.33706333287232226 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/3c685ed0f92e30f6ffeb5cea7cef5994 | cancer → benign | -6.3129 | 100 | 1.0 | 0.0 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/dc7254ab21584e852fe556646c86d6f4 | cancer → benign | -2.1218 | 512 | 0.5669988925802879 | 0.2341318778501767 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/e02a4e6752db30ddfe21a7c2cab7470b | cancer → benign | -1.0959 | 441 | 1.0 | 0.004552648337191066 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/615b8a4e40699ea384e5f518ac0c68b4 | cancer → benign | -5.6070 | 252 | 1.0 | 0.024314829623926372 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | train/dd1110c6430e3b1ac732be548a089886 | cancer → benign | -2.6520 | 460 | 1.0 | 0.020806028382116187 | 0.020806028382116183 | 1.0000000000000002 |
| benign_cancer/linear_mean_max_topk | train/36dd11dbc0aba4413623bdc44775e6fe | cancer → benign | -0.1641 | 448 | 1.0 | 0.3074488991092567 | 0.30800297012184097 | 0.9982010854883475 |
| benign_cancer/linear_mean_max_topk | train/7f15c706a91ae8c7ccbfaae1897aa024 | cancer → benign | -2.6574 | 439 | 1.0 | 0.5631555079579845 | 0.5665385558812391 | 0.9940285654204198 |
| benign_cancer/linear_mean_max_topk | calibration/a213e4e689988738b8fb764e958ca497 | benign → cancer | 1.1884 | 191 | 1.0 | 0.0 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | calibration/d383a65adb84e2f3032f0c68246224eb | benign → cancer | 0.0980 | 512 | 0.7211267605633803 | 0.0 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | calibration/d38a9db63e100d405ddb1a932b53d92f | cancer → benign | -2.1076 | 398 | 1.0 | 0.4285134153589515 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | calibration/03849b0243900d79446bb27849dc0bb2 | cancer → benign | -1.9656 | 512 | 0.9696969696969697 | 0.1710150580992208 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | calibration/9b56f501c6765027cce8a1a8ad797767 | cancer → benign | -0.4115 | 512 | 0.6297662976629766 | 0.04212168863416922 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | calibration/ebc0cf09e9f77d222af0b8015c409a01 | cancer → benign | -0.3049 | 512 | 0.8707482993197279 | 0.2294374024619828 | 0.0 | None |
| benign_cancer/linear_mean_max_topk | calibration/20be7c34058e2f24ef3bb0cda3c376d5 | cancer → benign | -0.4626 | 512 | 0.6221142162818954 | 0.1390954620005223 | 0.0 | None |
| low_high/linear_mean_max_topk | train/dd1110c6430e3b1ac732be548a089886 | high_grade → low_grade | -1.4295 | 460 | 1.0 | 0.020806028382116187 | 0.020806028382116183 | 1.0000000000000002 |
| low_high/linear_mean_max_topk | train/955f09b99664b07b0cf18768c84f2253 | high_grade → low_grade | -4.2235 | 512 | 0.5475935828877005 | 0.26043228618814285 | 0.509160058613858 | 0.5114939433724359 |
| low_high/linear_mean_max_topk | train/9c2eafb5480094f718bc40213531b7d5 | high_grade → low_grade | -1.6006 | 512 | 0.6392009987515606 | 0.7955419675671533 | 1.2668474407546808 | 0.6279698264956328 |
| low_high/linear_mean_max_topk | train/8efb75ef39c5b55cffeac6d3d19cf238 | high_grade → low_grade | -0.3004 | 512 | 0.6117084826762246 | 1.8600806841756745 | 2.9130935891060306 | 0.6385241761993976 |
| low_high/linear_mean_max_topk | train/7f15c706a91ae8c7ccbfaae1897aa024 | high_grade → low_grade | -3.2217 | 439 | 1.0 | 0.5631555079579845 | 0.5665385558812391 | 0.9940285654204198 |
| low_high/linear_mean_max_topk | train/9ffb9e9e7be39a7af216779a06a6302b | high_grade → low_grade | -2.9215 | 131 | 1.0 | 0.8354870837252655 | 0.8429311128755678 | 0.9911688760367289 |
| low_high/linear_mean_max_topk | train/d0cb73c9ad19c13c6fe93cc2c61cc073 | high_grade → low_grade | -4.4781 | 323 | 1.0 | 1.6102494972931558 | 1.6134708623782676 | 0.9980034563001878 |
| low_high/linear_mean_max_topk | calibration/8d96e24f96029fb89ad33d017f1fbcfc | high_grade → low_grade | -1.2891 | 117 | 1.0 | 0.7892703753718082 | 0.7920917881730909 | 0.9964380229117258 |
| low_high/linear_mean_max_topk | calibration/8fae0151f134c7499934dfe20c700eb9 | high_grade → low_grade | -0.5316 | 512 | 0.4995121951219512 | 1.0085775443374934 | 1.9993179732271988 | 0.5044608000544797 |
| low_high/linear_mean_max_topk | calibration/1e73a4d3e89de944a6c309defde99839 | high_grade → low_grade | -1.9477 | 512 | 0.7975077881619937 | 0.38224659478080597 | 0.4932300442452194 | 0.7749864373443648 |

Annotation area is limited to exported tile footprints; no full-slide tumor-area claim is made. Source area is the rectangular image bounding area, not tissue area. Coverage is fraction of eligible RGB tissue-grid cells sampled. The separate native GP4/5 and capture measurements come from the earlier verified CPU mask receipt, joined only after the primary was frozen. Native GP3+4+5 annotated areas are available for 92/96 development slides from existing hash-verified mask-audit JSON, with no WSI reread. Three original profile slides lack standalone cached audits and one corrupt mask remains unknown. This is native annotation area, not independently verified cancer burden. Case JSON separates full-native GP3+4+5, native GP4/5 and sampled GP3+4+5 areas. Slide grade never assigns a label to every tile. Missing masks remain unknown.

## Diagnostic associations

The companion JSON reports every per-model/per-split/per-class margin/error Spearman association with tile count, sampling density, source area, tissue-grid coverage and sampled annotation area. These diagnostics are post-selection, exploratory and uncorrected for multiplicity; annotations are not predictor features.

Original mean grade-error association with GP4/5 capture is rho=-0.513 across 24 high-grade training slides and rho=-0.289 across 7 usable-mask high-grade known-cal slides. This is compatible with sampling contributing to some errors, without establishing the cause. Known-cal slide aa9be7d9f82e983d21e2746078b877d9 is missed by original mean despite 99.79% native GP4/5 capture and full eligible-grid sampling; selected-probe error 8d96e24f96029fb89ad33d017f1fbcfc has 99.64% capture and full grid sampling. Thus missed predictions cannot all be attributed to sampling.

## Probability quality and complexity

- benign_cancer/linear_mean: OOF Brier 0.1868, ECE 0.1884; known-cal Brier 0.2035, ECE 0.1960.
- benign_cancer/linear_mean_max_topk: OOF Brier 0.1597, ECE 0.1952; known-cal Brier 0.1565, ECE 0.1428.
- low_high/linear_mean: OOF Brier 0.1406, ECE 0.1090; known-cal Brier 0.2515, ECE 0.2044.
- low_high/linear_mean_max_topk: OOF Brier 0.1529, ECE 0.1730; known-cal Brier 0.1602, ECE 0.1320.

Balanced logistic outputs are uncalibrated and class weighting changes class priors. No probability calibration mapping was fitted. Cosine similarities have no Brier score because they are not probabilities. Model 4 (attention/MIL) was deferred before execution: 48 grade training slides with unknown patient IDs do not support credible tuning of additional learned tile-weight parameters.

Recorded model failures: `[]`. Every attempted C/fold is in `run/fold_audit.json`.

## Reproducibility and limits

The JSON/NPZ predictors contain all scaler/linear coefficients and fixed feature transforms; inference uses NumPy only. Every result, model parameter and input receipt is hash-recorded. Frozen model selection uses train-only grouped nested CV. Grouping is by known patient if available, otherwise slide ID; true patient independence remains unknown. Repeated donors, contamination outcomes and calibration results did not select these models. The original S2 result is immutable; a changed scorer defines a new experiment.

## Strict historical adapter acceptance

The initial research adapter matched all 480 historical zero-shot labels/predictions but 158/480 score vectors differed by at most 3.87430191e-07. The cause was float32 reduction strides after reducing text classes too early. The corrected adapter preserves all four text classes and legacy column-indexing before pooling. Separate CPU job 23069033 verified 480/480 historical score vectors exactly, plus 80 frozen linear known-cal predictions exactly. No linear probe was retrained and no primary was changed. Initial job artifacts remain immutable; the margin distributions and native-annotation case studies here use corrected zero-shot margins. The copied initial `run/diagnostic_correlations.json` remains explicitly associated with the original numerical adapter.
