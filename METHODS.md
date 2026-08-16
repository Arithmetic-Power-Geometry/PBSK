# PBSK v4.0.0 — Computational Methods

## Scientific question

PBSK tests whether regions of scientific knowledge that later become transformative differ, *before the event*, from comparable regions that do not undergo the same future transition.

The conceptual sequence is derived from *THE IMPOSSIBLE IDEA: How New Realities Enter the World* (Akhtar/Shunya, 2026): possibility, question, pattern, imagination, insight, discovery, and transformation.

## Two-cohort design

### Landmark cohort

Twelve recognized historical landmark cases and their controls are retained for continuity with PBSK v3. Because v3 results have already been inspected, v4 labels this cohort **exploratory** for newly emphasized signals.

### Independent power-validation cohort

OpenAlex research topics are sampled independently. Topics with adequate pre-cutoff literature are characterized using annual work counts. By default, 2018 is the information cutoff and 2019–2023 is the future outcome window. Topics in the upper future-growth tail form the positive class. Controls are selected from non-positive topics within the same domain using only **pre-cutoff volume and pre-cutoff momentum** for matching.

No predictor used in PBSK is allowed to access post-cutoff documents when predicting the power-validation outcome.

## Retrieval

v3 retrieved the first N results and capped region windows at 300. v4 replaces this with deterministic random sampling through OpenAlex `sample` and `seed`, using up to 600 records per landmark window and 300 records per power-validation topic window. The sampling query and seed are cached and recorded in manifests.

This strategy reduces rank-order truncation while keeping the API footprint bounded and reproducible.

## Coverage gate

Inferential and predictive models use only region/cutoff observations satisfying pre-specified coverage requirements. Defaults are at least 60 documents, at least five publication years represented, and nonzero recent and prior activity. Sparse cases remain in descriptive/QC outputs but cannot silently drive inferential results.

## Book-stage architecture

Raw proxies are grouped into stage-level constructs. The v4 book-wide score gives equal weight to six pre-discovery stages rather than equal weight to every raw variable. A geometric mean is used so that the score represents joint organization across the arc instead of allowing one very high component to compensate fully for a missing stage.

## v3-derived core hypothesis

`core_geometry_score` combines structured knowledge-gap geometry, cross-domain collision, and sequence-order agreement. Because this hypothesis was motivated by inspected v3 results, it is **not** treated as confirmatory evidence in the original landmark cohort. Its confirmatory test is the independent v4 power-validation cohort.

## Multiplicity

Hypothesis tests are split into pre-specified confirmatory and exploratory families. Benjamini–Hochberg false-discovery-rate correction is applied within offset × family. This avoids both uncorrected multiple testing and an unnecessarily broad correction across unrelated exploratory questions.

## Predictive evaluation

Predictions use grouped out-of-fold cross-validation so all observations from a matched group remain in the same fold. Models include conventional activity/citation baselines, legacy PBS, stage-balanced book-wide PBSK, core geometry, augmented baselines, a full logistic theory model, random forest, and histogram gradient boosting.

Primary metrics are ROC-AUC, PR-AUC, Brier score, and balanced accuracy. Group-bootstrap 95% confidence intervals are reported. Incremental-value tables directly compare augmented models with the activity/citation baseline using matched bootstrap resampling by group.

## Temporal locking

For a landmark year T, features are evaluated at T−5, T−3, and T−1. The leakage audit checks that no work used for prediction exceeds the corresponding cutoff. The power-validation cohort uses the same pre-cutoff logic and defines outcomes only in the later window.

## Transformation

Post-event transformation is evaluated only through years that actually exist at the configured `current_year`. Incomplete T+10 horizons for recent landmarks are therefore reported as incomplete rather than silently filled with nonexistent future data.

## Replication

PubMed is an independent biomedical source. Applicable landmark regions and Life-realm power-validation topics are queried independently. Cross-source agreement and replication hypothesis tables are generated separately from the OpenAlex training/evaluation path.

## Guardrail

No AUC, p-value, effect size, confidence interval, or favorable conclusion is hard-coded. A successful run confirms software integrity only. Scientific claims must follow the generated evidence.
