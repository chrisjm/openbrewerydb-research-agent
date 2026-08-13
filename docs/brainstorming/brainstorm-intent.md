# OBDB Research Agent — Brainstorm Intent

---

## Problem Statement

Open Brewery DB (OBDB) contributors manually verify and update brewery records through tab-hopping across state licensing sites, brewery websites, and the OBDB dataset. One correction can take 10+ minutes. Stale, incorrect, or missing brewery data erodes dataset quality and community trust. Low-quality PRs from uninformed contributors compound maintainer burden.

---

## Target User — Contributor Cody

An OBDB community contributor who notices a suspect record (wrong address, closed brewery still marked active, missing fields) and wants to produce a well-evidenced, high-confidence correction without manual research. Cody has a GitHub account and is comfortable copy-pasting a CSV diff into a PR or VS Code. Cody is **not** a developer running scripts.

---

## Core Job-to-Be-Done

> "I see something wrong on OBDB → I want it fixed without 10 minutes of manual tab-hopping."

Given a brewery name + location, the agent must: look up the current OBDB record, query authoritative state licensing data, assess confidence in proposed changes, and produce a copyable CSV diff with full evidence provenance — or surface the evidence without a diff if confidence is too low.

---

## v0.1 Pipeline Architecture

```
[Input: brewery name + location]
        ↓
[1] OBDB Lookup          — fetch current record from OBDB API
        ↓
[2] State API Pull       — query state licensing API (CA ABC / CO / TX)
        ↓  (cache full state/city dataset; reuse across runs — bulk-pull once, TTL-gated)
[3] Website HTTP Check   — HTTP status + closure keyword scan only (no LLM extraction)
        ↓
[4] Confidence Ladder    — rules-based scoring across signals; no LLM in v0.1
        ↓
[5] Output Gate
     ├─ Above threshold → copyable CSV diff row + evidence chain
     └─ Below threshold → evidence display only, no copy button
```

**Design constraints:**
- One brewery per agent run; designed for swarming (parallelism via multiple runs, not batching).
- All judgment in v0.1 is **deterministic rules** — no LLM calls in the critical path.
- State API is load-bearing for determinism: without it, extraction requires LLM (not acceptable for v0.1).

---

## MoSCoW Scope — v0.1

### Must Have
- OBDB record lookup
- State licensing API adapters: California (ABC), Colorado, Texas
- Bulk cache + TTL for state/city datasets
- Website HTTP status check + closure keyword scan
- Confidence ladder (rules-based, multi-signal)
- Typed diff engine: compares candidate record to existing OBDB record with per-field confidence scores
- Evidence/provenance chain: every proposed change cites source URL + extracted text snippet
- Output gating: above-threshold → copyable CSV diff; below-threshold → evidence only, no copy button
- Schema SCD2-readiness: handle `brewery_type='closed'` now; accommodate future tag + SCD type 2 schema without a rewrite

### Should Have
- Visible confidence scores in output
- Formal adapter interface (pluggable state API adapters)
- Eval harness with ground-truth cases (doubles as training data for v0.2)

### Could Have
- Google Business Profile as supplementary signal
- Human-readable explanation when evidence is insufficient

### Won't Have (v0.1)
- Web search / shallow or deep research
- LLM field extraction from brewery websites
- HTML research reports
- Automated GitHub PR creation
- EIN enrichment or secondary data APIs
- OBDB site integration ("research" button)

---

## Key Constraints

| Constraint | Detail |
|---|---|
| **Deterministic** | v0.1 pipeline is rules-based end-to-end; LLM extraction deferred to v0.2 |
| **Human-in-the-loop** | Output gate ensures a human reviews before any data is applied; no auto-commit path |
| **Confidence gating** | Below-threshold results surface evidence but suppress the copy button, preventing low-quality PRs |
| **Schema forward-compatibility** | Diff engine must handle current `brewery_type='closed'` convention and not break when OBDB migrates to tag + SCD type 2 |
| **Swarm-safe cache** | Bulk state dataset pulled once per TTL window; individual brewery lookups reuse the cache — makes swarming cheap |

---

## North-Star Vision

A "Research" button on the OBDB brewery page fires this agent and returns a GitHub PR with full evidence within seconds. The v0.1 local CLI should feel like that button in miniature — interface fidelity matters even for a local tool.

**Upside chain:** high-confidence diffs → fewer low-quality PRs → less maintainer burden → faster dataset improvement → community engagement snowballs → premium data tier enabled by enriched records (EIN → water usage, barrels produced, predictive models).

---

## Explicitly Deferred

| Item | Target |
|---|---|
| Shallow + deep web search for field verification and discovery | v0.2 |
| LLM/NER extraction from brewery websites | v0.2 |
| Additional state API adapters beyond CA/CO/TX | v0.2+ |
| HTML research reports | v0.3+ |
| Automated GitHub PR creation | v0.3+ |
| EIN lookup + secondary API enrichment | Roadmap |
| OBDB site "research" button integration | Roadmap |
| ML/LLM extraction trained on eval harness ground-truth | v0.2+ |
