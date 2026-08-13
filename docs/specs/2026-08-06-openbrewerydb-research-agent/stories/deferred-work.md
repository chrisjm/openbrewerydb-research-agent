
## Deferred from: code review of 1-1-fetch-the-target-obdb-record (2026-08-06)

- `per_page=5` silently misses valid match ranked >5 — acceptable for v0.1 but causes silent false-not-found for common brewery names. Fix: add pagination or increase limit when needed.
- `_location_matches` word-overlap false positives on short tokens — heuristic is documented in dev agent log; revisit if location matching causes real false positives in practice.
- `longitude`/`latitude` typed `str | None` — API returns strings; coerce to `float | None` when a downstream consumer needs numeric coordinates.

## Deferred from: story 1-2b-capture-real-license-source-snapshots (2026-08-06)

- **CA ABC live fetch blocked** — `abc.ca.gov` licensing reports are JavaScript/AJAX-rendered with session nonces. Automated bulk fetch requires browser automation (Playwright/Selenium) or a nonce-refresh mechanism. CA adapter currently uses a synthetic fixture and always returns `StepError` on `live=True`. Fix: add headless browser support or find an alternative CA data source (e.g., a CA open data portal dataset if one is published).

## Deferred from: story 1-3-check-brewery-website-status-in-the-run (2026-08-06)

- **JS-heavy website support with crawl policy guardrail** — add a browser-capable website adapter path for JS-rendered pages and anti-bot flows, while keeping `WebsitePort` as the shared contract so HTTP-only and browser-backed implementations are interchangeable. Crawl only when `robots.txt` allows it, and surface explicit `StepError` when blocked by policy or technical controls. Start with per-domain allow/deny decisions and record blocked domains for follow-up tuning.
