---
baseline_commit: be67ca29fb1802ca571fc47d793b489e0b9b12e7
---

# Story 1.2b: Capture Real License Source Snapshots and Validate Normalization Contract

Status: review

## Story

As a contributor,
I want each state license adapter to fetch from a real source, save a raw snapshot, and parse it into `StateLicenseRecord` objects,
so that the normalization contract is proven against actual data shapes before the orchestrator wires everything together.

## Acceptance Criteria

1. **Given** a live network connection **When** `fetch_bulk(live=True)` is called on any of the three adapters **Then** it hits the real source URL, saves the raw response to the fixture path, and returns parsed `StateLicenseRecord` items.
2. **Given** a previously saved snapshot **When** `fetch_bulk()` is called (default, no live flag) **Then** it reads the snapshot from disk and returns parsed `StateLicenseRecord` items — no network call.
3. **Given** the three real snapshots **When** each is parsed **Then** every record maps to a valid `StateLicenseRecord` (all required fields present, no unhandled exceptions).
4. **Given** a source that requires authentication or blocks automated access **When** the live fetch is attempted **Then** the adapter surfaces a `StepError` with a clear message identifying the blocker — it does not crash or silently return empty results.
5. **Given** the completed spike **When** the story is closed **Then** a source-map note exists in Dev Agent Record documenting: each state's real URL, response format (HTML/CSV/JSON/other), auth requirements if any, and any quirks discovered.

## Tasks / Subtasks

- [x] Research and document real source URLs for CA, CO, TX license lookups (AC: 5)
  - [x] Identify the public-facing search or bulk-download URL for each state
  - [x] Note format (HTML table / CSV / JSON / PDF / other) and any auth/CAPTCHA requirements
  - [x] Record findings in Dev Agent Record → Source Map before writing any code
- [x] Add `live=False` parameter to `fetch_bulk` on all three adapters; wire live HTTP path (AC: 1, 2)
  - [x] `live=True` fetches from real URL via `httpx`, saves raw bytes to fixture path, then parses
  - [x] `live=False` (default) reads existing fixture from disk — existing behavior preserved
  - [x] If source requires auth or returns non-200, surface `StepError` (AC: 4)
- [x] Update `_to_record` parsers to match real response shape for each adapter (AC: 3)
  - [x] CA: implement parser for actual CA ABC response format
  - [x] CO: implement parser for actual CO SBG response format
  - [x] TX: implement parser for actual TX TABC response format
- [x] Replace synthetic fixture files with real captured snapshots (AC: 2, 3)
  - [x] Run `fetch_bulk(live=True)` for each adapter, commit resulting fixture files
  - [x] Fixtures must contain at least 2 real records each (or document why fewer exist)
- [x] Update `obdb/tests/test_state_license_adapters.py` to cover live-flag behaviour (AC: 1, 2, 4)
  - [x] Default (offline) path: existing snapshot tests continue to pass
  - [x] Auth/block error path: monkeypatched non-200 surfaces `StepError`
- [x] All 32 existing tests pass after changes; ruff clean (AC: 3)

## Dev Notes

### Architecture Constraints (carry forward from 1.2)

- **AD-1:** Adapters implement `StateLicensePort`. `live` is an implementation detail — the port signature stays `fetch_bulk(self) -> list[StateLicenseRecord] | StepError`. The `live` parameter is on the concrete class only.
- **AD-2:** `StateLicenseRecord` remains `frozen=True`. Parser output must map cleanly to the model fields.
- **AD-4:** All three adapters normalize to the same shape regardless of source format (HTML/CSV/JSON). That is the whole point of this story.

### Live Fetch Pattern

```python
def fetch_bulk(self, *, live: bool = False) -> list[StateLicenseRecord] | StepError:
    if live:
        try:
            resp = httpx.get(self._source_url, timeout=15.0)
            resp.raise_for_status()
            _FIXTURE.write_bytes(resp.content)
        except Exception as exc:
            return StepError(step_id=self._step_id, message=str(exc), source=self._source_url)
    # fall through to existing disk-read + parse path
    try:
        raw = _FIXTURE.read_bytes()
        return self._parse(raw)
    except Exception as exc:
        return StepError(step_id=self._step_id, message=str(exc), source=str(_FIXTURE))
```

Refactor each adapter to extract `_parse(raw: bytes) -> list[StateLicenseRecord]` so the format-specific logic is isolated and testable independently.

### Parser Abstraction Guidance

- If CA/CO/TX all return HTML: extract a shared `parse_html_table(raw, field_map)` utility in `obdb/adapters/_html_parser.py`.
- If formats differ: keep parsers inline per adapter for now. Document the format in the Source Map. A shared abstraction layer is deferred to a follow-on story once we know what we're abstracting.
- Do NOT prematurely build a generic parser framework. Let the real data shapes decide.

### Source Map (fill in during Task 1)

| State | URL | Format | Auth required | Quirks |
|-------|-----|--------|--------------|--------|
| CA | TBD | TBD | TBD | TBD |
| CO | TBD | TBD | TBD | TBD |
| TX | TBD | TBD | TBD | TBD |

### Blocker Handling

If any source requires authentication, a session cookie, or a CAPTCHA that cannot be automated:
- Surface `StepError(step_id="<state>_license_lookup", message="Source requires auth: <detail>", source=<url>)`
- Document in Source Map
- Do NOT block the story — complete the other states and note the blocked state as a known limitation
- File a deferred-work note for the blocked state

### Dependencies

- `httpx` already in runtime deps (from story 1.1)
- HTML parsing: use stdlib `html.parser` if needed — do NOT add `beautifulsoup4` unless HTML is genuinely too complex to parse without it, and get approval first
- CSV parsing: use stdlib `csv` module

### TDD Order

1. Document Source Map (no code).
2. Add failing test for `fetch_bulk(live=True)` with mocked `httpx` response.
3. Implement live fetch path → green.
4. Update `_to_record` / `_parse` for real shapes.
5. Run live fetch, commit real snapshots.
6. Confirm all tests pass against real snapshots.

### References

- Story 1.2: established `StateLicensePort`, `StateLicenseRecord`, adapter shape
- Architecture AD-1, AD-2, AD-4
- Deferred-work tracker: `deferred-work.md`

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Source Map

*(Completed during Task 1)*

| State | URL | Format | Auth required | Quirks |
|-------|-----|--------|--------------|--------|
| CA | `https://www.abc.ca.gov/licensing/licensing-reports/` | JavaScript/AJAX-rendered HTML | **BLOCKED** — session nonces required | No bulk download; data is dynamically rendered via WP plugin with expiring nonces. `live=True` always returns `StepError`. Synthetic fixture retained. See deferred-work.md. |
| CO | `https://data.colorado.gov/resource/ier5-5ms2.csv` | Socrata CSV API | None | Filter: `license_type LIKE '%Manufacturer (brewery)%'`. Returns `licensee_name`, `doing_business_as`, `license_number`, `license_type`, `expiration`, `street_address`, `city`, `state`, `zip`. Clean, no auth, no pagination needed for ≤200 records. |
| TX | `https://data.texas.gov/resource/7hf9-qc9f.csv` | Socrata CSV API | None | Brewer's License type = `BW`. Filter: `license_type='BW' AND primary_status='Active'`. Fields: `license_id` (has trailing `.0`), `trade_name`, `owner`, `city`, `address`, `state`, `license_status`. Numeric IDs must have `.0` stripped. |

### Completion Notes List

- CO and TX replaced synthetic JSON fixtures with real Socrata CSV snapshots (10 records each, captured 2026-08-06).
- CA remains synthetic JSON fixture — live source is blocked (JS/AJAX nonces); `live=True` returns `StepError` with clear message. Deferred to future story.
- All adapters restructured: `_parse(raw: bytes)` extracts format-specific logic; `fetch_bulk(*, live=False)` handles live/fixture branching.
- CO and TX parse CSV via stdlib `csv.DictReader`. CA parses JSON. No new dependencies added.
- TX `license_id` field has trailing `.0` (Socrata numeric export artifact) — stripped in parser.
- `fetched_at` generated at parse time (`datetime.now(UTC).isoformat()`); not stored in fixture.
- 37 tests pass (5 pre-existing OBDB adapter + 32 state license adapter tests). Ruff clean.
- CA blocker documented in `deferred-work.md`.

### File List

- `obdb/adapters/ca_license_adapter.py` (modified — live blocker, `_parse` refactor)
- `obdb/adapters/co_license_adapter.py` (modified — CSV parsing, live HTTP, `_parse`)
- `obdb/adapters/tx_license_adapter.py` (modified — CSV parsing, live HTTP, `_parse`)
- `obdb/tests/test_state_license_adapters.py` (modified — updated hit tests, live-fetch tests)
- `obdb/tests/fixtures/co_license_hit.csv` (new — real Socrata snapshot, replaces JSON)
- `obdb/tests/fixtures/tx_license_hit.csv` (new — real Socrata snapshot, replaces JSON)
- `obdb/tests/fixtures/co_license_hit.json` (deleted)
- `obdb/tests/fixtures/tx_license_hit.json` (deleted)

## Change Log

## Change Log

- 2026-08-06: Story 1.2b implemented — real CO/TX Socrata CSV snapshots, live HTTP path, CA live blocker documented, 37 tests pass (claude-sonnet-4.6)
