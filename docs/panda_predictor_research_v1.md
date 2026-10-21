# Frozen-CONCH prediction research v1

This is development-only CPU research. It preserves the CONCH checkpoint, image
embeddings, fixed text prompts, original zero-shot models and historical results.
No final-test arrays or predictions may be opened. The 24 known calibration
slides have been inspected repeatedly; results on them are descriptive development
measurements, not independent validation.

The configuration is committed before execution. Both tasks compare unchanged
zero-shot mean/top-1%/top-5% pooling, balanced L2 logistic regression on the
512-dimensional tile mean, and balanced L2 regression on concatenated mean,
coordinatewise maximum, and coordinatewise top-five-tile means (1,536 dimensions).
K=5 is fixed even for slides with different tile counts; slides with fewer tiles
use all their tiles for that block. This transform does not select tiles using
annotations or disease scores. Coordinates, mask labels, tissue coverage and slide
identity are never predictive features.

The train split supplies 72 benign/cancer slides and 48 low/high slides. A
four-fold stratified grouped outer CV generates one out-of-fold prediction per
training slide. Three-fold inner CV chooses C from 0.01, 0.1 and 1, maximizing
balanced accuracy and breaking ties toward stronger regularization. Every scaler
and regression is fit only on that fold's training portion. Groups are verified
patient IDs where available, otherwise unique slide IDs; patient independence
remains unverified. All attempted model/C fits and failures are recorded.

The primary model maximizes train out-of-fold balanced accuracy, then worst-class
recall, then the configured preference for simpler models. The primary and its
parameters are written before opening known calibration arrays. A final three-fold
training-only CV chooses C for the all-training fit. Choosing among five outer-CV
results introduces selection optimism: the reported intervals resample unique
slides, conditional on fitted predictions, and do not capture refitting or model
selection uncertainty. Fresh validation is required.

The preset S2 engineering-readiness screen is balanced accuracy >=0.70 and both
class recalls >=0.60 on training out-of-fold predictions. It checks whether a
scorer merits a bounded engineering comparison; it is not a clinical criterion
or independent validation. Calibration and contamination outcomes cannot change
the primary or this screen. The original S2 negative result remains unchanged.

An attention/MIL model is deferred: only 48 grade training slides with unknown
patient IDs cannot justify additional learned tile-weight parameters and their
complexity tuning. This is an explicit infeasibility decision, not an unreported
failed model or proof that MIL cannot work.

Outputs include raw per-slide predictions/margins, class confusion/recall and
Wilson intervals, balanced-accuracy slide bootstrap, Brier score and five-bin ECE
for logistic outputs. Class-balanced logistic probabilities are uncalibrated;
cosine similarities are never presented as probabilities. Diagnostic correlations
use sampled annotation area only after model selection, with missing/corrupt masks
kept unknown. Sampled area is not full-slide tumor burden and cannot diagnose tile
ground truth from a slide grade. Associations are exploratory and uncorrected for
multiple comparisons.

Models are portable JSON plus hash-verified NPZ, never pickle. Import
`floater_finder.predictors.load_predictor(directory)` and call
`predictor.score_slide(slide)` to enforce the checkpoint identity. The lower-level
`predictor(feats)` accepts a finite matrix and returns prediction, class scores,
signed positive-minus-negative margin and optional uncalibrated probability.
Linear class scores are symmetric logits; zero-shot scores remain original pooled
cosines. Scores from different model kinds are not comparable probability scales.
