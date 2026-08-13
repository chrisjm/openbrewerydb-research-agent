---
title: OBDB Research Agent v0.1
status: final
created: 2026-08-06
updated: 2026-08-06
---

# PRD: OBDB Research Agent v0.1

## 0. Document Purpose
This PRD defines v0.1 requirements for an internal CLI workflow that helps OBDB contributors prepare high-confidence, evidence-backed corrections with less manual research. Audience is PM, engineering, and downstream UX/architecture/epic/story workflows. Terms in Glossary are canonical, and features are grouped with globally numbered FRs.

## 1. Vision
OBDB contributors lose time verifying brewery records across OBDB, state licensing sources, and brewery websites. v0.1 delivers a deterministic, one-brewery-at-a-time CLI pipeline that gathers authoritative signals, scores confidence, and outputs either a copyable CSV diff or evidence-only output when confidence is too low.

Goal is better correction quality with less maintainer burden: fewer low-quality PRs, faster trusted updates, and cleaner base for future automation. v0.1 deliberately keeps a human review gate and excludes LLM-dependent extraction.

## 2. Target User

### 2.1 Jobs To Be Done
- Detect suspect brewery record and verify quickly without manual tab-hopping.
- Produce correction proposal with source provenance maintainers can trust.
- Avoid submitting low-confidence changes.

### 2.2 Non-Users (v0.1)
- Not for fully automated data application with no human review.
- Not for users who need browser-integrated OBDB button flow in v0.1.

### 2.3 Key User Journeys
- **UJ-1. Cody verifies and proposes a correction in one CLI run.**
  - **Persona + context:** Cody is OBDB contributor, comfortable with GitHub PR edits, not running complex scripts.
  - **Entry state:** Has brewery name + location from suspect OBDB row.
  - **Path:** Runs CLI command, system fetches OBDB + state-license + website signals, confidence engine scores candidate changes.
  - **Climax:** If score meets threshold, Cody gets copyable CSV diff with evidence per changed field.
  - **Resolution:** Cody pastes CSV into PR/VS Code and includes evidence links.
  - **Edge case:** If score below threshold, system returns evidence-only output and suppresses copyable diff.

- **UJ-2. Cody validates a possible closure.**
  - **Persona + context:** Cody sees brewery appears closed but OBDB still active.
  - **Entry state:** Runs same CLI path for single brewery.
  - **Path:** System combines state license status and website closure signals, then scores confidence.
  - **Climax:** System proposes closure-related field updates only when evidence is strong.
  - **Resolution:** Low-confidence closure stays evidence-only for manual follow-up.

## 3. Glossary
- **OBDB Record** — Current brewery record fetched from Open Brewery DB API.
- **State License Record** — Normalized record from CA/CO/TX licensing adapter.
- **Candidate Record** — Proposed updated record assembled from research signals.
- **Evidence Ref** — Provenance object with source URL, snippet, fetched timestamp, and source type.
- **Field Diff** — Typed delta for one field (`old_value`, `new_value`, confidence, evidence references).
- **Confidence Score** — Numeric trust score in range 0.0–1.0 with signal breakdown.
- **Output Gate** — Rule that allows copyable CSV diff only when confidence meets threshold.
- **Swarm-safe Cache** — TTL disk cache for bulk state data reused across runs.

## 4. Features

### 4.1 Source Collection and Normalization
**Description:** System collects OBDB Record, State License Record, and website status signals for one brewery per run. State adapters are pluggable for CA/CO/TX in v0.1. Realizes UJ-1 and UJ-2.

**Functional Requirements:**

#### FR-1: OBDB lookup
System can fetch OBDB Record from OBDB API for single-brewery lookup by name + location input. Realizes UJ-1.

**Consequences (testable):**
- Returns typed OBDB Record for known match.
- Returns structured not-found result for missing brewery.
- Single-brewery lookup path calls OBDB API directly, not local full-dataset cache.

#### FR-2: State adapter contract
System must define one shared contract for state adapters (CA/CO/TX) that returns normalized State License Record items. Realizes UJ-1.

**Consequences (testable):**
- Contract includes `state_code`, single lookup method, and bulk fetch method.
- CA, CO, TX adapters conform to same typed output shape.

#### FR-3: CA/CO/TX adapter coverage
System can query California, Colorado, and Texas licensing sources in v0.1. Realizes UJ-1.

**Consequences (testable):**
- Known fixture case in each state returns normalized record list.
- Source-specific parser failures are surfaced as structured step errors.

#### FR-4: Website status check
System can run website status and closure-keyword scan for brewery website URL through pluggable website adapters. HTTP-only checks are the default v0.1 path, with a browser-capable adapter path for JS-rendered sites planned as an extension. Realizes UJ-2.

**Consequences (testable):**
- Produces typed website signal (`active`, `redirect`, `404`, `closed_keyword`).
- Uses closure phrase list without LLM extraction in v0.1.
- Crawl attempts must be policy-aware: consult `robots.txt` and return structured policy-blocked errors when disallowed.
- Requests must include an env-configured scraper identity header for transparent, ethical source access.
- Website-step blocked outcomes must use structured codes (`policy_blocked`, `technical_blocked`, `config_error`) and must never silently map to `active`.
- Adapter behavior must stay deterministic: HTTP adapter first; browser-capable adapter only on explicit technical-block predicates; maximum one fallback attempt; no hidden retries.
- Config contract: `SCRAPER_IDENTITY_HEADER_NAME` defaults to `User-Agent`; `SCRAPER_IDENTITY_HEADER_VALUE` is required and missing value yields `config_error`.
- If `robots.txt` is unreadable/unavailable/invalid, return `technical_blocked` (single-attempt behavior remains).
- v0.1 uses single-attempt check with explicit error reporting; retry policy deferred to v0.2.

### 4.2 Deterministic Evaluation and Gating
**Description:** System computes confidence using deterministic rules and applies Output Gate. No LLM in critical path for v0.1. Realizes UJ-1 and UJ-2.

**Functional Requirements:**

#### FR-5: Rules-based confidence ladder
System can score Candidate Record confidence from multi-signal evidence. Realizes UJ-1.

**Consequences (testable):**
- Returns Confidence Score (`value`, `signals`) for every run.
- Scoring rules enforce precedence tiers: authoritative state-license match signals rank above website-status-only signals.
- Given equivalent inputs, increasing high-tier signal count increases score more than increasing low-tier signal count.

#### FR-6: Configurable threshold
System must apply configurable confidence threshold for Output Gate. Realizes UJ-1.

**Consequences (testable):**
- Default threshold is `0.7`.
- Threshold policy is global in v0.1; per-state tuning deferred to v0.2.
- Threshold override is accepted via CLI flag and config file.

#### FR-7: Below-threshold suppression
System must suppress copyable diff when confidence is below threshold and return evidence-only output. Realizes UJ-1.

**Consequences (testable):**
- `copyable=false` when `confidence < threshold`.
- Evidence output still includes source URLs and snippets.

### 4.3 Diff and Provenance Output
**Description:** System compares OBDB Record and Candidate Record, emits typed Field Diff list, and renders CLI output suitable for PR workflow. Realizes UJ-1.

**Functional Requirements:**

#### FR-8: Typed field diff engine
System can produce Field Diff list between OBDB Record and Candidate Record. Realizes UJ-1.

**Consequences (testable):**
- Field Diff includes field name, old/new value, confidence, and evidence references.
- No-change case yields empty diff list.

#### FR-9: Closure schema readiness
System must support current `brewery_type='closed'` convention and remain compatible with future tag/SCD2 migration. Realizes UJ-2.

**Consequences (testable):**
- Current closure mapping works for v0.1 fixtures.
- Closure mapping logic is isolated so future schema change does not require full diff-engine rewrite.

#### FR-10: Evidence chain per change
System must attach Evidence Ref items to each proposed changed field when available. Realizes UJ-1.

**Consequences (testable):**
- Each changed field includes source URL and snippet.
- Missing evidence for a field lowers confidence or blocks copyable output per scoring rules.

#### FR-11: Copyable CSV diff output
System can render copyable CSV diff when Output Gate passes. Realizes UJ-1.

**Consequences (testable):**
- Output is valid CSV for OBDB workflow.
- v0.1 emits changed fields only as default format.

#### FR-12: Evidence-first CLI rendering
System can render concise evidence report in terminal both for passing and failing gates. Realizes UJ-1 and UJ-2.

**Consequences (testable):**
- Evidence display is readable at 100-column terminal width with wrapped long snippets and no truncated source URL.
- Failing gate output contains no copyable CSV block.

### 4.4 Pipeline Orchestration
**Description:** System orchestrates full single-brewery pipeline with immutable state transitions and resilient error propagation. Realizes UJ-1.

**Functional Requirements:**

#### FR-13: Ordered single-brewery pipeline
System must execute one-brewery pipeline in this order: OBDB API lookup, state fetch/cache, website check, confidence, diff, gate, render. Realizes UJ-1.

**Consequences (testable):**
- End-to-end run returns structured pipeline result for known fixture.
- Pipeline does not batch multiple breweries in one run.

#### FR-14: Error continuity
System must surface step failures in state error and continue to response stage. Realizes UJ-1.

**Consequences (testable):**
- Step failure does not crash process.
- Response includes explicit error context and any partial evidence gathered.

#### FR-15: OBDB full-data cache source
System must source full OBDB dataset cache from OBDB GitHub repository snapshots for background refresh/indexing use cases, while per-run brewery lookup remains OBDB API authoritative per FR-1. Realizes UJ-1.

**Consequences (testable):**
- Bulk cache refresh job pulls from configured OBDB GitHub dataset source, not per-record API fan-out.
- Runtime single-brewery lookup continues to use OBDB API path from FR-1.
- Bulk cache refresh path is enabled by default in v0.1 for background/local index refresh tasks.

## 5. Non-Goals (Explicit)
- No web search/deep research in v0.1.
- No LLM/NER website extraction in v0.1.
- No automated GitHub PR creation in v0.1.
- No HTML research report generation in v0.1.
- No OBDB site button integration in v0.1.
- No EIN/secondary enrichment API integration in v0.1.

## 6. MVP Scope

### 6.1 In Scope
- CLI form-factor for one brewery per run.
- OBDB API for single-brewery lookup path.
- OBDB GitHub source for full-dataset cache refresh path.
- CA/CO/TX state licensing adapters.
- Swarm-safe Cache with TTL reuse.
- Deterministic Confidence Score and Output Gate.
- Typed Field Diff + Evidence Ref chain.
- Copyable CSV diff only when confidence threshold passes.

### 6.2 Out of Scope for MVP
- Additional state adapters beyond CA/CO/TX (defer to v0.2+).
- LLM-assisted extraction and discovery (defer to v0.2).
- Browser/website integration surfaces (defer to roadmap).

## 7. Success Metrics
**Primary**
- **SM-1:** Median contributor research-to-diff time reduced by at least 60% from 10-minute manual baseline (target median <= 4 minutes). Validates FR-13, FR-11.
- **SM-2:** At least 90% of copyable CSV diffs include complete field-level evidence links/snippets. Validates FR-10, FR-12.
- **SM-3:** Less than 5% of below-threshold cases emit copyable output (target 0%). Validates FR-7.

**Secondary**
- **SM-4:** At least 95% fixture pass rate across CA/CO/TX adapter and pipeline tests. Validates FR-2, FR-3, FR-13.
- **SM-5:** Cache reuse avoids repeated bulk state fetch within TTL for at least 80% of multi-run sessions. Validates FR-13.

**Counter-metrics (do not optimize)**
- **SM-C1:** Do not optimize for maximum copyable output volume at expense of evidence quality. Counterbalances SM-1.
- **SM-C2:** Do not reduce evidence verbosity below reviewer-usable level to make output shorter. Counterbalances SM-2.

## 8. Cross-Cutting NFRs
- **Determinism:** Scoring and gating results are reproducible from same inputs and cache state.
- **Reliability:** Step-level failures are explicit and non-crashing (FR-14).
- **Observability:** Pipeline result includes step outcomes and confidence signal list for diagnosis.
- **Security/Privacy:** v0.1 uses public no-auth data endpoints; no secret tokens printed in output.
- **Performance:** Typical single run targets <=10s cached path and <=30s uncached path.

## 9. Integration and Dependencies
- Depends on OBDB public API contract for current record retrieval.
- Depends on OBDB GitHub repository dataset availability for bulk cache refresh path.
- Depends on CA/CO/TX licensing source accessibility and parser stability.
- Depends on local disk access for Swarm-safe Cache persistence.
- CSV output contract must remain compatible with maintainer review workflows in GitHub PRs.

## 10. Risks and Mitigations
- **Risk:** State source shape changes break adapters.  
  **Mitigation:** Isolate adapter parsers and validate with snapshot fixtures per state.
- **Risk:** Low-confidence data still looks actionable to contributors.  
  **Mitigation:** Hard Output Gate with no copyable CSV below threshold.
- **Risk:** Future OBDB closure schema migration breaks diff logic.  
  **Mitigation:** Keep closure mapping isolated and covered by compatibility tests.

## 11. Open Questions
No phase-blocking open questions currently.

## 12. Assumptions Index
No unresolved assumptions currently.
