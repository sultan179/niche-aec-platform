# Niche AEC Project State

**Updated:** 2026-09-16
**Core plan:** `docs/plan.md` v0.1 (DRAFT, awaiting approval)

---

## Phase and objective

- **Current phase:** 0, Discovery / POC
- **Current objective:** answer the IFC/GlobalId question and prove the real Revit → SAFI data path on one representative project.

---

## Known facts

These were reported by the drafter in the initial interview:

- The architectural PDF is modeled in Revit and then rebuilt in SAFI.
- SAFI results are applied to Revit by hand and checked by print-and-tick.
- Revit and SAFI IDs differ.
- Coordinates are close but not identical.
- Gridlines match in both programs.

From SAFI's published materials (source: safi.com):

- SAFI can import IFC.
- SAFI 3D exports DXF, SDNF, and KISS formats.
- Reports can be saved as Excel, Access, or ASCII.
- No public API is documented.

New on 2026-09-16:

- **FACT:** SAFI has no API (confirmed by email from SAFI support).
- **SAFI can export IFC** (reported by Sultan; source to confirm).
- An IFC test tool (`ifc_inspect.py`) and a test protocol are ready. The tool is tested on synthetic files only.
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, entries D-001 to D-012.

---

## Open questions

- Material and SAFI module
- What changes after analysis
- Whether and how the analytical model is used
- Worksharing and Revit version
- Units and coordinate conventions
- Who approves structural changes
- SAFI IFC export: schema version, physical or analytical entities, profiles and materials, GlobalId stability, whether Revit GlobalIds survive the round trip
- Whether IFC carries analysis results, or those come from Excel/Access reports instead
- Manual rebuild time (baseline)

---

## Active risks

- SAFI exposes too little structured data.
- The IFC import loses analytical intent, or nodes don't connect.
- GlobalIds are not kept.
- The physical → analytical transformation is more complex than assumed.
- Revit's analytical model doesn't match SAFI's.
- There isn't enough project data for labeling.

---

## Evidence collected

- `docs/evidence/safi-integration.md`: no API (confirmed by SAFI support); IFC export reported (2026-09-16).
- `docs/evidence/ifc-test-protocol.md`: test plan, not run yet.

---

## Next decision gate

**G0:** IFC/GlobalId verdict (full / partial / fail) and a proven data path.

---

## Project setup (2026-09-16)

- The project is now a git repo for Claude Code (`niche-aec-platform`), and the repo is the source of truth for the docs. Root `CLAUDE.md`, `docs/`, `.claude/rules/coding.md`, the `/wrap-up` skill, and `tools/ifc_inspect/` are in place.
- Handoff keywords: **"wrap up"** / **"change"** (as standalone commands), plus automatic updates at milestones.

---

## Next actions

1. Sultan approves `plan.md` v0.1, and decides on the proposed IFC-based POC.
2. With the drafter, agree on pass/fail criteria, then run `docs/evidence/ifc-test-protocol.md` on one project.
3. Run `ifc_inspect.py` on the exports, and record results in `docs/evidence/ifc-test-results.md`.
4. Ask SAFI support about IFC export details: schema, analytical entities, and whether GlobalIds are kept.
5. Decide G0 (full / partial / fail).
6. Build a read-only diff prototype on one project.
