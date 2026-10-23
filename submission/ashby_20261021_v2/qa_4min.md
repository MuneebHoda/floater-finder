# Four-minute Q&A preparation

Eight concise answers provide approximately four minutes of material at a measured pace, including pauses. Answer the question asked rather than reciting the entire document. The numbers below refer to development data.

1. **Does this detect real floaters?**

   We have not established that. The donor tissue contains real annotated cancer, but its insertion and translated placement are synthetic. We demonstrate model sensitivity and test review-policy feasibility. Natural-floater detection requires adjudicated real contaminants and external clinical validation.

2. **What does the “new error” endpoint mean?**

   It means an originally correct host changes to a prediction inconsistent with its original slide label. The synthetic bag truly contains donor cancer, so this is not proof of misrecognizing cancer pixels. Five clean-correct benign calibration hosts define the primary S1 denominator. Initial errors remain separate.

3. **Why can’t dependence identify contamination?**

   Genuine annotated cancer can legitimately drive a prediction. Excluding an unmodified component containing native cancer changes cancer to benign. Decision-only hypothetical filtering damages 3/20 originally correct clean predictions. Floater Finder preserves original tissue and supplies review evidence rather than automatically discarding a component.

4. **Why reject a detector with no clean alerts?**

   Combined v1 also misses every calibration fragment: 0/40 hits. Silence is not useful detection. Moreover, 0/24 observed clean alerts has a 95% Wilson upper bound of 13.8%, so this small sample does not establish a population rate below the 10% review target.

5. **Did S2 show grade upgrades?**

   The primary mean scorer shows no new low-to-high calibration errors, 0/8 at every tested primary dose. Its clean high-grade sensitivity is only 4/8. Secondary top pooling flips tiny clean-correct denominators and is already poorly specific. These are binary zero-shot model endpoints, not clinical Gleason Grade Group upgrades.

6. **Did ranked detector v2 improve on v1?**

   No useful validated improvement emerged. The selected rank detects 22/120 training fragments but 0/40 on known calibration. Unbudgeted top-one visual-plus-relevance review hits 21/40 but alerts on all 24 clean slides and flags 14 native cancer components. Previously seen calibration makes this iterative development.

7. **Are the trials independent patients?**

   No. S1 reuses 32 hosts and 21 donors across nested doses. S2 has 760 records across 32 hosts and 37 donors, with only 55 distinct source slides. Patient identifiers are unavailable. We retain unique-host denominators and disclose donor reuse instead of treating trials as independent patients.

8. **What is the contribution if both detectors fail?**

   A verified real-data pipeline, a reproducible model-sensitivity experiment, genuine-cancer safety controls and explicit rejection gates. We preserve negative results rather than tune the held-out set. Future work needs realistic contaminants, useful burden-controlled review and a new frozen protocol before an explicitly authorized independent test.

## Follow-up details

- **Components:** RGB foreground at pyramid factor 16 is a geometry proxy. There is no gap filling or pathologist-confirmed whole-piece boundary. Empty exclusions remain unevaluable.
- **Placement:** All 40 calibration donor components lie beyond the observed native right edge. Spatial performance may exploit this construction. It cannot establish natural-floater generalization.
- **S2 capacity:** Eight GP5-positive 10% calibration trials are unavailable because the chosen connected component has 37 tiles but needs 40–52. Unavailable is not a zero error rate.
- **S2 native safety:** Mean exclusion of native GP4/5 components changes high to low on six training and two calibration slides. Those are genuine annotated regions, not detector flags.
- **Compute:** Cached embeddings support S1, S2 and review analysis on CPU. No new GPU model or inference accompanied these extensions.
- **Clinical scope:** The zero-shot baselines are engineering scorers. No diagnostic deployment, specimen attribution, patient independence or final-test performance is established.

## Numeric reference

| Measurement | Verified result |
|---|---:|
| Cohort / embeddings | 120 slides / 50,729 |
| Splits | 72 train / 24 calibration / 24 untouched test |
| Clean S1 primary calibration | 20/24 correct, 78.1% balanced accuracy |
| S1 primary induced errors by positive dose | 1/5, 1/5, 2/5, 2/5, 2/5 |
| Combined v1 | 0/40 hits, 0/24 clean-slide alerts |
| Decision only | 8/40 hits, 4/24 alerts, 3/20 hypothetical clean damage |
| Spatial only | 32/40 hits, 19/24 alerts, 3.583 components/slide |
| S2 primary clean calibration | 12/16 correct, low 8/8, high 4/8 |
| S2 primary GP4/5 calibration | 0/8 new errors at each requested positive dose |
| S2 exact oracle / exclusions | 760/760 passes / eight GP5 10% exclusions |
| Selected v2 known calibration | 0/40 hits, 1/24 alerts, 0/20 damage |
| Unbudgeted top-one visual + relevance | 21/40 hits, 24/24 alerts, 14 native cancer components flagged |
| Final test | 24 slides unscored, scientifically blocked |
