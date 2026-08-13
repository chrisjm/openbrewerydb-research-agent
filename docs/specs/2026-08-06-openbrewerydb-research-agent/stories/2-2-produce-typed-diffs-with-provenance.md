---
baseline_commit: 9814433d3043d57eef75ef6db99d99fa9315fa48
---

# Story 2.2: Produce Typed Diffs with Provenance

Status: done

## Story

As a contributor,
I want field-level diffs tied to evidence refs,
so that each proposed change is reviewable and traceable.

## Acceptance Criteria

1. **Given** an OBDB record and a candidate record **When** the diff runs **Then** each changed field includes field name, old value, new value, confidence, and evidence refs.
2. **Given** a no-change comparison **When** the diff runs **Then** it yields an empty diff list.
3. **Given** missing or weak evidence **When** the diff is computed **Then** confidence is reduced or the run falls back to evidence-only output according to the gate rules.
4. **Given** the same inputs **When** the diff is built twice **Then** the output is deterministic and stable.

## Tasks / Subtasks

- [ ] Add typed diff generation with provenance metadata (AC: 1, 4)
  - [ ] Create `obdb/domain/diff.py` with a pure diff builder that compares field values and returns structured change entries.
  - [ ] Include field name, old value, new value, confidence, and evidence refs in each result item.
  - [ ] Keep the diff deterministic for equivalent inputs and output ordering stable.
- [ ] Wire diff output into the run state (AC: 1, 4)
  - [ ] Update the orchestrator to call the diff step after confidence has been computed.
  - [ ] Store the diff payload in the frozen run state without mutating prior state snapshots.
  - [ ] Preserve step outcomes and explicit render behavior for diff failures.
- [ ] Add no-op and fallback behavior (AC: 2, 3)
  - [ ] Return an empty list when no field values differ.
  - [ ] Ensure a missing or low-confidence evidence signal results in lower trust metadata or gate failure, not silent success.
- [ ] Add focused regression tests (AC: 1, 2, 3, 4)
  - [ ] Add a test proving field-level diff structure includes provenance metadata.
  - [ ] Add a test proving identical records yield an empty diff.
  - [ ] Add a test proving low-evidence or weak provenance is surfaced in the diff payload metadata.
- [ ] Keep existing checks green and run repo quality gates
  - [ ] `uv run ruff check obdb/`
  - [ ] `uv run ruff format --check obdb/`
  - [ ] `uv run pytest obdb/tests/ -v`

## Dev Notes

### Story Foundation and Epic Context

- This story follows the deterministic confidence gate from Story 2.1 and provides the structured evidence diff that the renderer consumes.
- Business value: reviewers can see exactly what changed, with traceability back to website, state, and OBDB evidence.

### Technical Requirements (must follow)

1. Keep diff generation pure and deterministic.
2. Use the shared frozen state model and explicit step outcomes.
3. Preserve the single-authority gate model: scoring and gate decide whether output is copyable or evidence-only.
4. Evidence refs must be explicit and traceable to step or source URLs when available.
5. Keep all default tests offline and fixture-based.

### Architecture Compliance Guardrails

- **AD-5:** Scoring and gate remain single authority; diff output is evidence metadata only.
- **AD-6:** Step failure still continues to response rendering.
- **FR-8:** produce typed field diffs.
- **FR-10:** attach evidence refs to changed fields when available.

### File Structure Requirements

#### Update files (read and preserve behavior)

- `obdb/agent/orchestrator.py`
- `obdb/agent/state.py`
- `obdb/domain/scoring.py`

#### New files (expected)

- `obdb/domain/diff.py`
- `obdb/tests/test_diff_provenance.py`

### Implementation Pattern (lean/default)

- Prefer a small pure function that takes current and candidate records and emits a list of change dictionaries.
- Store evidence refs as simple strings or structured metadata that renderer code can consume without re-deriving source data.
- Use stable ordering by field name to keep diffs deterministic.

### Testing Requirements

- Default tests should stay offline and use fixed fixtures.
- Treat provenance as part of the contract, not incidental metadata.
- One focused suite is enough; do not add broad integration scaffolding.

### References

- Epic 2 story definition: `epics.md`
- Prior implementation context: `obdb/agent/orchestrator.py`
- Confidence gate: `obdb/domain/scoring.py`
- Workflow constraints: `AGENTS.md`

## Project Context Reference

- No `project-context.md` discovered from `file:{project-root}/**/project-context.md`.

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Completion Notes List

- Story template created for Epic 2, Story 2.2.

### File List

- `2-2-produce-typed-diffs-with-provenance.md` (created)
