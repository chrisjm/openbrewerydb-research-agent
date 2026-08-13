---
baseline_commit: 90ea64b92f9843a299ca78a8d365d13a745b9c6f
---

# Story 1.4: Preserve Ordered Execution and Partial Evidence on Failure

Status: done

## Story

As a contributor,
I want the run to follow one fixed pipeline and keep partial evidence when a step fails,
so that I can still review what succeeded and what broke.

## Acceptance Criteria

1. **Given** a single brewery run **When** the pipeline executes **Then** it runs in the fixed order: OBDB lookup, state fetch/cache, website check, confidence, diff, gate, render.
2. **Given** each step executes **When** state moves forward **Then** each step returns a new state snapshot rather than mutating in place.
3. **Given** a step failure **When** execution continues **Then** failure is captured in state error and response stage still runs.
4. **Given** cache refresh behavior **When** runtime lookup and bulk refresh are used **Then** bulk cache refresh uses OBDB GitHub snapshots while runtime lookup stays on OBDB API.

## Tasks / Subtasks

- [ ] Add orchestrator run-state model and fixed-order executor (AC: 1, 2, 3)
  - [ ] Create `obdb/agent/orchestrator.py` with one deterministic entrypoint for single-brewery execution.
  - [ ] Define explicit ordered step sequence in code (not caller-controlled), matching AC order exactly.
  - [ ] Return immutable state snapshots via `model_copy(update=...)`; no in-place mutation.
- [ ] Extend shared state model for pipeline snapshots and per-step outcomes (AC: 2, 3)
  - [ ] Update `obdb/agent/state.py` with frozen pipeline state model(s) carrying:
    - input target (name, location)
    - OBDB lookup result
    - state-license evidence
    - website signal/error
    - confidence payload placeholder
    - diff payload placeholder
    - gate payload placeholder
    - structured `StepError` context
    - step outcomes list for render visibility
  - [ ] Keep existing model contracts compatible with existing tests.
- [ ] Add domain placeholders for confidence, diff, and gate boundaries (AC: 1)
  - [ ] Create `obdb/domain/scoring.py`, `obdb/domain/diff.py`, `obdb/domain/gate.py` with minimal typed stubs used by orchestrator (do not over-build rules yet).
  - [ ] Ensure orchestrator calls through these modules so Story 2 can replace internals without rewiring orchestration.
- [ ] Add cache and renderer ports plus minimal adapters used by orchestrator (AC: 1, 3, 4)
  - [ ] Add `obdb/ports/cache_port.py` and `obdb/ports/renderer_port.py`.
  - [ ] Add `obdb/adapters/disk_cache_adapter.py` and `obdb/adapters/cli_renderer_adapter.py` minimal implementations for v0.1 path.
  - [ ] Keep OBDB runtime lookup path through `OBDBApiAdapter.lookup_one`; do not route runtime lookup through bulk cache.
- [ ] Add OBDB snapshot refresh boundary for bulk cache source (AC: 4)
  - [ ] Add explicit bulk-refresh method/path that identifies OBDB GitHub snapshot source.
  - [ ] Keep runtime single lookup untouched and API-authoritative.
  - [ ] Surface refresh failures as structured `StepError` without crashing run.
- [ ] Add orchestrator tests for order, immutability, and error continuity (AC: 1, 2, 3, 4)
  - [ ] Add `obdb/tests/test_orchestrator.py` with step-call-order assertion.
  - [ ] Add regression test proving pipeline reaches render after injected step failure.
  - [ ] Add regression test proving prior state snapshots remain unchanged after each step.
  - [ ] Add test proving runtime lookup uses OBDB API path and bulk refresh uses GitHub snapshot path.
- [ ] Keep existing checks green and run repo quality gates
  - [ ] `uv run ruff check obdb/`
  - [ ] `uv run ruff format --check obdb/`
  - [ ] `uv run pytest obdb/tests/ -v`

## Dev Notes

### Story Foundation and Epic Context

- This is Epic 1 completion story for deterministic end-to-end orchestration before confidence/diff/gate detail stories in Epic 2.
- Sequencing note from sprint status: keep this story after 1.3 and 1.3b to avoid pipeline and error-contract rework.
- Business value: contributor gets complete run evidence even when one step fails.

### Technical Requirements (must follow)

1. Keep fixed pipeline order hard-coded in orchestrator per FR-13 and AC-1.
2. Preserve immutable state transitions per AD-2 (`frozen=True`, `model_copy(update=...)`).
3. Preserve error continuity per AD-6: capture `StepError`, continue to render stage.
4. Runtime lookup remains OBDB API (`OBDBApiAdapter.lookup_one`); bulk refresh path uses OBDB GitHub snapshots only.
5. Keep deterministic behavior for same inputs and fixtures. No hidden retries in orchestrator.
6. Reuse existing stack only (`pydantic`, `httpx`, stdlib, pytest). No new dependency needed.

### Architecture Compliance Guardrails

- **AD-1:** Orchestrator invokes ports and domain boundaries only. No direct adapter internals in domain modules.
- **AD-2:** Every step returns new state snapshot.
- **AD-3:** Runtime API lookup split from bulk snapshot refresh.
- **AD-4:** State adapters remain on shared contract (`state_code`, `lookup_one`, `fetch_bulk`).
- **AD-5:** Scoring and gate remain single authority (wired now, logic deepened in Epic 2).
- **AD-6:** Step failure never aborts before response rendering.
- **AD-8:** Website check stays behind `WebsitePort` contract already established.

### File Structure Requirements

#### Update files (read and preserve behavior)

- `obdb/agent/state.py`
  - Current state: frozen data models for OBDB/state license/website and `StepError`.
  - This story changes: add pipeline run-state + step-outcome models for orchestration.
  - Preserve: existing model field names/types used by current tests.
- `obdb/adapters/obdb_api_adapter.py`
  - Current state: runtime lookup by name/location against OBDB API.
  - This story changes: no runtime-path behavior change; only wire from orchestrator.
  - Preserve: error shapes (`StepError(step_id="obdb_lookup", ...)`) and return union.
- `obdb/adapters/website_http_adapter.py`
  - Current state: policy-aware deterministic website check with optional one browser fallback.
  - This story changes: orchestration wiring only.
  - Preserve: blocker codes and no hidden retries behavior.
- `obdb/ports/obdb_port.py`, `obdb/ports/state_license_port.py`, `obdb/ports/website_port.py`
  - Preserve runtime-checkable protocol contracts.

#### New files (expected)

- `obdb/agent/orchestrator.py`
- `obdb/domain/__init__.py`
- `obdb/domain/scoring.py`
- `obdb/domain/diff.py`
- `obdb/domain/gate.py`
- `obdb/ports/cache_port.py`
- `obdb/ports/renderer_port.py`
- `obdb/adapters/disk_cache_adapter.py`
- `obdb/adapters/cli_renderer_adapter.py`
- `obdb/tests/test_orchestrator.py`

### Implementation Pattern (lean/default)

- Keep orchestrator as one small deterministic function/class; avoid workflow framework.
- Use explicit local sequence list for step execution order and test against it.
- Propagate structured errors through state, not exceptions, for expected step failures.
- Keep placeholder implementations minimal for scoring/diff/gate to satisfy wiring and tests in this story; deep rules come in Epic 2.
- Prefer one shared failure-capture helper used by all steps to avoid duplicated guard code.

### Testing Requirements

- Add one focused orchestrator test module; avoid broad integration scaffolding.
- Cover non-trivial branch points:
  - happy path ordered execution
  - injected failure with continued rendering
  - immutable snapshot transitions
  - source-authority split (API lookup vs snapshot refresh)
- Keep snapshot/offline-first style; no live network in default tests.

### Previous Story Intelligence (1.3b)

- Keep website outcomes typed and coded (`policy_blocked`, `technical_blocked`, `config_error`).
- Browser fallback remains single-hop only (`allow_browser_fallback=False` on fallback call).
- Existing pattern in this repo: contract first, adapter/domain implementation second, tests third.
- Existing stories enforce explicit `StepError` over silent fallback behavior; keep same standard in orchestration.

### Git Intelligence Summary (recent commits)

- Recent commits touched adapters/ports/state/tests only; orchestrator/domain layer is new in this story.
- Commit pattern is small and boundary-first; follow same to reduce review churn.
- Existing tests use fixture/mocking style and protocol `isinstance` checks; reuse that style.

### Latest Tech Information

- Verified current latest stable versions align with project constraints:
  - `httpx` 0.28.1
  - `pydantic` 2.13.4
  - `pytest` 9.1.1
  - `ruff` 0.16.1
- No upgrades required for this story.

### References

- Epic/story ACs: `/epics.md` (Epic 1, Story 1.4)
- FR details: `prd.md` (FR-13, FR-14, FR-15)
- Architecture invariants: `ARCHITECTURE-SPINE.md` (AD-1..AD-8)
- Prior implementation context: `1-3-check-brewery-website-status-in-the-run.md`
- Prior implementation context: `1-3b-add-policy-aware-and-js-capable-website-access.md`
- Workflow constraints: `AGENTS.md`

## Project Context Reference

- No `project-context.md` discovered from `file:{project-root}/**/project-context.md`.

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.

### File List

- `1-4-preserve-ordered-execution-and-partial-evidence-on-failure.md` (created)
