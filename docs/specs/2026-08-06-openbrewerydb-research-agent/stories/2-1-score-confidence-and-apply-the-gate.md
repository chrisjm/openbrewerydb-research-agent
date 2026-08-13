---
baseline_commit: 42bbe279d766b190d4816d25a4a2fe59b2956c7d
---

# Story 2.1: Score Confidence and Apply the Gate

Status: done

## Story

As a contributor,
I want deterministic confidence scoring with a configurable threshold,
so that I know when the run output is safe to copy into a correction PR.

## Acceptance Criteria

1. **Given** the same inputs and cache state **When** the score is computed twice **Then** the confidence value is the same both times.
2. **Given** the default configuration **When** the score is computed **Then** the default threshold is 0.7.
3. **Given** CLI or config override input **When** the threshold is set **Then** the gate uses the override value instead of the default.
4. **Given** confidence below threshold **When** rendering occurs **Then** copyable output is suppressed and evidence-only output remains available.

## Tasks / Subtasks

- [ ] Add deterministic scoring authority and threshold gate (AC: 1, 2, 3, 4)
  - [ ] Create `obdb/domain/scoring.py` with a deterministic score model and default threshold constant.
  - [ ] Add a gate function or policy object that compares score against threshold and returns pass/fail.
  - [ ] Ensure repeated runs with identical inputs produce identical score results.
- [ ] Wire score and gate into the run pipeline (AC: 1, 3, 4)
  - [ ] Update orchestrator to invoke confidence scoring as the configured step after website evaluation.
  - [ ] Store score and gate result in the frozen run state without mutating previous snapshots.
  - [ ] Propagate below-threshold state so the renderer can switch to evidence-only output.
- [ ] Add rendering gating behavior (AC: 4)
  - [ ] Ensure copyable CSV output is only rendered when gate passes.
  - [ ] Keep evidence output available in the failing case without leaking untrusted CSV.
- [ ] Add focused tests for score determinism and threshold behavior (AC: 1, 2, 3, 4)
  - [ ] Add regression test for equal inputs producing equal confidence values.
  - [ ] Add test covering default threshold 0.7.
  - [ ] Add test covering threshold override and below-threshold suppression.
- [ ] Keep existing checks green and run repo quality gates
  - [ ] `uv run ruff check obdb/`
  - [ ] `uv run ruff format --check obdb/`
  - [ ] `uv run pytest obdb/tests/ -v`

## Dev Notes

### Story Foundation and Epic Context

- This is Epic 2 follow-on work after the fixed-order pipeline story in Epic 1.
- The confidence and gate logic must remain deterministic and single-authority; renderers must not recompute it.
- Business value: contributors can trust when output is safe for PR copy and when evidence-only output is the correct fallback.

### Technical Requirements (must follow)

1. Keep scoring deterministic for same inputs and cache state.
2. Default gate threshold is 0.7 unless config override is provided.
3. Preserve immutable state transitions and explicit step outcomes through the orchestrator.
4. Renderers must consume gate result, not re-derive it.
5. Keep all tests offline and fixture-first.

### Architecture Compliance Guardrails

- **AD-5:** Scoring and gate remain single authority and should be domain-owned.
- **AD-6:** Step failure still continues to response rendering.
- **FR gating:** below-threshold runs suppress CSV and show evidence-only output.

### File Structure Requirements

#### Update files (read and preserve behavior)

- `obdb/agent/orchestrator.py`
  - This story wires in scoring and gate results.
- `obdb/agent/state.py`
  - Preserve immutable run-state model and extend with confidence/gate fields if needed.
- `obdb/tests/test_orchestrator.py`
  - Extend with scoring and gate fixtures.

#### New files (expected)

- `obdb/domain/scoring.py`
- `obdb/domain/gate.py` (if kept separate from scoring, or fold into scoring if simpler)
- `obdb/tests/test_confidence_gate.py` or equivalent focused suite

### Implementation Pattern (lean/default)

- Keep the scoring model small and deterministic.
- Prefer explicit threshold constants and pure functions over hidden state.
- Use the existing repo’s pydantic frozen model pattern and test style.

### Testing Requirements

- Add focused tests for determinism, threshold, and suppression behavior.
- Do not rely on live network calls in default tests.
- One minimal suite is enough; avoid broad integration scaffolding.

### References

- Epic 2 story definition: `epics.md`
- Architecture invariants: `ARCHITECTURE-SPINE.md`
- Prior pipeline implementation: `obdb/agent/orchestrator.py`
- Workflow constraints: `AGENTS.md`

## Project Context Reference

- No `project-context.md` discovered from `file:{project-root}/**/project-context.md`.

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Completion Notes List

- Story template created for Epic 2, Story 2.1.

### File List

- `2-1-score-confidence-and-apply-the-gate.md` (created)
