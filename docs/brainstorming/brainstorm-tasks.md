# OBDB Research Agent — v0.1 Epic & Story Task List

**Source:** `.memlog.md` from brainstorming session 2026-08-06
**Scope:** v0.1 deterministic pipeline (OBDB + state API + confidence + diff output)
**Output language:** English

---

## Scope Summary

| Tier | Items |
|------|-------|
| **Must (v0.1)** | OBDB lookup, state API (CA/CO/TX), cache+TTL, confidence ladder, website HTTP check, diff engine, evidence chain, output gating, schema SCD2-readiness |
| **Should (stretch)** | Visible confidence scores in output, documented adapter interface, eval harness |
| **Could** | Google Business signal, insufficient-evidence explanation text |
| **Won't / Deferred** | Web search (v0.2), LLM/NER website extraction (v0.2), HTML discovery reports (v0.3+), automated GitHub PR (v0.3+), EIN enrichment (future), OBDB site integration button (future) |

---

## Design Constraints

- **One brewery per agent run** — designed for swarming, not batch-in-one-run.
- **Bulk cache strategy** — full state/city dataset pulled and cached once; individual lookups reuse it cheaply.
- **Human always in the loop** — no change is applied without a human reviewing the output.
- **Schema dual-mode** — diff engine must handle `brewery_type='closed'` (current) and tag-based SCD type 2 (upcoming).

---

## Epic 1 — Data Sources

Fetch authoritative data from OBDB and state licensing APIs.

### Story 1.1 — OBDB Lookup

**Title:** Fetch existing brewery record from OBDB API
**Description:** Given a brewery name and location, retrieve the current OBDB record via the public API.
**Acceptance criteria:**
- Returns a typed `OBDBRecord` model for a known brewery.
- Returns a structured "not found" result (not an exception) for an unknown name.
- Covers at least one happy-path and one not-found test case.

**Dependencies:** None

---

### Story 1.2 — State API Adapter Interface

**Title:** Define the common state adapter interface
**Description:** Establish a documented abstract interface (`StateAdapter`) that all state licensing adapters must implement, enabling future contributors to add new states without modifying core pipeline code.

**Interface contract (document this explicitly):**
```
StateAdapter:
  state_code: str                    # e.g. "CA", "CO", "TX"
  fetch(brewery_name, city) -> list[StateLicenseRecord]
  bulk_fetch(state_code) -> list[StateLicenseRecord]   # for cache population
```

**Acceptance criteria:**
- Abstract base class (or Protocol) exists in `obdb/adapters/base.py`.
- Docstring specifies required fields on `StateLicenseRecord` (name, address, license_status, source_url, fetched_at).
- At least one concrete adapter passes a type-check against the interface.

**Dependencies:** None

---

### Story 1.3 — CA ABC Adapter

**Title:** Implement California ABC licensing adapter
**Description:** Fetch and parse brewery license data from the California Alcoholic Beverage Control (ABC) source.
**Acceptance criteria:**
- Returns `StateLicenseRecord` list for a known CA brewery.
- Snapshot fixture used by default; live HTTP gated behind `--live` flag.
- Implements `StateAdapter` interface from Story 1.2.

**Dependencies:** Story 1.2

---

### Story 1.4 — Colorado Adapter

**Title:** Implement Colorado state licensing adapter
**Description:** Fetch and parse brewery license data from the Colorado licensing source.
**Acceptance criteria:**
- Returns `StateLicenseRecord` list for a known CO brewery.
- Snapshot fixture used by default.
- Implements `StateAdapter` interface from Story 1.2.

**Dependencies:** Story 1.2

---

### Story 1.5 — Texas Adapter

**Title:** Implement Texas state licensing adapter
**Description:** Fetch and parse brewery license data from the Texas licensing source (TABC or equivalent).
**Acceptance criteria:**
- Returns `StateLicenseRecord` list for a known TX brewery.
- Snapshot fixture used by default.
- Implements `StateAdapter` interface from Story 1.2.

**Dependencies:** Story 1.2

---

### Story 1.6 — Website HTTP Check

**Title:** Probe brewery homepage for closure signals
**Description:** Issue an HTTP HEAD/GET request to the brewery's website URL; classify result as `active`, `404`, `redirect`, or `closed_keyword` based on status code and shallow keyword scan.

**v0.1 scope:** HTTP status + closure keyword scan only (e.g. "permanently closed", "we have closed"). No LLM extraction — deferred to v0.2.

**Acceptance criteria:**
- Returns a typed `WebCheckResult(status, signal, url, checked_at)`.
- `closed_keyword` signal triggered when page body contains any closure phrase in a defined list.
- Uses snapshot HTML fixtures in tests; live HTTP gated behind `--live` flag.

**Dependencies:** None

---

## Epic 2 — Pipeline Core

Orchestrate the per-brewery research run and manage caching.

### Story 2.1 — Cache Layer with TTL

**Title:** Implement fetch-and-cache for state API responses
**Description:** Cache the full state/city dataset (per state) with a configurable TTL so that multiple single-brewery lookups within a run reuse one network call.
**Acceptance criteria:**
- First call fetches from source; subsequent calls within TTL return cached data.
- TTL is configurable (default 24 h).
- Cache is stored on disk (not in-memory only) so it survives between CLI invocations.
- Cache entry includes `fetched_at` timestamp and `state_code`.

**Dependencies:** Story 1.2

---

### Story 2.2 — Pipeline Orchestrator

**Title:** Wire the deterministic per-brewery research pipeline
**Description:** Compose the pipeline steps in order: OBDB lookup → state API pull (via cache) → website HTTP check → confidence scoring → diff generation → output gating.

**Pipeline steps:**
1. OBDB lookup (Story 1.1)
2. State API fetch via cache (Story 2.1 + matching adapter)
3. Website HTTP check (Story 1.6)
4. Confidence scoring (Epic 3)
5. Diff generation (Epic 4)
6. Output gating → render result (Epic 5)

**Acceptance criteria:**
- Given a brewery name + state, the pipeline runs end-to-end and produces a `PipelineResult`.
- Each step's output is passed as immutable state to the next (frozen Pydantic model, `model_copy(update=...)`).
- Errors in any step populate `state.error` and flow continues to RESPOND — pipeline never hard-crashes.
- Integration test covers a full happy-path run using fixtures.

**Dependencies:** Stories 1.1, 1.3–1.5, 1.6, 2.1, Epic 3, Epic 4

---

## Epic 3 — Confidence Engine

Score how trustworthy the research result is and gate output accordingly.

### Story 3.1 — Confidence Ladder

**Title:** Implement rules-based confidence scoring
**Description:** Assign a confidence score (0.0–1.0) to a candidate record update based on the agreement and authority of evidence signals.

**Scoring signals (v0.1):**
| Signal | Weight |
|--------|--------|
| State API license status matches | High |
| Website HTTP 200 + no closure keyword | Medium |
| Website 404 or closure keyword | High (for closure verdict) |
| State API record not found | Low negative |
| OBDB record and state API name match exactly | Bonus |

**Acceptance criteria:**
- `score_confidence(evidence: Evidence) -> ConfidenceScore` is a pure function with no I/O.
- Unit tests cover: high-confidence open, high-confidence closed, low-evidence inconclusive.
- Returns `ConfidenceScore(value: float, signals: list[str])`.

**Dependencies:** None (pure function; integrates in Story 2.2)

---

### Story 3.2 — Output Gating

**Title:** Gate output by confidence threshold
**Description:** If confidence meets or exceeds threshold, produce a copyable CSV diff. Below threshold, show evidence only — no copy button. Human is always in the loop.

**Acceptance criteria:**
- Threshold is configurable (default 0.7).
- `gate_output(result: PipelineResult, threshold: float) -> GatedOutput` is a pure function.
- `GatedOutput.copyable: bool` is `True` only when `confidence >= threshold`.
- Unit tests cover above-threshold and below-threshold cases.

**Dependencies:** Story 3.1

---

## Epic 4 — Diff Engine

Produce a typed, evidence-backed diff between the existing OBDB record and the candidate update.

### Story 4.1 — Typed Field Comparator

**Title:** Implement typed diff between OBDB record and candidate record
**Description:** Compare each field of the existing `OBDBRecord` with a `CandidateRecord` and produce a list of `FieldDiff` objects.

**Acceptance criteria:**
- `diff_records(existing: OBDBRecord, candidate: CandidateRecord) -> list[FieldDiff]`.
- `FieldDiff(field, old_value, new_value, confidence, evidence_refs)`.
- Handles `brewery_type='closed'` (current schema) correctly.
- Designed to accommodate tag-based SCD type 2 without structural changes — `brewery_type` logic is isolated in a single function.
- Unit tests cover: no-change, single field change, closure type change.

**Dependencies:** Story 1.1

---

### Story 4.2 — Evidence Chain

**Title:** Attach source provenance to every proposed field change
**Description:** Each `FieldDiff` must cite the source URL and extracted text snippet that supports the proposed change.

**Acceptance criteria:**
- `EvidenceRef(source_url, snippet, fetched_at, source_type)` model exists.
- Every `FieldDiff` carries `evidence_refs: list[EvidenceRef]` (may be empty list if inconclusive).
- Integration test verifies that a state API–sourced change includes a valid `source_url`.

**Dependencies:** Stories 1.2, 4.1

---

## Epic 5 — Output / UI

Render the pipeline result in a form the user can inspect and act on.

### Story 5.1 — CSV Diff Output

**Title:** Render diff as a copyable CSV row
**Description:** Format the field diffs as a CSV row matching the OBDB schema, ready to paste into a GitHub PR or VS Code edit.

**Acceptance criteria:**
- Output is valid CSV with OBDB column headers.
- Only changed fields are highlighted (or all fields are included with changed ones marked — TBD by implementer, document choice).
- `--output csv` flag writes to stdout; can be piped to a file.

**Dependencies:** Story 4.1, Story 3.2

---

### Story 5.2 — Evidence Display

**Title:** Render evidence chain in CLI output
**Description:** Below the CSV diff (or alone when confidence is below threshold), print the evidence chain so the user can verify sources.

**Acceptance criteria:**
- Each `FieldDiff` with evidence prints: field name, proposed value, source URL, snippet.
- When `GatedOutput.copyable` is False, evidence is printed but no CSV copy block is shown.
- Output is readable in a standard 80-column terminal.

**Dependencies:** Stories 4.2, 3.2

---

## Stretch Goals (Should)

These are in scope for v0.1 if time allows, but do not block the Must stories.

### Stretch S1 — Visible Confidence Scores

**Title:** Surface confidence scores in CLI output
**Description:** Print the overall confidence score and per-signal breakdown alongside the diff output, so the user understands why a result is gated.
**Acceptance criteria:** Score and signals printed in human-readable format below the evidence block.
**Dependencies:** Story 3.1, Story 5.2

---

### Stretch S2 — Eval Harness

**Title:** Build ground-truth test fixture set for pipeline evaluation
**Description:** Curate a set of known-good brewery records (with known correct updates) as fixtures. Run the full pipeline against them and assert output matches expected diff.

**Note:** These fixtures double as training data for the v0.2 LLM/NER extraction layer.

**Acceptance criteria:**
- At least 5 ground-truth cases: 2 open, 2 closed, 1 inconclusive.
- `uv run pytest obdb/tests/test_eval.py -v` passes against fixture set.
- Cases cover all three v0.1 states (CA, CO, TX).

**Dependencies:** Story 2.2 (full pipeline)

---

## Deferred Items

| Item | Target version | Reason deferred |
|------|---------------|-----------------|
| Web search layer (verify + discover fields) | v0.2 | Requires non-deterministic step; breaks v0.1 pure-determinism goal |
| LLM/NER website extraction | v0.2 | Without state API, website is the only source — requires deterministic state API first |
| HTML discovery reports | v0.3+ | Nice-to-have; UI investment before pipeline is proven |
| Automated GitHub PR creation | v0.3+ | Risk of flooding maintainer with low-quality PRs before quality is proven |
| EIN enrichment (water usage, barrels, predictive models) | Future | Valuable but out of MVP scope |
| OBDB site "research" button integration | Future | Requires upstream site changes |
| Google Business signal | Could / v0.2 | Useful signal but not load-bearing for v0.1 determinism |

---

## Story Dependency Map

```
1.2 (adapter interface)
  └── 1.3 CA, 1.4 CO, 1.5 TX
       └── 2.1 (cache)
            └── 2.2 (pipeline) ← 1.1, 1.6, 3.1, 4.1
                                       │        │
                                      3.2      4.2
                                       └── 5.1, 5.2
```

---

## Suggested Implementation Order

1. `1.1` OBDB Lookup
2. `1.2` Adapter interface
3. `1.6` Website HTTP check
4. `4.1` Diff comparator
5. `3.1` Confidence ladder
6. `3.2` Output gating
7. `4.2` Evidence chain
8. `1.3` CA adapter
9. `2.1` Cache layer
10. `1.4` CO adapter, `1.5` TX adapter (parallel)
11. `2.2` Pipeline orchestrator
12. `5.1` CSV output, `5.2` Evidence display (parallel)
13. *(Stretch)* `S1` Visible scores, `S2` Eval harness
