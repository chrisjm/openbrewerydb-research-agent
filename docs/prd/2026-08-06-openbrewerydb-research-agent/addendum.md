# Addendum — OBDB Research Agent v0.1

## Source Preservation
This addendum preserves deeper planning detail from brainstorming artifacts that informs downstream architecture and epic/story decomposition.

## Imported Depth
- Landscape/comparable signals from discovery research are available in session output and should inform later architecture risk review.

## Websites Reviewed in Discovery and What Was Learned
- `https://opencorporates.com/` — large legal-entity dataset/API; useful pattern for status verification and provenance-first entity data.
- `https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/company-profile/company-profile` — official registry API reference; useful model for deterministic record-check contracts.
- `https://www.gleif.org/en/lei-data/gleif-api` — LEI API supports entity search/fuzzy lookup; useful for future entity-resolution strategy.
- `https://github.com/opensanctions/opensanctions` — pipeline patterns for ingest/clean/deduplicate/export; useful architecture reference, but licensing constraints must be reviewed before reuse.
- `https://openrefine.org/docs/manual/reconciling` — human-in-loop reconciliation flow aligns with v0.1 confidence gate.
- `https://github.com/paulfitz/daff` — CSV/table diff tooling; useful reference for future diff format interoperability.
- `https://specs.frictionlessdata.io/tabular-diff/` — formal tabular diff spec; useful for standardizing machine-readable correction artifacts later.
- `https://framework.frictionlessdata.io/` — data validation framework; useful for post-diff quality checks.
- `https://docs.greatexpectations.io/docs/0.18/core/introduction/introduction/` — data quality test patterns; useful for regression checks as pipeline grows.
- `https://www.fincen.gov/beneficial-ownership-information-reporting-rule-fact-sheet` — regulatory volatility example; reminder to avoid assumptions about data source stability.
- `https://github.com/datafold/data-diff` — open-source maintenance risk signal; avoid hard dependency without maintenance check.

## Are These Sites Useful for Additional Data Gathering?
Yes, with constraints:
- Useful now for design patterns (entity verification, reconciliation UX, diff/validation standards).
- Useful later (v0.2+) for stronger entity matching and richer validation workflows.
- Not direct drop-in replacements for CA/CO/TX authoritative licensing signals in v0.1.
- Some sources carry licensing/maintenance risk, so any adoption needs legal + reliability review first.

## Deferred Evolution Items (v0.2+ roadmap, not open for v0.1)
- Optional per-state threshold tuning model after v0.1 performance review.
- Optional alternate CSV presentation mode (full-row markers) if maintainers request it.
- Optional website check retry/timeout tuning pass after initial reliability telemetry.
