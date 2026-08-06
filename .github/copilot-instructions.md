# Copilot Instructions for `openbrewerydb-research-agent`

## Build, test, and lint commands

Use **`uv` for all Python tooling** in this repository.

| Purpose | Command |
| --- | --- |
| Sync dependencies | `uv sync --extra dev` |
| Run all tests | `uv run pytest obdb/tests/ -v` |
| Run single test file | `uv run pytest obdb/tests/test_parse.py -v` |
| Run single test case | `uv run pytest obdb/tests/test_parse.py::test_parse_lookup_by_name -v` |
| Lint (check) | `uv run ruff check obdb/` |
| Format (check) | `uv run ruff format --check obdb/` |
| Format (apply) | `uv run ruff format obdb/` |
| Run CLI harness | `uv run python -m obdb.agent.cli` |
| Run Discord bot | `uv run brewery-agent` |

**Workflow rule:** `uv sync --extra dev` → write failing tests → implement → `ruff check + format --check` → `pytest` → commit.

## Key conventions

- **Tooling:** `uv` only (`uv sync`, `uv run ...`). No direct `pip`/`python`.
- **Formatting/lint:** `ruff` — check and format must pass before every commit.
- **TDD:** failing test first, then implementation. See `AGENTS.md` for full rules.
- **State:** frozen pydantic `BaseModel`, transitions via `model_copy(update=...)`.
- **Errors:** EXECUTE surfaces failures in `state.error`; flow always continues to RESPOND.
- **Tests:** snapshot fixtures by default; live HTTP only with explicit flag.
- **Commits:** one commit per plan task packet; message specified in packet.
