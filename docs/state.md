# Niche AEC Project State

**Updated:** 2026-09-17
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1, MVP-1 (read-only reconciliation report). G0 exit gate passed 2026-09-17.
- **Current objective:** turn the first-pass geometry matcher into a trustworthy Excel reconciliation report (plan.md §7); next real gap is section/material mapping.

---

## Known facts

Drafter interview: PDF modeled in Revit, rebuilt by hand in SAFI, results applied to Revit by hand (print-and-tick). Revit/SAFI IDs differ; coordinates close but not identical; gridlines match.

- **FACT:** SAFI has no API (SAFI support, 2026-09-16). Import/Export menu confirmed IFC-**import-only** (Export SDNF/KISS/AutoCAD; Import IFC/STAAD — no Export IFC).
- **FACT:** real file tested, `data/ifc/Kingsway Apartments - 1 floor test.ifc` (Revit 26.4.10.51, IFC2X3): 95 physical elements (24 beam/23 column/48 `IfcMember`), materials on all, but section profiles only on beams. Zero analytical content in the export.
- **FACT:** Revit's IFC export is GlobalId/Tag-stable on re-export (100%, 95/95). But **SAFI discards Revit's identity on import** — its member Name field shows SAFI's own numbering, not the Tag. ID-based matching is not viable on the SAFI side (D-013, G0 = Fail).
- **FACT:** SAFI import connectivity: 78–83% of members floating/half-connected, barely improves with a larger offset tolerance — likely a real geometry gap, not a tolerance issue. Needs drafter confirmation.
- **FACT:** built a geometry matcher (`tools/ifc_inspect/parse_sdnf.py`, `match.py`, `report.py`). Found the Revit↔SAFI coordinate transform (90° rotation: `SAFI_x=Revit_y, SAFI_y=-Revit_x`, no offset). Matched **47/47 SAFI elements to Revit at sub-millimeter precision.** 48 unmatched Revit elements are all `IfcMember` (missing from this SAFI export — Sultan suspects an export setting, deprioritized).
- **FACT:** all 47 matched pairs flagged "verify section" — Revit uses imperial names (`W18X40`), SAFI uses metric (`W460x60`); same section, different string. Confirms plan §8's requirement for a real SectionMapping subsystem, not string equality.
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, D-001–D-013. Latest: **D-013, G0 = Fail** — matching relies entirely on the Niche geometry mapping layer, no ID signal from SAFI.

---

## Open questions

- Material and SAFI module; what changes after analysis; whether/how the analytical model is used; units and coordinate conventions; who approves structural changes
- Why columns/`IfcMember` lack section profiles in the Revit IFC export
- Whether the 78–83% SAFI connectivity gap is a real model issue or scope artifact — needs drafter
- Why 48 `IfcMember` elements are missing from the SAFI SDNF export — deprioritized
- Whether SDNF/KISS/Excel carries analysis results
- Manual rebuild time baseline — deprioritized, current focus is the comparison tool (D-005), not time savings

---

## Active risks

- SAFI exposes too little structured data (profiles missing on non-beam elements; 48 Members not in SDNF export).
- SAFI import connectivity is poor (78-83% floating) — may indicate real modeling gaps.
- Section/material name mismatch between systems needs a real mapping dictionary, not string equality (confirmed today, not just a risk anymore).
- There isn't enough project data for labeling yet (only one file tested).

---

## Evidence collected

- `docs/evidence/safi-integration.md`: no API; IFC import-only; real-file inspection; SAFI import connectivity results; geometry matcher result (47/47 matched, sub-mm).
- `docs/evidence/ifc-test-protocol.md`: original protocol's SAFI-export step (`compare R1.ifc S1.ifc`) can't run as written (SAFI has no IFC export) — superseded by the geometry-matcher approach that was actually built and proven.

---

## Next decision gate

**G0: DECIDED — Fail** (D-013). **Next gate: G1** (MVP-1 precision/recall target, drafter trusts the report) — in progress, not yet met.

---

## Next actions

1. Build a real SectionMapping dictionary (imperial ↔ metric section equivalence, e.g. `W18X40` ↔ `W460x60`) to resolve the "verify section" flag.
2. With the drafter: confirm whether the 78–83% SAFI connectivity gap and the missing 48 `IfcMember` elements are real issues or export-setting artifacts.
3. Extend `report.py` toward the full plan.md §7 report (confidence, match reason) and test on a second real project once available.
4. Decide G1 criteria (target precision/recall) with the drafter.
