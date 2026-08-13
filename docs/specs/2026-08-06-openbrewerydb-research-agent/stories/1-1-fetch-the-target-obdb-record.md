---
baseline_commit: 566c5a4fef8fa3b79a79699a53cffbcd38ac5a50
---

# Story 1.1: Fetch the Target OBDB Record

Status: done

## Story

As a contributor,
I want to enter a brewery name and location and fetch the matching OBDB record,
so that I can verify the target brewery before comparing other sources.

## Acceptance Criteria

1. **Given** a brewery name and location **When** the CLI runs the OBDB lookup **Then** it returns one typed `OBDBRecord` for a known match.
2. **Given** a brewery name and location that does not exist in OBDB **When** the CLI runs the OBDB lookup **Then** it returns a structured not-found result (not an exception crash).
3. **Given** any single-brewery lookup **When** the adapter is invoked **Then** it calls the OBDB API directly and does not read from a local bulk-dataset cache.

## Tasks / Subtasks

- [x] Scaffold project: `pyproject.toml`, `obdb/` package skeleton per architecture structural seed (AC: all)
  - [x] Add `httpx` (HTTP client) and `pydantic` (v2, frozen models) as runtime deps
  - [x] Add `pytest`, `pytest-httpx` (or `respx`) as dev deps
- [x] Define `OBDBRecord` and `StepError` frozen Pydantic models in `obdb/agent/state.py` (AC: 1, 2)
- [x] Define `OBDBPort` protocol in `obdb/ports/obdb_port.py` with `lookup_one(name: str, location: str) -> OBDBRecord | None` (AC: 1, 2, 3)
- [x] Implement `OBDBApiAdapter` in `obdb/adapters/obdb_api_adapter.py` that calls `https://api.openbrewerydb.org/v1/breweries/search?query=<name>&per_page=5` and filters by location (AC: 1, 2, 3)
  - [x] Map OBDB JSON response to `OBDBRecord`; return `None` on no-match
  - [x] Raise/surface `StepError` on HTTP errors (non-2xx or timeout), not bare exception
- [x] Write snapshot fixture tests in `obdb/tests/test_obdb_adapter.py` using pre-recorded response JSON (AC: 1, 2)
  - [x] Happy path: known brewery fixture returns populated `OBDBRecord`
  - [x] Not-found path: empty response returns `None`
  - [x] Error path: 5xx response surfaces `StepError`, does not raise unhandled exception

## Dev Notes

### Architecture Constraints (must follow — AD-1, AD-2, AD-3)

- **Hexagonal boundary:** `OBDBApiAdapter` implements `OBDBPort`. Orchestrator (Story 1.4) will call the port, not the adapter directly. For this story the adapter can be instantiated directly in tests and a thin CLI smoke-path.
- **Immutable state:** `OBDBRecord` must be a `frozen=True` Pydantic `BaseModel`. Use `model_copy(update=...)` for any future derived state. No attribute mutation after construction.
- **AD-3 source split:** This adapter ONLY covers runtime single-brewery lookup via the OBDB API. Bulk cache refresh (OBDB GitHub snapshots) is out of scope for this story and must not be implemented here.

### OBDB API

- Base URL: `https://api.openbrewerydb.org/v1`
- Lookup endpoint: `GET /breweries/search?query={name}&per_page=5`
- Response: JSON array of brewery objects. Key fields to map: `id`, `name`, `brewery_type`, `street` (or `address_1`), `city`, `state_province` (or `state`), `postal_code`, `country`, `website_url`, `phone`, `longitude`, `latitude`.
- No auth required (public endpoint, NFR-4).
- Filter the returned list by `city`/`state` match on the `location` parameter to select the correct record. If zero records match after filtering, return `None`.

### File Locations (architecture structural seed)

```
obdb/
  __init__.py
  agent/
    __init__.py
    state.py          # OBDBRecord, StepError (NEW)
  ports/
    __init__.py
    obdb_port.py      # OBDBPort protocol (NEW)
  adapters/
    __init__.py
    obdb_api_adapter.py  # OBDBApiAdapter (NEW)
  tests/
    __init__.py
    test_obdb_adapter.py  # snapshot fixture tests (NEW)
    fixtures/
      obdb_search_hit.json    # pre-recorded OBDB API response, 1 match
      obdb_search_empty.json  # pre-recorded OBDB API response, 0 matches
```

### Models (minimum viable shape for Story 1.1)

```python
# obdb/agent/state.py
from pydantic import BaseModel

class OBDBRecord(BaseModel, frozen=True):
    id: str
    name: str
    brewery_type: str | None
    address_1: str | None
    city: str | None
    state_province: str | None
    postal_code: str | None
    country: str | None
    website_url: str | None
    phone: str | None
    longitude: str | None
    latitude: str | None

class StepError(BaseModel, frozen=True):
    step_id: str
    message: str
    source: str | None = None
```

`StepError` is defined here so later steps can import it from one place.

### HTTP Client

Use `httpx` (sync `httpx.get` is fine for v0.1, no async needed). Add a 10-second timeout. On `httpx.HTTPStatusError` or `httpx.RequestError`, surface as `StepError` — do not let exceptions propagate to the caller unhandled.

### Testing Approach

- **Default (snapshot):** Mock HTTP responses using `pytest-httpx` (or `respx`) with pre-recorded JSON fixtures — no live HTTP in the default test run.
- **Live flag:** Guard any live-API call behind `@pytest.mark.live` or `--live` flag.
- Keep fixture JSON files small (2–3 brewery objects max).
- Follow project TDD rule: write failing test first, then implement.

### Project Setup (greenfield — no pyproject.toml yet)

Create a minimal `pyproject.toml`:
```toml
[project]
name = "openbrewerydb-research-agent"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["httpx>=0.27", "pydantic>=2.7"]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-httpx>=0.30", "ruff>=0.4"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I"]
```

Run `uv sync --extra dev` after creating this file.

### Lint / Format

`uv run ruff check obdb/ && uv run ruff format --check obdb/` must pass before commit.

### References

- Architecture AD-1, AD-2, AD-3: [Source: `ARCHITECTURE-SPINE.md`]
- FR-1, FR-15: [Source: `prd.md`]
- OBDB API: `https://api.openbrewerydb.org/v1/breweries/search`
- Structural seed: architecture spine `## Structural Seed`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

- `_location_matches` initially used substring `in` check; "co" (Colorado) matched "francisc**o**" in "San Francisco". Fixed to word-boundary set intersection.

### Completion Notes List

- All 5 tests pass (happy path, not-found, location-mismatch, 5xx StepError, Protocol compliance).
- `OBDBPort` is `runtime_checkable`; `isinstance(adapter, OBDBPort)` verified.
- Bulk-cache path deliberately excluded per AD-3.
- `_location_matches` uses word-set intersection — handles multi-word city names and abbreviations via city word overlap; state abbreviations (CA, CO) match when city name provides the match.

### File List

- `pyproject.toml` (new)
- `obdb/__init__.py` (new)
- `obdb/agent/__init__.py` (new)
- `obdb/agent/state.py` (new)
- `obdb/ports/__init__.py` (new)
- `obdb/ports/obdb_port.py` (new)
- `obdb/adapters/__init__.py` (new)
- `obdb/adapters/obdb_api_adapter.py` (new)
- `obdb/tests/__init__.py` (new)
- `obdb/tests/test_obdb_adapter.py` (new)
- `obdb/tests/fixtures/obdb_search_hit.json` (new)
- `obdb/tests/fixtures/obdb_search_empty.json` (new)
- `uv.lock` (new)

### Review Findings

- [x] [Review][Patch] `exc.request.url` AttributeError in `RequestError` handler — `httpx.RequestError` does not guarantee `.request` is set; `str(exc.request.url)` raises `AttributeError` for connection-level errors before a request is built. [obdb/adapters/obdb_api_adapter.py:50-52]
- [x] [Review][Patch] `resp.json()` JSONDecodeError not caught — a 2xx response with a non-JSON body (e.g. CDN maintenance page) raises `json.JSONDecodeError` uncaught, escaping the `StepError` contract. [obdb/adapters/obdb_api_adapter.py:55]
- [x] [Review][Patch] `_to_record` raises bare `KeyError` if `id`/`name` absent in API response — malformed records from the API propagate an uncaught `KeyError` through `lookup_one`. [obdb/adapters/obdb_api_adapter.py:18-19]
- [x] [Review][Patch] Non-list JSON response iterates dict keys — if `resp.json()` returns a dict, `for raw in results` iterates string keys, not records; produces corrupt `OBDBRecord` or `KeyError`. [obdb/adapters/obdb_api_adapter.py:55]
- [x] [Review][Patch] Empty/whitespace-only `location` silently returns `None` for all results — `tokens` is empty set; every brewery is silently dropped. [obdb/adapters/obdb_api_adapter.py:10-14]
- [x] [Review][Defer] `per_page=5` silently misses valid match ranked >5 — pre-existing architectural choice; acceptable for v0.1 but will cause silent false-not-found for common brewery names — deferred, pre-existing
- [x] [Review][Defer] `_location_matches` word-overlap false positives on short tokens (e.g. "il" in "Illinois" vs. substring "il") — acceptable heuristic per dev agent log; deferred, pre-existing
- [x] [Review][Defer] `longitude`/`latitude` typed `str | None` — API returns strings; coercion to `float` deferred to consumer need — deferred, pre-existing
