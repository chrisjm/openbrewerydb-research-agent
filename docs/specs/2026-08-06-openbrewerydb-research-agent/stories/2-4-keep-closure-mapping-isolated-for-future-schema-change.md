---
baseline_commit: 9814433d3043d57eef75ef6db99d99fa9315fa48
---

# Story 2.4: Keep Closure Mapping Isolated for Future Schema Change

Status: done

## Story

As a contributor,
I want closed-brewery mapping to stay isolated,
so that a future tag or SCD2 schema change does not force a full diff-engine rewrite.

## Acceptance Criteria

1. **Given** current v0.1 closure fixtures **When** the closure mapping runs **Then** it supports the current `brewery_type='closed'` convention.
2. **Given** future schema changes **When** the closure convention changes **Then** the update is isolated behind a dedicated mapping boundary rather than the diff engine itself.
3. **Given** a closed-brewery record **When** the diff or gate logic runs **Then** the closure mapping remains explicit, deterministic, and testable.
4. **Given** current repo conventions **When** the closure logic is implemented **Then** it stays separate from the diff contract and does not leak field-specific assumptions into the generic diff builder.

## Tasks / Subtasks

- [ ] Isolate closure mapping behind one dedicated module or boundary (AC: 1, 2, 4)
  - [ ] Create a dedicated closure-mapping layer under the domain or adapter boundary.
  - [ ] Keep the mapping logic independent from field-diff generation.
  - [ ] Make the mapping explicit and simple enough to swap with a future schema change.
- [ ] Preserve current closure behavior while keeping diff engine generic (AC: 1, 3, 4)
  - [ ] Support current `brewery_type='closed'` semantics without embedding closure logic in the diff engine.
  - [ ] Keep the diff engine focused on field comparison and provenance, not brewery-specific policy.
- [ ] Add focused regression tests (AC: 1, 2, 3)
  - [ ] Add a test proving the closure mapping supports current closed-brewery fixtures.
  - [ ] Add a regression test proving the diff engine remains generic and not coupled to a hardcoded closure policy.
  - [ ] Add a test or contract proving a future schema-change swap can happen behind a dedicated mapping boundary.
- [ ] Keep existing checks green and run repo quality gates
  - [ ] `uv run ruff check obdb/`
  - [ ] `uv run ruff format --check obdb/`
  - [ ] `uv run pytest obdb/tests/ -v`

## Dev Notes

### Story Foundation and Epic Context

- This story preserves future-proofing for the closure logic after the confidence, diff, and render pipeline is stable.
- Business value: the diff engine remains generic while brewery-specific business rules remain isolated and easy to evolve.

### Technical Requirements (must follow)

1. Keep closure mapping behind a small dedicated boundary; do not mix it into generic diff behavior.
2. Keep the diff engine generic and stable; schema-specific policy belongs outside the engine.
3. Preserve deterministic behavior with current fixtures and minimal assumptions.
4. Keep tests fixture-based and offline.

### Architecture Compliance Guardrails

- **AD-5:** scoring and gate remain single authority; closure is a separate domain concern.
- **FR-9:** closure mapping remains isolated for future schema changes.
- **FR-10:** evidence refs remain attached at the diff layer, not inside brewery-specific closure policy.

### File Structure Requirements

#### Update files (read and preserve behavior)

- `obdb/domain/diff.py`
- `obdb/agent/state.py`

#### New files (expected)

- `obdb/domain/closure.py` or equivalent isolated mapping module
- `obdb/tests/test_closure_mapping.py`

### Implementation Pattern (lean/default)

- Create one explicit function such as `is_closed_brewery(record)` or `map_closure_status(record)` that the diff/gate boundary can call.
- Keep field naming and output generic; the mapping layer should return an explicit boolean or status code, not a diff-specific schema.
- Design it so future tag or schema changes are a single boundary update, not a diff-engine rewrite.

### Testing Requirements

- Cover current closed-brewery behavior and one future-change seam.
- Ensure the generic diff does not need brewery-specific logic to work.
- Keep the suite narrow and deterministic.

### References

- Epic 2 story definition: `epics.md`
- Diff engine: `obdb/domain/diff.py`
- Architecture invariants: `ARCHITECTURE-SPINE.md`
- Workflow constraints: `AGENTS.md`

## Project Context Reference

- No `project-context.md` discovered from `file:{project-root}/**/project-context.md`.

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Completion Notes List

- Story template created for Epic 2, Story 2.4.

### File List

- `2-4-keep-closure-mapping-isolated-for-future-schema-change.md` (created)
