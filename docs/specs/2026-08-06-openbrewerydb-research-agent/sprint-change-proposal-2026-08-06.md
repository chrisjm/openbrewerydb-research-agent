# Sprint Change Proposal — 2026-08-06

## 1. Issue Summary

During Story 1.3 planning, we identified a gap: HTTP-only website checks are insufficient for real-world brewery websites that are JS-rendered or bot-gated. We also need explicit ethical scraping controls early, not as an afterthought:

- Policy-aware behavior via `robots.txt`
- Transparent scraper identity via env-configured request header
- Structured blocked/error outcomes instead of false `active` classifications

Trigger source: Story 1.3 readiness review + deferred-work findings from Story 1.2b/1.3.

## 2. Impact Analysis

### Epic Impact

- **Epic 1 affected**: add a dedicated scope slice for policy-aware and JS-capable website access.
- Added new story: `1.3b-add-policy-aware-and-js-capable-website-access` (status `backlog`).
- Story 1.4 sequencing remains valid and now consumes a clearer website-access contract.

### Story Impact

- `1-3-check-brewery-website-status-in-the-run`: remains focused on typed website status + closure signals.
- `1-3b-add-policy-aware-and-js-capable-website-access`: new story to add ethical crawl policy checks, env identity header requirement, and JS-capable adapter path.
- `1-4-preserve-ordered-execution-and-partial-evidence-on-failure`: no rewrite needed; inherits improved website-step behavior.

### Artifact Conflicts and Resolutions

- **PRD conflict**: FR-4 implied HTTP-only path; now updated to adapter-based path with policy/identity constraints.
- **Architecture conflict**: no explicit policy/identity invariant; now added as AD-8.
- **UX impact**: N/A (no UI artifact exists).

### Technical Impact

- Requires website-port-consistent design for multiple adapter implementations.
- Adds config/env requirement for scraper identity header.
- Adds policy gate behavior (`robots.txt`) and explicit policy-blocked error handling.

## 3. Recommended Approach

**Selected path: Option 1 (Direct Adjustment)**

- Effort: **Medium**
- Risk: **Medium**
- Timeline impact: **Low-to-medium** (new story inserted, no rollback)

Rationale:

1. Avoids destabilizing current in-progress work.
2. Preserves MVP while making ethical + resilient website handling explicit.
3. Keeps architecture clean by extending existing port/adapter model.

Rollback was rejected as unnecessary. MVP reduction was rejected because this is core evidence quality and ethics behavior, not optional polish.

## 4. Detailed Change Proposals

### 4.1 PRD Update (Approved)

Artifact: `prd.md`
Section: `FR-4: Website status check`

OLD:
- HTTP status and closure-keyword scan
- single-attempt explicit errors

NEW:
- pluggable website adapters (HTTP-first, browser-capable path)
- `robots.txt` policy-aware checks for crawl behavior
- env-configured scraper identity header requirement
- retain single-attempt explicit-error v0.1 behavior

### 4.2 Epic/Story Plan Update (Approved)

Artifact: `epics.md`
Section: Epic 1 story list

OLD:
- 1.3 website check
- 1.4 ordered execution

NEW:
- Keep 1.3
- Add 1.3b policy-aware + JS-capable website access
- Keep 1.4 after 1.3b

### 4.3 Architecture Update (Approved)

Artifact: `architecture/architecture-openbrewerydb-research-agent-2026-08-06/ARCHITECTURE-SPINE.md`
Section: Invariants and conventions

OLD:
- No dedicated website policy/identity architecture invariant

NEW:
- AD-8: policy-aware website access behind a single website port
- require `robots.txt` policy checks for crawl behavior
- require env-configured scraper identity headers
- require structured policy/technical blocked errors

### 4.4 Sprint Status Update (Approved)

Artifact: `sprint-status.yaml`

NEW:
- Added `1-3b-add-policy-aware-and-js-capable-website-access: backlog`
- Updated `last_updated` timestamp

## 5. Implementation Handoff

### Scope Classification

**Moderate** — backlog reorganization plus implementation coordination.

### Handoff Recipients and Responsibilities

- **Product Owner / Planner flow**
  - Create story file for `1-3b-add-policy-aware-and-js-capable-website-access`.
  - Ensure acceptance criteria include robots-policy checks and env header behavior.

- **Developer flow**
  - Implement Story 1.3 and 1.3b with shared `WebsitePort` contract.
  - Add deterministic tests for policy blocked, technical blocked, and JS-capable path behavior.
  - Enforce deterministic adapter selection (HTTP first, optional one browser fallback on technical block only) and validate structured blocked codes (`policy_blocked`, `technical_blocked`, `config_error`) while preserving render-stage continuation.

- **Architecture stewardship**
  - Keep AD-8 enforced during code review; avoid adapter-specific orchestrator branching.

### Success Criteria

1. Website step never silently classifies policy/technical blocked sites as `active`.
2. Crawl-capable behavior consults `robots.txt` before crawling.
3. Requests carry env-configured scraper identity header.
4. HTTP-only and JS-capable adapters remain interchangeable under one port.

## Checklist Execution Status

- 1. Understand Trigger and Context: **[x] Done**
- 2. Epic Impact Assessment: **[x] Done**
- 3. Artifact Conflict and Impact Analysis: **[x] Done**
- 4. Path Forward Evaluation: **[x] Done** (Option 1 selected)
- 5. Sprint Change Proposal Components: **[x] Done**
- 6. Final Review and Handoff prep: **[x] Done** (pending explicit user final approval)
