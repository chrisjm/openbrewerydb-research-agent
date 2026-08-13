---
id: SPEC-openbrewerydb-research-agent
companions:
  - glossary.md
  - ../../planning-artifacts/architecture/architecture-openbrewerydb-research-agent-2026-08-06/ARCHITECTURE-SPINE.md
sources:
  - ../../planning-artifacts/prds/prd-openbrewerydb-research-agent-2026-08-06/prd.md
  - ../../planning-artifacts/prds/prd-openbrewerydb-research-agent-2026-08-06/addendum.md
---

# OBDB Research Agent v0.1

## Why

OBDB contributors need a faster way to verify brewery record corrections without losing provenance or shipping low-confidence changes. v0.1 targets an internal CLI workflow that reduces manual tab-hopping, keeps a human review gate, and produces evidence-backed diffs that maintainers can trust.

## Capabilities

- **CAP-1**
  - **intent:** The system can gather OBDB, state-license, and brewery-website signals for one brewery run.
  - **success:** A run returns typed evidence for the requested brewery or a structured step error, with no multi-brewery batching.

- **CAP-2**
  - **intent:** The system can score confidence from multi-signal evidence and apply a threshold gate.
  - **success:** Equivalent inputs produce the same score, and below-threshold runs suppress copyable output.

- **CAP-3**
  - **intent:** The system can produce typed field diffs with evidence refs and render copyable CSV only when the gate passes.
  - **success:** Passing runs emit valid CSV; failing runs emit evidence-only output with source URLs and snippets.

- **CAP-4**
  - **intent:** The system can run an ordered in-process pipeline with immutable run state and error continuity.
  - **success:** Each step returns a new state snapshot, and failures still reach the render stage with explicit step context.

- **CAP-5**
  - **intent:** The system can source runtime lookup from the OBDB API while bulk cache refresh uses OBDB GitHub snapshots.
  - **success:** Single-brewery lookup never depends on the bulk cache path, and cache refresh never fans out record-by-record at runtime.

## Constraints

- v0.1 runs as a local CLI with local disk cache only.
- v0.1 uses public no-auth data endpoints only.
- No LLM-dependent extraction in the critical path.
- No automated GitHub PR creation in v0.1.
- One brewery per run, with a fixed deterministic step order.

## Non-goals

- Browser-integrated OBDB button flow.
- Fully automated data application with no human review.
- Additional state adapters beyond CA/CO/TX in v0.1.
- HTML research report generation in v0.1.

## Success signal

A contributor can verify one suspect brewery in a single CLI run and get either a copyable CSV diff or evidence-only output in under the v0.1 confidence gate. Low-confidence cases stay non-copyable, and the output still carries enough provenance for a maintainer to review quickly.
