# PBSK v4.0.0

**Possibility-to-Breakthrough Scientific Knowledge (PBSK)** is an open and reproducible **science-of-science framework** for investigating whether the evolving structure of scholarly knowledge contains measurable signals associated with future scientific emergence.

**Repository:** https://github.com/Arithmetic-Power-Geometry/PBSK  
**DOI:** https://doi.org/10.5281/zenodo.21967787  
**License:** Apache License 2.0

---

## Conceptual Foundation

PBSK is computationally motivated by:

> Mohammad Amir Khusru Akhtar (Shunya). (2026). *THE IMPOSSIBLE IDEA: How New Realities Enter the World*. https://a.co/d/03buY0qI

The book organizes the emergence of new realities through the progression:

**Possibility → Question → Pattern → Imagination → Insight → Discovery → Transformation**

PBSK translates this conceptual progression into observable, literature-level computational proxies that can be evaluated using temporally locked scholarly data.

The framework does **not** claim to directly measure private cognition. Constructs such as questioning, imagination, insight, and discovery readiness are operationalized as measurable properties of scholarly knowledge structures.

---

## Research Question

PBSK addresses a fundamental question in the **science of science**:

> **Does the organization of scientific knowledge exhibit detectable structural precursors before a research field visibly emerges?**

Rather than treating scientific breakthroughs as events that can only be understood retrospectively, PBSK investigates whether emerging scientific regions display measurable structural organization years before their later growth becomes visible.

---

## PBSK v4.0.0

Version 4.0.0 substantially strengthens the empirical architecture developed in earlier PBSK experiments.

The original **12 historical scientific landmarks** are retained as a transparent exploratory cohort.

A separate prospective validation experiment evaluates the framework using approximately:

- **120 future-emergent OpenAlex topics**
- **240 matched control topics**

The design maintains strict temporal separation.

All predictive features are constructed from information available at or before the **2018 cutoff**, while subsequent scientific emergence is evaluated during **2019–2023**.

This architecture separates hypothesis generation from independent validation and reduces the risk of retrospective result selection.

---

## Major Methodological Features

PBSK v4.0.0 includes:

- independent prospective power validation;
- temporally locked feature construction;
- pre-cutoff matching of future-emergent topics and controls;
- reproducible OpenAlex sampling;
- expanded scholarly sampling;
- explicit minimum-coverage requirements;
- hierarchical stage-balanced PBSK construction;
- grouped out-of-fold predictive evaluation;
- ROC-AUC, PR-AUC and Brier-score assessment;
- group-bootstrap confidence intervals;
- direct incremental-value testing against conventional bibliometric baselines;
- temporal analysis at **T−5, T−3 and T−1**;
- confirmatory and exploratory hypothesis families;
- false-discovery-rate correction;
- stage and construct ablation analysis;
- PubMed biomedical replication where applicable;
- post-emergence transformation analysis;
- temporal-leakage auditing;
- retrieval-quality control;
- complete machine-readable output generation.

---

## Book-Wide Measurement Architecture

PBSK operationalizes multiple dimensions of emerging scholarly structure, including:

- possibility pressure;
- question pressure;
- structured knowledge gaps;
- anomalies and productive confusion;
- boundary tension;
- pattern formation;
- cross-domain similarity;
- analogical transfer;
- bridge formation;
- cross-domain collision;
- surprise geometry;
- insight coherence;
- nonlinear leap;
- originality risk;
- momentum;
- recombination;
- convergence;
- sequence-order agreement.

These measurements are organized into six pre-discovery stages:

1. `stage_possibility`
2. `stage_question`
3. `stage_pattern`
4. `stage_imagination`
5. `stage_insight`
6. `stage_discovery_readiness`

The stage-balanced composite,

`bookwide_pbsk`

is constructed from the six stage scores rather than by simply averaging all raw variables.

This prevents stages containing more proxy variables from receiving disproportionate influence.

A separate:

`core_geometry_score`

captures the previously identified interaction among structured knowledge gaps, cross-domain collision, and temporal sequence organization.

Its evaluation in v4 is separated from the exploratory landmark analysis so that previously observed patterns can be tested on an independent cohort.

---

## Temporal Architecture

PBSK examines scholarly structure before scientific emergence at multiple temporal distances:

**T−5 → T−3 → T−1 → Emergence**

This makes it possible to investigate whether structural signals are already detectable several years before the outcome and whether those signals reorganize as emergence approaches.

Post-emergence analysis additionally examines transformation after the landmark event while preventing unavailable future years from being treated as observed data.

---

## Data Sources

PBSK uses two complementary scholarly information systems.

### OpenAlex

**OpenAlex** provides the primary large-scale scholarly corpus and the topic-level prospective validation environment.

It supports:

- scholarly works;
- topics;
- concepts;
- citations;
- publication dates;
- disciplinary relationships;
- large-scale temporal analysis.

### PubMed

**PubMed E-utilities** provides an independent biomedical replication layer for applicable analyses.

This allows selected findings obtained from the broader OpenAlex knowledge system to be examined using an independently maintained biomedical literature source.

PBSK does **not** require downloading the complete OpenAlex or PubMed databases.

Only records required for a particular experiment are retrieved through their APIs and cached for reproducibility.

---

## Reproducible GitHub Workflow

The complete PBSK experiment can be executed through GitHub Actions.

Navigate to:

**Actions → PBSK Reproducible Run → Run workflow → `full`**

### Required GitHub Secret

`OPENALEX_API_KEY`

### Recommended GitHub Secret

`NCBI_API_KEY`

### Optional Repository Variable

`PBSK_CONTACT_EMAIL`

The automated workflow performs:

1. environment configuration;
2. credential validation;
3. software integrity tests;
4. scholarly-data cache restoration;
5. OpenAlex and PubMed retrieval;
6. temporally locked feature construction;
7. cohort generation and matching;
8. hypothesis testing;
9. grouped predictive evaluation;
10. temporal analysis;
11. ablation analysis;
12. replication analysis;
13. transformation analysis;
14. leakage auditing;
15. retrieval-quality assessment;
16. publication figure generation;
17. result-integrity validation;
18. artifact packaging;
19. scholarly API cache preservation.

---

## Main Outputs

A successful full workflow produces:

`pbsk-results-full.zip`

The artifact contains the complete computational record, including:

- landmark feature tables;
- matched-control tables;
- independent power-validation cohort;
- power-validation controls;
- OpenAlex feature matrices;
- PubMed feature matrices;
- retrieval and coverage metadata;
- confirmatory hypothesis tests;
- exploratory hypothesis tests;
- grouped out-of-fold predictions;
- predictive-performance tables;
- bootstrap confidence intervals;
- incremental-value tests;
- temporal T−5/T−3/T−1 evaluation;
- stage-ablation results;
- PubMed replication analyses;
- cross-source agreement analyses;
- post-emergence transformation analyses;
- temporal-leakage audits;
- retrieval-quality diagnostics;
- publication figures;
- publication tables;
- modeling contracts;
- `run_summary.json`;
- complete HTML results report.

---

## Independent Validation

A central feature of PBSK v4.0.0 is the separation between exploratory landmark analysis and independent prospective validation.

The power-validation experiment uses future scientific growth to define the outcome while restricting PBSK predictors and matching information to the pre-outcome period.

This enables the framework to test whether structural properties of scholarly knowledge observed before the cutoff are associated with later scientific emergence.

The design therefore moves beyond retrospective description toward temporally disciplined empirical testing.

---

## Reproducibility and Scientific Guardrails

PBSK is designed so that the software cannot interpret successful execution as confirmation of the underlying theory.

A green workflow indicates that:

- computation completed successfully;
- required data were retrieved;
- temporal restrictions were respected;
- modeling contracts were satisfied;
- figures and tables were generated correctly;
- integrity checks passed.

Scientific conclusions must instead be determined from:

- effect sizes;
- confidence intervals;
- multiplicity-adjusted statistical tests;
- independent validation;
- out-of-sample predictive performance;
- baseline comparisons;
- temporal behavior;
- ablation analysis;
- replication evidence.

No inferential or predictive efficacy values are hard-coded.

Positive, null, and contradictory findings remain part of the scientific record.

---

## Scientific Contribution

PBSK provides a computational framework for studying the **prehistory of scientific emergence**.

Its central proposition is testable:

> **Future-emergent scientific regions may exhibit measurable structural organization before their later emergence becomes visible.**

The framework therefore shifts attention from studying breakthroughs only after they occur toward examining the organization of knowledge that precedes scientific emergence.

PBSK integrates large-scale scholarly data, temporal validation, knowledge-structure analysis, predictive modeling, independent controls, and reproducible computation into a unified **science-of-science research system**.

---

## Software and Reproducibility

**Software:** PBSK v4.0.0  
**Repository:** https://github.com/Arithmetic-Power-Geometry/PBSK  
**DOI:** https://doi.org/10.5281/zenodo.21967787  
**License:** Apache License 2.0

PBSK is released openly to support independent reproduction, criticism, extension, and validation.

---

## Citation

If PBSK is used in academic work, please cite the software release and the conceptual source specified in `CITATION.cff`.

### Conceptual Source

Mohammad Amir Khusru Akhtar (Shunya). (2026). *THE IMPOSSIBLE IDEA: How New Realities Enter the World*. https://a.co/d/03buY0qI

### Research DOI

https://doi.org/10.5281/zenodo.21967787
