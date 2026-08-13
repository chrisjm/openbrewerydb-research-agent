# AGENTS.md — Development ethos for openbrewerydb-research-agent

## Non-negotiable workflow rules

1. **`uv sync` before you start any task.** Run `uv sync --extra dev` to ensure your environment matches the lockfile. Never install packages by hand.
2. **Work on a feature branch, never directly on `main`.** For each story, create a branch named `feat/<story-key>` (e.g. `feat/1-2-normalize-state-license-records`) before writing any code.
3. **Tests pass before every commit.** `uv run pytest obdb/tests/ -v` must be green. If a task introduces a test failure, fix it in that same task — do not defer.
4. **Ruff passes before every commit.** `uv run ruff check obdb/ && uv run ruff format --check obdb/`. Format violations are a build break, not a nit.
5. **One commit per plan task.** Commit messages follow the task packet's specified message exactly. Include the `Co-authored-by: Copilot` trailer.
6. **Open a PR when the story is complete.** After the final commit on the feature branch, open a PR targeting `main` with title `feat(<story-key>): <story title>` and a body that references the story file path. Do not merge — leave the PR for human review.

## Branch workflow

```
git checkout -b feat/<story-key>   # at story start
# ... implement, commit per task ...
gh pr create --base main --title "feat(<story-key>): <story title>" \
  --body "Story: docs/specs/<spec-id>/stories/<story-key>.md"
```

Required CI checks run automatically on every PR:
- `ci / unit-tests` — ruff + pytest
- `evals / eval-suite-pass` — placeholder until eval suite is wired
- `security / secret-scan` — gitleaks

## TDD discipline

- **Write the failing test first**, then implement the minimum code to make it pass, then refactor.
- Tests must cover the behavior stated in the task's "Implementation requirements" before any production code is written.
- A stub handler that vacuously passes a test does not count — tests must assert the actual behavior the task specifies.
- Snapshot fixtures are preferred over live HTTP in all default test runs. Gate live calls behind an explicit flag/command.

## Tooling

| Purpose | Command |
|---|---|
| Sync dependencies | `uv sync --extra dev` |
| Run all tests | `uv run pytest obdb/tests/ -v` |
| Run single test | `uv run pytest obdb/tests/test_orchestrator.py -v` |
| Lint (check) | `uv run ruff check obdb/` |
| Format (check) | `uv run ruff format --check obdb/` |
| Format (apply) | `uv run ruff format obdb/` |
| Create PR | `gh pr create --base main` |

## Scope discipline

- Do not widen scope beyond the current plan task packet.
- Do not auto-refresh snapshot fixtures — manual refresh only, documented per task.

