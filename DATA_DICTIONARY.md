# PBSK v4.0.0 Data Dictionary

## Core identifiers

- `source`: OpenAlex or PubMed.
- `cohort`: `landmark` or `power_validation`.
- `region_id`: unique region identifier.
- `match_case_id`: matched-group identifier used for grouped inference/CV.
- `target`: 1 for future breakthrough/emergent region, 0 for matched control.
- `domain`: scholarly domain.
- `book_realm`: Nature, Life, Minds, Cultures, Machines, or Unassigned.
- `landmark_year`: event year; for the power-validation cohort this is cutoff+1.
- `offset`: years before landmark (`5`, `3`, `1`).
- `cutoff_year`: latest allowable predictor year.
- `max_publication_year`: audit field for temporal leakage.

## Coverage fields

- `n_docs`: documents available at the cutoff in the retrieved sample.
- `years_covered`: number of represented publication years.
- `quality_eligible`: 1 when pre-specified minimum coverage rules are satisfied.
- `activity_recent`: recent pre-cutoff activity.
- `activity_prior`: earlier pre-cutoff activity.
- `mean_citations`: mean citations of sampled works.
- `topic_entropy`: normalized topic entropy.

## Legacy mechanisms

- `density_gap`: semantic separation between two dominant knowledge clusters.
- `boundary_activity`: share of work close to a semantic cluster boundary.
- `complementarity`: topic diversity.
- `momentum`: recent versus prior activity acceleration.
- `recombination`: reference-based recombination proxy.
- `convergence`: change in inter-cluster similarity.
- `skg`: geometric Structured Knowledge Gap score.
- `pbs`: legacy weighted Pre-Breakthrough Signature.

## Book-wide raw proxies

- `possibility_pressure`
- `question_pressure`
- `anomaly_pressure`
- `doubt_tension`
- `pattern_formation`
- `cross_domain_similarity`
- `analogical_transfer`
- `bridge_formation`
- `collision_index`
- `surprise_geometry`
- `insight_coherence`
- `leap_nonlinearity`
- `originality_risk`
- `sequence_order_score`

These are literature-level proxies, not direct psychological measurements.

## v4 stage scores

- `stage_possibility`
- `stage_question`
- `stage_pattern`
- `stage_imagination`
- `stage_insight`
- `stage_discovery_readiness`

`bookwide_pbsk` is the geometric mean of these six stage scores.

## Independent v4 hypothesis

- `core_geometry_score`: geometric synthesis of SKG, collision structure, and sequence-order agreement. It is v3-derived and therefore confirmatory only in the independent v4 power-validation cohort.

## Transformation outcomes

- `post_docs`
- `post_growth`
- `topic_diffusion`
- `normalization_index`
- `post_adoption`
- `transformation`

## Power-validation topic table

- `topic_id`, `topic_name`
- `pre_count`, `post_count`
- `recent_pre_count`, `early_pre_count`
- `pre_momentum_ratio`
- `future_growth`, `future_ratio`
- `growth_rank`
- `match_distance`

Future-growth fields define the validation outcome only; they are not used as pre-breakthrough predictors.
