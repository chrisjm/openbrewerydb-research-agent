---
baseline_commit: 7f74f67e673fd48960b97d035d587ce738776e1b
---

# Story 1.3: Check Brewery Website Status in the Run

Status: done

## Story

As a contributor,
I want the run to check website status and closure keywords,
so that I can see whether the brewery website supports or weakens the correction.

## Acceptance Criteria

1. **Given** a brewery website URL **When** the website check runs **Then** it returns one of the typed signals: `active`, `redirect`, `404`, or `closed_keyword`.
2. **Given** a brewery website response body **When** closure phrases are configured **Then** the check uses that phrase list (no LLM extraction).
3. **Given** a single-attempt request failure **When** the website check runs **Then** it surfaces a `StepError` explicitly and does not silently retry.
4. **Given** a website that cannot be reliably evaluated by plain HTTP (JS-rendered flow, anti-bot challenge, or auth wall) **When** the check runs **Then** it returns a structured `StepError` explaining the blocker and does not misclassify the site as `active`.

## Tasks / Subtasks

- [x] Add typed website signal model(s) in `obdb/agent/state.py` (AC: 1)
  - [x] Keep model(s) frozen and compatible with existing `StepError` flow.
  - [x] Include enough fields for pipeline use (signal, final URL, status code, matched phrase, source URL).
- [x] Add website port contract in `obdb/ports/website_port.py` (AC: 1, 3)
  - [x] `check(url: str) -> WebsiteSignal | StepError`.
- [x] Implement HTTP website adapter in `obdb/adapters/website_http_adapter.py` (AC: 1, 2, 3)
  - [x] Classify status into `active`, `redirect`, `404`, `closed_keyword`.
  - [x] Use configured closure phrase list (constructor arg + default constant).
  - [x] Use a single request attempt and surface failures as `StepError(step_id="website_check", ...)`.
- [x] Add tests in `obdb/tests/test_website_http_adapter.py` (AC: 1, 2, 3)
  - [x] 200 + no closure phrase => `active`.
  - [x] 3xx (no follow) => `redirect`.
  - [x] 404 => `404`.
  - [x] 200 + closure phrase present => `closed_keyword`.
  - [x] request/network error => `StepError`, with no retry behavior.
  - [x] JS-only/challenge/auth-wall-like response path => explicit `StepError` classification (not false `active`).
  - [x] protocol compliance: `isinstance(adapter, WebsitePort)` is `True`.
- [x] Keep existing tests green; run targeted then full test suite and ruff checks per repo workflow (AC: 1, 2, 3).

### Review Findings

- [x] [Review][Patch] Handle challenge/auth blocker detection for non-2xx responses to satisfy AC4 detail guarantees [obdb/adapters/website_http_adapter.py:62]
- [x] [Review][Patch] Remove broad `except Exception` that masks non-request defects as request failures [obdb/adapters/website_http_adapter.py:41]
- [x] [Review][Patch] Normalize redirect `Location` header to absolute `final_url` for relative redirects [obdb/adapters/website_http_adapter.py:47]

## Dev Notes

### Story Foundation and Epic Context

- This story is Epic 1 signal collection work between state-license normalization (1.2/1.2b) and pipeline continuity wiring (1.4).
- The output here must be typed and deterministic so Story 1.4 can plug it into ordered pipeline state with explicit errors.
- Business value: closure signals and website liveness influence whether corrections are trustworthy before diff/gate.

### Technical Requirements (must follow)

1. Keep hexagonal boundaries: port in `obdb/ports`, implementation in `obdb/adapters`.
2. Keep immutable state models (`frozen=True`) and explicit error envelopes via `StepError`.
3. No LLM parsing; closure detection is deterministic substring matching over configured phrases.
4. No hidden retries. Exactly one request attempt for v0.1.
5. Reuse existing dependencies only (`httpx`, stdlib, pydantic).
6. Preserve adapter polymorphism: website checking must stay behind `WebsitePort` so HTTP-only and browser-capable implementations can coexist without orchestrator branching.

### Architecture Compliance Guardrails

- **AD-1**: Orchestrator must call a port, not adapter internals. Add `WebsitePort` now so Story 1.4 can wire it cleanly.
- **AD-2**: Return typed model or `StepError`; no mutable shared state.
- **AD-6**: Errors must be structured and recoverable by later response rendering.
- Keep deterministic behavior: same input URL/body + same phrase list => same typed signal.
- Do not let transport limitations leak into false positives. If evaluation is blocked by JS/challenge/auth, return `StepError` and continue pipeline per AD-6.

### File Structure Requirements

#### New files

- `obdb/ports/website_port.py`
- `obdb/adapters/website_http_adapter.py`
- `obdb/tests/test_website_http_adapter.py`

#### Update files

- `obdb/agent/state.py`
  - Current state: defines `OBDBRecord`, `StateLicenseRecord`, and `StepError` as frozen models.
  - This story changes: append website signal model(s) only; do not break existing model fields.
  - Preserve: all existing models and their field contracts used by current adapter tests.

- `obdb/ports/__init__.py` and/or `obdb/adapters/__init__.py` (only if project pattern requires exports)
  - Preserve current import behavior for existing tests.

### Implementation Pattern (lean/default)

- `WebsiteHttpAdapter` constructor should accept closure phrases:
  - `closure_phrases: tuple[str, ...] = DEFAULT_CLOSURE_PHRASES`
- For redirect detection, prefer request with `follow_redirects=False` and classify 3xx as `redirect`.
- For closure phrase scan:
  - lowercase response text and phrase list.
  - return `closed_keyword` when first phrase match appears.
- Suggested classification order:
  1. Request error -> `StepError`
  2. 3xx -> `redirect`
  3. 404 -> `404`
  4. 2xx + closure phrase hit -> `closed_keyword`
  5. otherwise -> `active`
- Add a blocker branch before `active`: if body/status indicates bot challenge, script-required shell, or auth gate with no extractable brewery evidence, return `StepError(step_id="website_check", message="<blocker detail>", source=<url>)`.

### Multi-adapter and JS-only Readiness

- Treat `website_http_adapter.py` as one implementation, not the only future path.
- Keep parsing/classification logic independent from fetch transport so a browser-backed adapter can reuse it later.
- Follow the same pattern already seen in state adapters (normal path + explicit blocker/error path) to avoid special-case orchestrator logic.
- Record blocked domains/patterns in deferred work when discovered, with enough detail to decide whether to add a browser-capable adapter in a follow-up story.

### Testing Requirements

- Use `pytest-httpx`; no live HTTP in default test runs.
- Add one test that proves no silent retry behavior:
  - configure one failing mocked response and assert one call path returns `StepError`.
- Keep tests deterministic and fixture-light (inline response text is sufficient).

### Previous Story Intelligence (1.2 / 1.2b)

- Existing adapters already enforce typed return unions and `StepError` propagation; follow the same pattern.
- Story 1.2b established a strong default: offline/snapshot-first tests and explicit live-network behavior only when requested.
- Keep dependency discipline: stdlib + `httpx` only; do not add parsing libraries for keyword detection.

### Git Intelligence Summary (recent commits)

- Recent work concentrated in adapters, ports, and tests; that structure should be reused.
- Contract evolution happened in ports first, then adapter implementation, then tests.
- Continue that order here to avoid drift and to keep protocol compliance tests simple.

### Latest Tech Information (web-checked)

- Current project minimums are still aligned with latest stable ecosystem:
  - `httpx` latest: `0.28.1`
  - `pydantic` latest: `2.13.4`
  - `pytest` latest: `9.1.1`
  - `ruff` latest: `0.16.1`
- No dependency upgrade is required for this story; implementation should use current repo constraints in `pyproject.toml`.

### References

- Epic story + ACs: `epics.md`
- FR-4 details and NFRs: `prd.md`
- Architecture invariants AD-1/AD-2/AD-6: `ARCHITECTURE-SPINE.md`
- Prior story learnings: `1-2-normalize-state-license-records-through-shared-adapters.md`
- Prior story learnings: `1-2b-capture-real-license-source-snapshots.md`
- Project workflow constraints: `AGENTS.md`

## Project Context Reference

- No `project-context.md` file was discovered from `file:{project-root}/**/project-context.md` during activation.

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Debug Log References

### Completion Notes List

- Added `WebsiteSignal` frozen model in shared state for typed website outcomes.
- Added `WebsitePort` contract and `WebsiteHttpAdapter` implementation with deterministic status/keyword classification.
- Added blocker detection for JS/challenge/auth-wall pages to return structured `StepError` instead of false `active`.
- Added focused adapter tests for typed signals, configured closure phrase behavior, single-attempt failure path, blocker path, and protocol compliance.
- Ran repo checks: `uv run ruff check obdb/`, `uv run ruff format --check obdb/`, `uv run pytest obdb/tests/ -v`.

### File List

- `obdb/agent/state.py` (modified)
- `obdb/ports/website_port.py` (added)
- `obdb/adapters/website_http_adapter.py` (added)
- `obdb/tests/test_website_http_adapter.py` (added)
- `1-3-check-brewery-website-status-in-the-run.md` (updated status/tasks/notes/file list)
- `sprint-status.yaml` (updated status to `review`)
