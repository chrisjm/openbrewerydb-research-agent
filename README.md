# openbrewerydb-research-agent

A CLI research engine that prepares high-confidence brewery corrections for [Open Brewery DB](https://www.openbrewerydb.org/). Gathers authoritative signals from OBDB, state licensing sources, and brewery websites, scores confidence, and outputs either a copyable CSV diff or evidence-only findings.

## What it does

**Problem:** OBDB contributors spend time tab-hopping between OBDB, state licensing boards, and brewery websites to verify a single brewery record.

**Solution:** One CLI command, one brewery name + location input. The agent:
1. Fetches the current OBDB record
2. Queries state licensing databases (CA, CO, TX)
3. Checks brewery website for active/closed status
4. Computes confidence score from signal alignment
5. Returns either copyable CSV diff (confidence ≥ threshold) or evidence-only output

Result: Contributors get trusted correction proposals with full provenance, fewer low-quality PRs, faster reviews.

## Quick start

### Install
```bash
uv sync --extra dev
```

### Test
```bash
uv run pytest obdb/tests/ -v
```

### Lint & format
```bash
uv run ruff check obdb/
uv run ruff format obdb/
```

## Project structure

```
obdb/
├── agent/           # Orchestrator: runs the research pipeline
├── adapters/        # Pluggable data sources
│   ├── obdb_api_adapter.py         # Brewery lookup
│   ├── ca/co/tx_license_adapter.py # State license queries
│   └── website_*_adapter.py        # Website status checks
├── domain/          # Business logic
│   ├── closure.py       # Closed brewery mapping
│   ├── diff.py          # Field diff generation
│   └── scoring.py       # Confidence computation
├── ports/           # Interface contracts
└── tests/           # Test suite with snapshot fixtures
```

## Architecture

- **Stateful pipeline:** Each brewery run is immutable `BreweryRunState` that flows through OBDB lookup → state license fetch → website check → confidence score → output gate.
- **Error handling:** Structured errors flow alongside results; pipeline continues to gather partial evidence on failure.
- **Pluggable adapters:** State license sources (CA, CO, TX) conform to one typed contract, website checks support both HTTP and browser-based approaches.
- **Confidence engine:** Combines signal alignment, source agreement, and closure indicators into single 0.0–1.0 score with breakdown.

## Development

**Workflow:** `uv sync` → write failing test → implement → lint (`ruff check + format --check`) → test → commit. See [AGENTS.md](AGENTS.md) for full discipline.

**Key rules:**
- One commit per task; include commit message from task packet
- Branch name: `feat/<story-key>`
- Tests must pass before every commit
- Ruff lint/format violations block commits
- Open PR on completion, leave for human review (do not merge)

**CI checks on every PR:**
- `unit-tests` — ruff lint/format + pytest
- `eval-suite-pass` — eval pipeline (placeholder)
- `secret-scan` — gitleaks

## Dependencies

- **httpx** ≥0.27 — HTTP client for OBDB & state license APIs
- **pydantic** ≥2.7 — Data validation & typed models
- **pytest, pytest-httpx, ruff** — dev only

## Status

**v0.1:** OBDB lookup, CA/CO/TX license adapters, website status checks, confidence scoring, CSV diff output with provenance. Human review required; no LLM extraction.

Future versions will add browser integration, additional states, and automated corrections with guardrails.
