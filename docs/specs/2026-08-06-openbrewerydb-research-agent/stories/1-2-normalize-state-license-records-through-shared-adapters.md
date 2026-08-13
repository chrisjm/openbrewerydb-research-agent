---
baseline_commit: bc86927
---

# Story 1.2: Normalize State-License Records Through Shared Adapters

Status: review

## Story

As a contributor,
I want CA, CO, and TX license sources to return the same normalized shape,
so that the run can compare state evidence without special-case code per state.

## Acceptance Criteria

1. **Given** a CA, CO, or TX source fixture **When** the adapter fetches records **Then** it returns normalized `StateLicenseRecord` items through the shared `StateLicensePort` contract.
2. **Given** each of the three adapters **When** inspected at runtime **Then** each exposes the same `state_code` attribute and `lookup_one` / `fetch_bulk` methods (i.e. each is a valid `StateLicensePort`).
3. **Given** a parser failure (malformed or missing fixture data) **When** any adapter encounters it **Then** it surfaces a `StepError` and does not raise an unhandled exception.

## Tasks / Subtasks

- [x] Define `StateLicenseRecord` frozen Pydantic model in `obdb/agent/state.py` (AC: 1, 2)
  - [x] Fields: `id: str`, `name: str`, `license_status: str | None`, `address: str | None`, `city: str | None`, `state_code: str`, `source_url: str`, `fetched_at: str`
- [x] Define `StateLicensePort` protocol in `obdb/ports/state_license_port.py` (AC: 2)
  - [x] `state_code: str` class attribute
  - [x] `lookup_one(name: str, city: str) -> list[StateLicenseRecord] | StepError`
  - [x] `fetch_bulk() -> list[StateLicenseRecord] | StepError`
  - [x] Mark `@runtime_checkable`
- [x] Add snapshot fixtures for CA, CO, TX (1-2 records each) under `obdb/tests/fixtures/` (AC: 1, 3)
  - [x] `ca_license_hit.json`, `co_license_hit.json`, `tx_license_hit.json`
- [x] Implement `CALicenseAdapter` in `obdb/adapters/ca_license_adapter.py` (AC: 1, 2, 3)
  - [x] `state_code = "CA"`
  - [x] `lookup_one` filters bulk records by name/city
  - [x] `fetch_bulk` returns all fixture records (v0.1: static fixture; live HTTP gated behind `--live`)
  - [x] Parser/key errors → `StepError(step_id="ca_license_lookup", ...)`
- [x] Implement `COLicenseAdapter` in `obdb/adapters/co_license_adapter.py` (AC: 1, 2, 3)
  - [x] `state_code = "CO"`
  - [x] Same contract as CA adapter
  - [x] Parser/key errors → `StepError(step_id="co_license_lookup", ...)`
- [x] Implement `TXLicenseAdapter` in `obdb/adapters/tx_license_adapter.py` (AC: 1, 2, 3)
  - [x] `state_code = "TX"`
  - [x] Same contract as CA adapter
  - [x] Parser/key errors → `StepError(step_id="tx_license_lookup", ...)`
- [x] Write snapshot fixture tests in `obdb/tests/test_state_license_adapters.py` (AC: 1, 2, 3)
  - [x] Happy path per adapter: known fixture returns `list[StateLicenseRecord]`
  - [x] `lookup_one` name/city filter: mismatch returns empty list
  - [x] Error path: malformed record returns `StepError`
  - [x] Protocol compliance: `isinstance(adapter, StateLicensePort)` is `True` for each

## Dev Notes

### Architecture Constraints (must follow — AD-1, AD-2, AD-4)

- **AD-1 (Hexagonal boundary):** Each adapter implements `StateLicensePort`. Future orchestrator (Story 1.4) calls the port, not adapters directly. Tests instantiate adapters directly.
- **AD-2 (Immutable state):** `StateLicenseRecord` must be `frozen=True`. No attribute mutation after construction; use `model_copy(update=...)` if derivation is needed downstream.
- **AD-4 (Unified state-adapter port contract):** All three adapters share one protocol. Contract includes `state_code`, `lookup_one`, and `fetch_bulk`. No per-state branching in the orchestrator is the explicit goal.

### Model to Add to `obdb/agent/state.py`

```python
class StateLicenseRecord(BaseModel, frozen=True):
    id: str                      # source-local license/record id
    name: str                    # brewery name as it appears in source
    license_status: str | None = None   # e.g. "active", "inactive", "cancelled"
    address: str | None = None
    city: str | None = None
    state_code: str              # "CA" | "CO" | "TX"
    source_url: str              # authoritative URL the record came from
    fetched_at: str              # ISO-8601 UTC timestamp string
```

Append to the existing `state.py` — do not duplicate `OBDBRecord` or `StepError`.

### Port Contract

```python
# obdb/ports/state_license_port.py
from typing import Protocol, runtime_checkable
from obdb.agent.state import StateLicenseRecord, StepError

@runtime_checkable
class StateLicensePort(Protocol):
    state_code: str
    def lookup_one(self, name: str, city: str) -> list[StateLicenseRecord] | StepError: ...
    def fetch_bulk(self) -> list[StateLicenseRecord] | StepError: ...
```

### Adapter Shape (CA example; CO and TX are structurally identical)

```python
# obdb/adapters/ca_license_adapter.py
import json as _json
from pathlib import Path
from obdb.agent.state import StateLicenseRecord, StepError

_FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "ca_license_hit.json"

class CALicenseAdapter:
    """CA ABC license adapter — v0.1 uses static fixture; live HTTP deferred."""
    state_code = "CA"

    def fetch_bulk(self) -> list[StateLicenseRecord] | StepError:
        try:
            raw_list = _json.loads(_FIXTURE.read_text())
            return [_to_record(r) for r in raw_list]
        except Exception as exc:
            return StepError(step_id="ca_license_lookup", message=str(exc))

    def lookup_one(self, name: str, city: str) -> list[StateLicenseRecord] | StepError:
        result = self.fetch_bulk()
        if isinstance(result, StepError):
            return result
        name_l, city_l = name.lower(), city.lower()
        return [r for r in result if name_l in r.name.lower() and city_l in (r.city or "").lower()]
```

`_to_record` maps fixture dict → `StateLicenseRecord`; wraps `KeyError` → `StepError`.

### Fixture JSON Shape (1–2 records, enough to cover happy + mismatch path)

```json
[
  {
    "id": "CA-12345",
    "name": "Anchor Brewing Company",
    "license_status": "active",
    "address": "1705 Mariposa St",
    "city": "San Francisco",
    "state_code": "CA",
    "source_url": "https://www.abc.ca.gov/",
    "fetched_at": "2026-08-06T00:00:00Z"
  }
]
```

Same shape for CO (`source_url`: `https://sbg.colorado.gov/`) and TX (`source_url`: `https://www.tabc.texas.gov/`).

### v0.1 Fixture Approach

- Adapters load from disk fixture in `fetch_bulk`. **No live HTTP in default test run.**
- Live HTTP is explicitly out of scope for v0.1 — the source parsing shape (JSON vs HTML) for each state's actual API is unknown and should not be reverse-engineered now. The fixture defines the normalized contract; real source parsing is a v0.2 concern.
- Do NOT add `httpx` calls to these adapters. `pytest-httpx` is not needed for this story.

### Error Handling Consistency (learned from Story 1.1)

Follow the same patterns already established in `obdb_api_adapter.py`:
- Wrap all `KeyError`, `json.JSONDecodeError`, `OSError` (file read) in `StepError`.
- Never let exceptions propagate out of `lookup_one` or `fetch_bulk`.
- `StepError.source` can be the fixture path as a string when relevant.

### Naming Conventions (from architecture spine)

- Adapters: `<source>_adapter.py` → `ca_license_adapter.py`, `co_license_adapter.py`, `tx_license_adapter.py`
- Port: `state_license_port.py`
- `step_id` strings: `"ca_license_lookup"`, `"co_license_lookup"`, `"tx_license_lookup"`

### Existing Files Being Extended

| File | Change |
|------|--------|
| `obdb/agent/state.py` | Append `StateLicenseRecord` class — do not modify existing classes |
| `obdb/ports/` | New file `state_license_port.py` |
| `obdb/adapters/` | Three new files |
| `obdb/tests/test_state_license_adapters.py` | New test file |
| `obdb/tests/fixtures/` | Three new JSON fixture files |

### TDD Order

1. Write `StateLicenseRecord` model + `StateLicensePort` protocol.
2. Write failing tests (`test_state_license_adapters.py`) that import adapters that don't exist yet.
3. Implement CA adapter → green.
4. Implement CO adapter → green.
5. Implement TX adapter → green.
6. Confirm all 5 existing tests still pass (no regressions).

### References

- Architecture AD-1, AD-2, AD-4: [Source: `ARCHITECTURE-SPINE.md`]
- FR-2, FR-3: [Source: `prd.md`]
- Structural seed file layout: architecture spine `## Structural Seed`
- Story 1.1 patterns (error handling, frozen models, pytest-httpx): [Source: `1-1-fetch-the-target-obdb-record.md`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

- All three adapters (CA, CO, TX) implemented with identical `StateLicensePort` contract.
- `StateLicenseRecord` frozen Pydantic model appended to `obdb/agent/state.py` (no existing classes modified).
- `StateLicensePort` `@runtime_checkable` Protocol added to `obdb/ports/state_license_port.py`.
- 24 new tests covering: protocol compliance, happy-path `fetch_bulk`, `lookup_one` hit/miss, malformed fixture → `StepError`, missing file → `StepError`, `lookup_one` propagates `StepError`.
- All 29 tests pass (5 pre-existing + 24 new). Ruff clean.
- v0.1: static fixture only; no `httpx` calls; live HTTP deferred to v0.2.

### File List

- `obdb/agent/state.py` (modified — appended `StateLicenseRecord`)
- `obdb/ports/state_license_port.py` (new)
- `obdb/adapters/ca_license_adapter.py` (new)
- `obdb/adapters/co_license_adapter.py` (new)
- `obdb/adapters/tx_license_adapter.py` (new)
- `obdb/tests/test_state_license_adapters.py` (new)
- `obdb/tests/fixtures/ca_license_hit.json` (new)
- `obdb/tests/fixtures/co_license_hit.json` (new)
- `obdb/tests/fixtures/tx_license_hit.json` (new)
- `sprint-status.yaml` (modified — status: review)

## Change Log

- 2026-08-06: Story 1.2 implemented — StateLicenseRecord model, StateLicensePort protocol, CA/CO/TX adapters, 3 fixtures, 24 tests (claude-sonnet-4.6)
