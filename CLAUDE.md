# Niche AEC AI Platform

An internal platform that removes duplicated manual work between **architectural PDF → Revit → SAFI → optimization → Revit**, while engineers keep final engineering authority.

**Owner:** Sultan (software integration specialist; not a structural engineer).
**Current phase:** 0, Discovery / POC. See the imported state below.

@docs/state.md

## Project files (read on demand, don't import)

- `docs/plan.md`: the core plan. **Never change it without Sultan's explicit approval.**
- `docs/CLAUDE_INSTRUCTIONS.md`: full working rules. Read it before architecture, review, or planning work.
- `docs/decisions.md`: decision log (D-001 onward). Read it before revisiting a past decision.
- `docs/evidence/`: facts collected: SAFI support replies, test protocols, test results.
- `.claude/rules/coding.md`: coding guidelines. Loads automatically when working on code.
- `tools/ifc_inspect/`: IFC inspector. Setup: `pip install -r tools/ifc_inspect/requirements.txt`. Tests: `cd tools/ifc_inspect && python make_fixtures.py && python -m pytest -q`.
- `data/`: real project files (IFC, RVT). **Git-ignored and confidential.**

## Rules that always apply

1. **Evidence labels:** tag claims as FACT (with source), HYPOTHESIS, DECISION, or RECOMMENDATION. Never present a hypothesis as fact. Never invent metrics; use TBD.
2. **Structural engineering:** use domain knowledge to form hypotheses, then have the drafter or engineer confirm them before building on them.
3. **Confidence ≠ authority:** no change to a Revit or SAFI model without a human-confirmed mapping, engineer approval, and a valid Change Contract. Only section/type swaps are eligible. The engineer has final authority.
4. **Deterministic first:** no ML matching and no multi-agent systems until a measured need exists. An LLM never decides element identity, sizing, adequacy, or approvals.
5. **Keep it simple:** one modular backend, PostgreSQL, object storage. No microservices, PostGIS, event buses, or web portal without a decision gate.
6. **Confidential data:** never send files from `data/`, or client or company models, to external services or APIs. Share derived reports only with Sultan's OK. Never commit `data/`.
7. **Plan conflicts:** if evidence conflicts with `docs/plan.md`, stop and propose the change (format in `docs/CLAUDE_INSTRUCTIONS.md` §23).
8. **If something is unclear, ask first.** Keep answers concise but understandable.

## Handoff

- When Sultan sends **"wrap up"** or **"change"** as a standalone command, run the `/wrap-up` skill. A request that merely contains the word ("change the beam size") is not a trigger.
- After milestones (a decision approved, new evidence, a phase or gate change, a meaningful piece of work finished), update `docs/state.md` without being asked.

## Environment

- Windows work laptop with Revit and SAFI. Python 3.11+.
- Revit and SAFI run only on Windows. IFC files are the exchange format, since SAFI has no API (FACT: SAFI support email).
