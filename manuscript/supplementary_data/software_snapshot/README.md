# PBSK v4.0.0

**Possibility-to-Breakthrough Scientific Knowledge (PBSK)** is a reproducible computational research system for testing whether scientific knowledge contains measurable precursors to future breakthrough formation.

Repository: https://github.com/Arithmetic-Power-Geometry/PBSK

License: **Apache License 2.0**

Conceptual source:

> Mohammad Amir Khusru Akhtar (Shunya). (2026). *THE IMPOSSIBLE IDEA: How New Realities Enter the World*. https://a.co/d/03buY0qI

The source book organizes creativity as:

**Possibility → Question → Pattern → Imagination → Insight → Discovery → Transformation**

PBSK converts this narrative into literature-level, temporally locked proxies. It does not claim to directly measure private cognition.

## What changed in v4

v4 is a methodological rebuild after the v3 landmark experiment. It does not alter the theory to manufacture favorable results. Instead it strengthens the test:

- the 12 historical landmarks remain a transparent **exploratory landmark cohort**;
- a new **independent prospective power-validation cohort** is generated from OpenAlex topics;
- the power cohort targets approximately **120 future-emergent topics**, each matched to controls using only pre-cutoff information;
- future topic growth (2019–2023 by default) defines the validation outcome, while every PBSK predictor is restricted to information available at or before the 2018 cutoff;
- the v3 observation that collision, structured gaps, and temporal ordering may be informative is condensed into `core_geometry_score`, but that score is treated as confirmatory only in the independent v4 cohort;
- OpenAlex retrieval uses reproducible random sampling rather than taking the first N search results;
- the old 300-record truncation is removed; landmark windows use up to 600 sampled works and power-validation topic windows up to 300;
- pre-specified coverage rules exclude extremely sparse regions from inferential and predictive analyses;
- the book-wide score is now hierarchical: equal weight is given to **book stages**, not to the number of raw proxy variables within each stage;
- predictive results include grouped out-of-fold evaluation, ROC-AUC, PR-AUC, Brier score, and group-bootstrap confidence intervals;
- incremental value is tested directly against the activity/citation baseline;
- FDR correction is applied within pre-specified confirmatory and exploratory families;
- PubMed provides an independent biomedical replication layer for applicable landmark and power-validation regions;
- incomplete post-breakthrough horizons are capped at the configured current year rather than pretending that future years already exist.

## Book-wide measurement architecture

PBSK computes observable proxies for possibility pressure, question pressure, anomalies/productive confusion, boundary tension, pattern formation, cross-domain similarity, analogical transfer, bridge formation, idea collision, surprise geometry, insight coherence, nonlinear leap, originality risk, structured knowledge gaps, momentum, recombination, convergence, and sequence-order agreement.

These are organized into six pre-discovery stage scores:

1. `stage_possibility`
2. `stage_question`
3. `stage_pattern`
4. `stage_imagination`
5. `stage_insight`
6. `stage_discovery_readiness`

The stage-balanced `bookwide_pbsk` is the geometric mean of these six pre-specified stages. `core_geometry_score` is a separate v3-derived hypothesis requiring independent v4 validation.

## Data sources

- **OpenAlex API** — primary scholarly knowledge corpus and topic-based prospective validation.
- **PubMed E-utilities** — independent biomedical replication.

The complete bulk datasets are not downloaded. PBSK retrieves only the records required for the experiment and caches them locally/GitHub Actions for reproducibility.

## GitHub Actions

Repository secrets:

- `OPENALEX_API_KEY` — required for full mode.
- `NCBI_API_KEY` — recommended for PubMed throughput.

Optional repository variable:

- `PBSK_CONTACT_EMAIL` — contact email supplied to NCBI E-utilities.

Run **Actions → PBSK Reproducible Run → Run workflow → full**.

The workflow performs credential preflight, tests the package, restores the scholarly cache, runs the full experiment, validates temporal integrity, packages all outputs, and saves the refreshed cache.

## Main outputs

A successful full workflow creates `pbsk-results-full.zip` containing, among other outputs:

- landmark and matched-control feature tables;
- power-validation topic cohort and controls;
- quality/coverage metadata;
- landmark and power-validation hypothesis tests;
- grouped out-of-fold predictions;
- predictive performance with bootstrap confidence intervals;
- incremental-value tests against conventional baselines;
- temporal T−5/T−3/T−1 evaluation;
- ablation analysis;
- PubMed replication and cross-source agreement;
- post-breakthrough transformation analyses;
- temporal leakage and retrieval QC;
- publication figures;
- `run_summary.json`, modeling contracts, and HTML results report.

## Scientific interpretation

A green workflow means the computation completed and passed integrity checks. It does **not** mean the theory was confirmed. Empirical support depends on the effect sizes, uncertainty intervals, multiplicity-adjusted tests, out-of-sample prediction, incremental value, independent power-validation cohort, and PubMed replication generated by that run.

## Citation

If PBSK is used in academic work, cite the software repository and the conceptual source identified in `CITATION.cff`.
