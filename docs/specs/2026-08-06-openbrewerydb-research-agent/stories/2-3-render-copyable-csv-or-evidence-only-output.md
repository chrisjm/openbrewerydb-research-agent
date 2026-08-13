---
baseline_commit: 2dea28bd65c75d1cbb86dfe09d13cccf8d93fb6
---

# Story 2.3: Render Copyable CSV or Evidence-Only Output

Status: done

## Story

As a contributor,
I want the CLI to render copyable CSV only when the gate passes and evidence-only output otherwise,
so that I can paste only trusted corrections into PRs.

## Acceptance Criteria

1. **Given** a gate-passing run **When** the renderer runs **Then** it emits valid CSV containing changed fields only.
2. **Given** a gate-passing run **When** the output is copied into a maintainer PR workflow **Then** the CSV remains reviewable and paste-ready.
3. **Given** a below-threshold run **When** the renderer runs **Then** it emits evidence-only output with source URLs and snippets.
4. **Given** a below-threshold run **When** the renderer prepares output **Then** it contains no copyable CSV block.
5. **Given** an error state **When** response rendering happens **Then** the final rendering still respects the gate and keeps evidence-first wording.

## Tasks / Subtasks

- [ ] Add output rendering policy based on gate result (AC: 1, 3, 4, 5)
  - [ ] Update the orchestrator or renderer boundary so gate result is the single decision authority for output mode.
  - [ ] Suppress CSV output on `gate == "fail"` and render evidence-only text instead.
  - [ ] Keep the render path active even after step errors so the final response still reaches the caller.
- [ ] Keep copyable output in the passing case (AC: 1, 2)
  - [ ] Emit CSV-only output for pass paths with changed fields and no extra narrative noise.
  - [ ] Preserve the field list and provenance metadata expected by human reviewers.
- [ ] Add evidence-first output formatting in failing cases (AC: 3, 4)
  - [ ] Include target name/location and source URLs or step evidence.
  - [ ] Include a clear message that copyable CSV has been suppressed due to low confidence.
- [ ] Add focused regression tests (AC: 1, 3, 4, 5)
  - [ ] Add a test proving copyable output is suppressed when the gate fails.
  - [ ] Add a test proving evidence-ready output is retained during a failing gate.
  - [ ] Add a test proving final render after step failure still includes response output.
- [ ] Keep existing checks green and run repo quality gates
  - [ ] `uv run ruff check obdb/`
  - [ ] `uv run ruff format --check obdb/`
  - [ ] `uv run pytest obdb/tests/ -v`

## Dev Notes

### Story Foundation and Epic Context

- This story closes the Epic 2 loop by ensuring the rendered response matches the trust gate: trusted passes are copyable; low-confidence runs remain evidence-only.
- Business value: contributors avoid pasting untrusted corrections into PRs while still retaining exact evidence to explain why a run was rejected.

### Technical Requirements (must follow)

1. Use the gate result as the single source of truth for render mode.
2. Keep renderers dumb and deterministic; do not recompute confidence or gate logic inline.
3. Preserve the final-response render on step failures.
4. Evidence output must remain readable by humans and safe to paste in issue/PR comments.
5. Keep default tests offline and fixture-first.

### Architecture Compliance Guardrails

- **AD-5:** scoring and gate remain domain-owned; render only consumes their result.
- **AD-6:** step failure still continues to response rendering.
- **FR-7:** suppress copyable output when confidence is below threshold.
- **FR-11:** copyable CSV rendering only when gate passes.
- **FR-12:** evidence-first CLI rendering in both passing and failing cases.

### File Structure Requirements

#### Update files (read and preserve behavior)

- `obdb/agent/orchestrator.py`
- `obdb/agent/state.py`

#### New files (expected)

- `obdb/tests/test_orchestrator.py` (or extended regression module)

### Implementation Pattern (lean/default)

- Add one small run-time decision in the orchestrator: `gate == "fail"` => `render_evidence_only`, else normal renderer.
- Preserve the normal renderer path for `gate == "pass"` to keep CSV output easy to review and copy.
- Keep message text short, deterministic, and copy-safe.

### Testing Requirements

- Cover pass-path render output and fail-path evidence-only output.
- Verify step-failure render still reaches the response stage.
- Keep tests targeted and minimal; no broad integration scaffolding.

### References

- Epic 2 story definition: `epics.md`
- Prior implementation context: `obdb/agent/orchestrator.py`
- Gate logic: `obdb/domain/scoring.py`
- Workflow constraints: `AGENTS.md`

## Project Context Reference

- No `project-context.md` discovered from `file:{project-root}/**/project-context.md`.

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Completion Notes List

- Story template created for Epic 2, Story 2.3.

### File List

- `2-3-render-copyable-csv-or-evidence-only-output.md` (created)
