# Changelog

## 4.0.0 — Power-validated design

- Added independent prospective OpenAlex topic power-validation cohort (target ≈120 positive future-emergent topics plus pre-cutoff matched controls).
- Separated v3 landmark exploration from v4 independent confirmation.
- Added `core_geometry_score` and restricted confirmatory interpretation to the independent v4 cohort.
- Replaced first-N retrieval with deterministic random OpenAlex sampling using `sample` + `seed`.
- Increased usable corpus sizes while remaining API-budget conscious.
- Added pre-specified minimum-document/year coverage gate.
- Rebuilt book-wide PBSK as a hierarchical equal-stage geometric score.
- Added six explicit stage scores.
- Added grouped bootstrap confidence intervals for predictive metrics.
- Added incremental-value tests versus activity/citation baseline.
- Added histogram-gradient-boosting comparison.
- Added confirmatory/exploratory FDR families.
- Extended PubMed replication to applicable power-validation topics.
- Capped post-breakthrough windows at the configured current year.
- Added live OpenAlex authentication preflight to GitHub Actions.
- Increased workflow timeout and refreshed API cache namespace.

## 3.0.3

- Hardened sparse plotting, PubMed replication, and full-run integrity checks.
