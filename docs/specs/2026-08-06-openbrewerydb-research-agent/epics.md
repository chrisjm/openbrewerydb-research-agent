---
stepsCompleted:
  - 1
  - 2
  - 3
---

# openbrewerydb-research-agent - Epic Breakdown

## Overview

This document breaks the OBDB Research Agent v0.1 requirements into implementation epics and stories. Inputs: PRD, addendum, and architecture spine.

## Requirements Inventory

### Functional Requirements

FR1: Fetch a single OBDB record by brewery name and location through the OBDB API.
FR2: Define one shared state-adapter contract that returns normalized license records.
FR3: Query California, Colorado, and Texas licensing sources in v0.1.
FR4: Check brewery website status and scan for closure keywords without LLM extraction.
FR5: Score confidence from multi-signal evidence with deterministic rules.
FR6: Apply a configurable confidence threshold with default 0.7 and CLI/config override.
FR7: Suppress copyable output when confidence is below threshold and return evidence-only output.
FR8: Produce typed field diffs between OBDB and candidate records.
FR9: Support current closed-brewery mapping and keep closure logic isolated for future schema changes.
FR10: Attach evidence refs to changed fields when available.
FR11: Render copyable CSV diff only when the output gate passes.
FR12: Render a concise evidence-first CLI report in both passing and failing cases.
FR13: Execute the single-brewery pipeline in the fixed order: OBDB lookup, state fetch/cache, website check, confidence, diff, gate, render.
FR14: Surface step failures in state error and continue to the response stage.
FR15: Source bulk cache refresh from OBDB GitHub snapshots while runtime lookup stays on the OBDB API.

### NonFunctional Requirements

NFR1: Scoring and gating must be deterministic for the same inputs and cache state.
NFR2: Step failures must be explicit and non-crashing.
NFR3: The pipeline must expose step outcomes and confidence signals for diagnosis.
NFR4: v0.1 uses public no-auth data endpoints only and must not print secrets.
NFR5: Typical single runs should target <=10s cached and <=30s uncached.

### Additional Requirements

- v0.1 is a local CLI with local disk cache only; no service or worker deployment shape is in scope.
- Runtime lookup must use the OBDB API; bulk refresh must use OBDB GitHub dataset snapshots.
- The pipeline must remain in-process with immutable state transitions via frozen models and explicit state copies.
- State adapters must share one contract with `state_code`, `lookup_one`, and `fetch_bulk`.
- Confidence scoring and threshold gating must live in one domain authority; renderers must not recompute them.
- CSV output must stay compatible with maintainer GitHub PR workflows.
- Closure mapping logic must stay isolated so future schema changes do not require a diff-engine rewrite.

### UX Design Requirements

None found.

### FR Coverage Map

FR1: Epic 1 - Single-brewery evidence collection
FR2: Epic 1 - Shared state adapter contract
FR3: Epic 1 - CA/CO/TX licensing coverage
FR4: Epic 1 - Website status and closure signal collection
FR5: Epic 2 - Deterministic confidence scoring
FR6: Epic 2 - Configurable threshold gate
FR7: Epic 2 - Below-threshold suppression
FR8: Epic 2 - Typed diff generation
FR9: Epic 2 - Closure schema compatibility
FR10: Epic 2 - Evidence refs per change
FR11: Epic 2 - Copyable CSV rendering
FR12: Epic 2 - Evidence-first CLI rendering
FR13: Epic 1 - Fixed-order single-brewery pipeline
FR14: Epic 1 - Error continuity to response
FR15: Epic 1 - OBDB API lookup and GitHub cache refresh split

## Epic List

### Epic 1: Run a single-brewery evidence pass
A contributor can verify one brewery in a single CLI run, collect OBDB/state/website signals, and get a complete evidence bundle even when a step fails.
**FRs covered:** FR1, FR2, FR3, FR4, FR13, FR14, FR15

### Epic 2: Produce trusted correction output
A contributor can turn gathered evidence into deterministic confidence, typed field diffs, provenance, and copyable CSV only when the output is trustworthy.
**FRs covered:** FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12

## Epic 1: Run a single-brewery evidence pass

Epic goal: A contributor can complete one ordered research run, see explicit step failures, and get source-backed evidence without waiting for later epics.

### Story 1.1: Fetch the target OBDB record

As a contributor,
I want to enter a brewery name and location and fetch the matching OBDB record,
So that I can verify the target brewery before comparing other sources.

**Acceptance Criteria:**

**Given** a brewery name and location
**When** the CLI runs the OBDB lookup
**Then** it returns one typed OBDB record for a known match
**And** it returns a structured not-found result when no match exists
**And** it does not depend on the bulk cache path for the lookup

### Story 1.2: Normalize state-license records through shared adapters

As a contributor,
I want CA, CO, and TX license sources to return the same normalized shape,
So that the run can compare state evidence without special-case code per state.

**Acceptance Criteria:**

**Given** a CA, CO, or TX source fixture
**When** the adapter fetches records
**Then** it returns normalized state-license records through the shared contract
**And** each adapter exposes the same `state_code`, `lookup_one`, and `fetch_bulk` behavior
**And** a parser failure is surfaced as a structured step error

### Story 1.3: Check brewery website status in the run

As a contributor,
I want the run to check website status and closure keywords,
So that I can see whether the brewery website supports or weakens the correction.

**Acceptance Criteria:**

**Given** a brewery website URL
**When** the website check runs
**Then** it returns one of the typed signals: active, redirect, 404, or closed_keyword
**And** it uses the configured closure phrase list without LLM extraction
**And** a single-attempt failure is reported explicitly instead of silently retried

### Story 1.3b: Add policy-aware and JS-capable website access

As a contributor,
I want website checks to honor crawl policy and support JS-rendered sites when allowed,
So that evidence collection stays ethical and resilient across modern brewery websites.

**Acceptance Criteria:**

**Given** a website URL
**When** website collection starts
**Then** the workflow checks `robots.txt` policy before non-trivial crawl behavior
**And** when disallowed it returns a structured policy-blocked error
**And** all crawl requests include an env-configured scraper identity header
**And** JS-rendered sites can be handled by a browser-capable adapter path behind the same website port contract
**And** blocked outcomes are surfaced as structured codes (`policy_blocked`, `technical_blocked`, `config_error`) and are never classified as `active`
**And** adapter selection is deterministic (HTTP first, optional single browser fallback on technical block only)
**And** when website access is blocked or fails, the pipeline continues with partial evidence and explicit step error context

### Story 1.4: Preserve ordered execution and partial evidence on failure

As a contributor,
I want the run to follow one fixed pipeline and keep partial evidence when a step fails,
So that I can still review what succeeded and what broke.

**Acceptance Criteria:**

**Given** a single brewery run
**When** the pipeline executes
**Then** it runs in the fixed order: OBDB lookup, state fetch/cache, website check, confidence, diff, gate, render
**And** each step returns a new state snapshot rather than mutating in place
**And** a step failure is captured in state error and the response stage still runs
**And** bulk cache refresh uses OBDB GitHub snapshots while runtime lookup stays on the OBDB API

## Epic 2: Produce trusted correction output

Epic goal: A contributor can score the run, compare candidate and source records, and export only reviewable output that carries field-level provenance.

### Story 2.1: Score confidence and apply the gate

As a contributor,
I want deterministic confidence scoring with a configurable threshold,
So that I know when the run output is safe to copy into a correction PR.

**Acceptance Criteria:**

**Given** the same inputs and cache state
**When** the score is computed twice
**Then** the confidence value is the same both times
**And** the default threshold is 0.7
**And** a CLI flag or config override can change the threshold
**And** when confidence is below threshold, copyable output is suppressed

### Story 2.2: Produce typed diffs with provenance

As a contributor,
I want field-level diffs tied to evidence refs,
So that each proposed change is reviewable and traceable.

**Acceptance Criteria:**

**Given** an OBDB record and a candidate record
**When** the diff runs
**Then** each changed field includes field name, old value, new value, confidence, and evidence refs
**And** a no-change comparison yields an empty diff list
**And** missing evidence lowers confidence or blocks copyable output according to gate rules

### Story 2.3: Render copyable CSV or evidence-only output

As a contributor,
I want the CLI to render copyable CSV only when the gate passes and evidence-only output otherwise,
So that I can paste only trusted corrections into PRs.

**Acceptance Criteria:**

**Given** a gate-passing run
**When** the renderer runs
**Then** it emits valid CSV containing changed fields only
**And** the CSV is copyable for maintainer PR workflows
**Given** a below-threshold run
**When** the renderer runs
**Then** it emits evidence-only output with source URLs and snippets
**And** it contains no copyable CSV block

### Story 2.4: Keep closure mapping isolated for future schema change

As a contributor,
I want closed-brewery mapping to stay isolated,
So that a future tag or SCD2 schema change does not force a full diff-engine rewrite.

**Acceptance Criteria:**

**Given** current v0.1 closure fixtures
**When** the closure mapping runs
**Then** it supports the current brewery_type='closed' convention
**And** the mapping logic is isolated behind a dedicated module or boundary
**And** future schema changes can be handled without changing the diff engine contract
