---
baseline_commit: 8b4fbfa3bb4e2d322ff3984f7780d3fdb26cb4f4
---

# Story 1.3b: Add Policy-Aware and JS-Capable Website Access

Status: done

## Story

As a contributor,
I want website checks to honor crawl policy and support JS-rendered sites when allowed,
so that evidence collection stays ethical and resilient across modern brewery websites.

## Acceptance Criteria

1. **Given** a website URL **When** website collection starts **Then** the workflow checks `robots.txt` policy before non-trivial crawl behavior.
2. **Given** `robots.txt` disallows crawling **When** the check runs **Then** it returns a structured policy-blocked error and does not fetch page content.
3. **Given** website checks run **When** requests are made **Then** they include env-configured scraper identity header values.
4. **Given** a JS-rendered or anti-bot-blocked site **When** HTTP adapter cannot reliably evaluate content **Then** the system can use a browser-capable adapter path behind the same website port contract.
5. **Given** blocked outcomes **When** they are surfaced **Then** they use structured codes (`policy_blocked`, `technical_blocked`, `config_error`) and are never classified as `active`.
6. **Given** adapter selection **When** evaluation runs **Then** behavior is deterministic: HTTP first, optional single browser fallback on technical block only, no hidden retries.
7. **Given** website access is blocked/fails **When** pipeline continues **Then** partial evidence and explicit step error context are preserved.

## Tasks / Subtasks

- [x] Extend website error contract for structured blocker codes (AC: 2, 5, 7)
  - [x] Add typed website error code support in `obdb/agent/state.py` without breaking existing `StepError` users.
  - [x] Keep models frozen and deterministic.
- [x] Update website port contract for policy-aware and fallback-capable checks (AC: 1, 4, 6)
  - [x] Update `obdb/ports/website_port.py` to support deterministic HTTP-first evaluation with optional fallback path.
- [x] Implement policy-aware HTTP checker behavior (AC: 1, 2, 3, 5, 6)
  - [x] In `obdb/adapters/website_http_adapter.py`, parse and evaluate `robots.txt` before page fetch.
  - [x] Add env-configured identity header behavior:
    - `SCRAPER_IDENTITY_HEADER_NAME` default `User-Agent`
    - `SCRAPER_IDENTITY_HEADER_VALUE` required; missing value yields `config_error`.
  - [x] If `robots.txt` read/parse fails, return `technical_blocked` (single-attempt behavior).
- [x] Add browser-capable fallback path behind same port boundary (AC: 4, 6)
  - [x] Add optional browser-capable adapter entry point (new adapter file or injected dependency) behind `WebsitePort`.
  - [x] Only attempt fallback on explicit `technical_blocked` HTTP outcomes.
  - [x] Keep fallback attempts to at most one.
- [x] Add/extend tests for deterministic policy and fallback behavior (AC: 1-7)
  - [x] Robots disallow path => `policy_blocked` and no page fetch.
  - [x] Missing identity value => `config_error`.
  - [x] Unreadable/invalid `robots.txt` => `technical_blocked`.
  - [x] Technical block from HTTP path can trigger exactly one browser fallback attempt.
  - [x] Non-technical outcomes never trigger fallback.
  - [x] Fallback success path returns typed `WebsiteSignal`; fallback block/fail returns structured coded `StepError`.
  - [x] Protocol compliance tests for website adapters.
- [x] Keep existing tests green and run repo quality gates (AC: 1-7)
  - [x] `uv run ruff check obdb/`
  - [x] `uv run ruff format --check obdb/`
  - [x] `uv run pytest obdb/tests/ -v`

### Review Findings

- [x] [Review][Patch] Route robots technical failures through fallback path so browser fallback works on technical blocks [obdb/adapters/website_http_adapter.py:58]
- [x] [Review][Patch] Guard empty `SCRAPER_IDENTITY_HEADER_NAME` as `config_error` [obdb/adapters/website_http_adapter.py:45]
- [x] [Review][Patch] Ensure fallback call enforces single-hop semantics (`allow_browser_fallback=False`) [obdb/adapters/website_http_adapter.py:209]
- [x] [Review][Patch] Wrap browser checker exceptions as structured `technical_blocked` `StepError` [obdb/adapters/website_browser_adapter.py:20]

## Dev Notes

### Story Foundation and Epic Context

- This story extends Story 1.3 and must preserve its typed website signal behavior while adding ethical crawl policy and resilient JS-capable access.
- Business value: prevent unsafe/opaque crawl behavior while reducing false negatives on modern JS/challenge-heavy brewery sites.
- Sequencing constraint from sprint file: complete 1.3b before 1.4 to avoid pipeline and error-contract rework.

### Technical Requirements (must follow)

1. Keep hexagonal boundaries: orchestrator only calls ports; adapters implement ports.
2. Keep deterministic behavior for same input/config.
3. Keep single-attempt semantics for each transport path; no hidden retries.
4. Reuse existing dependencies (`httpx`, stdlib, `pydantic`) unless explicitly approved.
5. Preserve v0.1 UX rule: blocked outcomes must not be represented as `active`.

### Architecture Compliance Guardrails

- **AD-1**: Port-first orchestration; no adapter internals called from orchestrator.
- **AD-2**: Immutable state transitions and frozen models.
- **AD-6**: Error continuity to response with explicit structured context.
- **AD-8**: Policy-aware website access with identity headers, deterministic HTTP-first selection, optional one browser fallback on technical block only.

### File Structure Requirements

#### Update files

- `obdb/agent/state.py`
  - Add website-step structured error code typing (or equivalent typed extension) compatible with existing `StepError` usage.
- `obdb/ports/website_port.py`
  - Extend contract to support deterministic fallback-capable evaluation semantics.
- `obdb/adapters/website_http_adapter.py`
  - Add robots policy check, identity header handling, and coded blocker outcomes.
- `obdb/tests/test_website_http_adapter.py`
  - Extend for robots/header/coded blockers and deterministic fallback triggers.

#### New files (expected)

- `obdb/adapters/website_browser_adapter.py` (or equivalent browser-capable implementation entry point behind `WebsitePort`)
- `obdb/tests/test_website_browser_adapter.py` (if separate adapter implementation is added)

### Implementation Pattern (lean/default)

- Use `urllib.robotparser` (stdlib) for `robots.txt` allow/disallow checks.
- Keep HTTP transport as default path.
- Represent blocker reasons with explicit coded contract:
  - `policy_blocked`
  - `technical_blocked`
  - `config_error`
- Fallback selection algorithm:
  1. Run HTTP path.
  2. If result is `technical_blocked` and browser path configured, run browser path once.
  3. Return browser result; never loop back to HTTP.

### Testing Requirements

- Keep offline-first and deterministic tests; mock HTTP and robots fetches.
- Add regression test ensuring policy-blocked path does not request target page content.
- Add regression test ensuring no fallback attempt for `policy_blocked` or `config_error`.
- Keep protocol/runtime-checkable adapter compliance tests.

### Previous Story Intelligence (1.3)

- Existing website adapter and tests already establish typed signal and blocker handling.
- Story 1.3 review fixes tightened behavior:
  - Relative redirect normalization to absolute URL.
  - Non-2xx blocker detection.
  - Removed broad exception masking in adapter logic.
- Preserve these fixes while adding policy/fallback behavior.

### Git Intelligence Summary (recent commits)

- Recent implementation pattern is stable: state/port contract first, adapter implementation second, tests third.
- Continue same order to keep review surface small and predictable.

### Latest Tech Information (web-checked)

- Current project ecosystem versions remain suitable:
  - `httpx`: `0.28.1`
  - `pydantic`: `2.13.4`
  - `pytest`: `9.1.1`
  - `ruff`: `0.16.1`
- No dependency upgrades required for this story.

### References

- Story source: `epics.md` (Epic 1, Story 1.3b)
- FR details: `prd.md` (FR-4, FR-13, FR-14)
- Architecture invariants: `ARCHITECTURE-SPINE.md` (AD-1, AD-2, AD-6, AD-8)
- Prior implementation context: `1-3-check-brewery-website-status-in-the-run.md`
- Workflow constraints: `AGENTS.md`

## Project Context Reference

- No `project-context.md` discovered from `file:{project-root}/**/project-context.md`.

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Debug Log References

### Completion Notes List

- Added typed website error codes on `StepError` for `policy_blocked`, `technical_blocked`, and `config_error`.
- Extended `WebsitePort` contract and implemented deterministic HTTP-first behavior with optional single browser fallback on technical block only.
- Added robots policy check via stdlib `urllib.robotparser` before page fetch; disallow now returns coded policy block and skips page request.
- Added env-configured scraper identity header contract with required `SCRAPER_IDENTITY_HEADER_VALUE`.
- Added browser-capable adapter entry point (`WebsiteBrowserAdapter`) behind same website port boundary.
- Added deterministic tests for robots policy, config errors, technical blockers, and fallback behavior.
- Ran repo quality gates and full suite:
  - `uv run ruff check obdb/`
  - `uv run ruff format --check obdb/`
  - `uv run pytest obdb/tests/ -v`

### File List

- `obdb/agent/state.py` (modified)
- `obdb/ports/website_port.py` (modified)
- `obdb/adapters/website_http_adapter.py` (modified)
- `obdb/adapters/website_browser_adapter.py` (added)
- `obdb/tests/test_website_http_adapter.py` (modified)
- `obdb/tests/test_website_browser_adapter.py` (added)
- `1-3b-add-policy-aware-and-js-capable-website-access.md` (updated status/tasks/notes/file list)
- `sprint-status.yaml` (updated status to `done`)
