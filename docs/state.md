# Niche AEC Project State

**Updated:** 2026-09-18
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1, MVP-1 (read-only reconciliation report). G0 exit gate passed 2026-09-17.
- **Current objective:** matcher validated on a second real file; next real gap is 1:N segment merging (SAFI splits connected beams).

---

## Known facts

Drafter interview: PDF modeled in Revit, rebuilt by hand in SAFI, results applied to Revit by hand (print-and-tick). Revit/SAFI IDs differ; coordinates close but not identical; gridlines match.

- **FACT:** SAFI has no API, IFC-**import-only** (SAFI support + UI, 2026-09-16/17).
- **FACT:** Revit's IFC export is GlobalId/Tag-stable (100% on re-export), but **SAFI discards Revit's identity on import** entirely — own numbering replaces it. ID-based matching isn't viable (D-013, G0 = Fail).
- **FACT:** built a geometry matcher (`tools/ifc_inspect/parse_sdnf.py`, `match.py`, `report.py`, `section_mapping.py`). Coordinate transform: 90° rotation, `SAFI_x=Revit_y, SAFI_y=-Revit_x`, no offset. SectionMapping dictionary built from real matched pairs (imperial↔metric), every row unconfirmed until drafter/engineer sign-off.
- **FACT (2026-09-18, drafter):** SAFI's connectivity tolerance is ~200mm (drafter's estimate); Revit→SAFI import doesn't always auto-connect.
- **FACT (2026-09-18):** tested a second, properly-connected file (`data/ifc/Cleaned/`) from the drafter. SAFI import connectivity: **0/172 floating, 36/172 (21%) cantilever, ~79% fully connected** — inverse of the first (messy) file's 78–83% broken rate. **Proves the earlier connectivity failure was a modeling-quality issue, not a SAFI/IFC platform limitation.**
- **FACT (2026-09-18):** matcher re-run on this second file — the coordinate transform and SectionMapping dictionary both **generalized cleanly** (22/24 beams matched, zero new mismatches). But SAFI's connectivity-generation **splits well-connected beams into multiple sub-segments** (79→172 members), which the current 1:1-only matcher can't handle — 2 beams/2 SAFI elements fell out of matching because of it. This is the "merge SAFI segments" step plan.md §8 already names but isn't built yet.
- Columns/`IfcMember` elements still have no section profile in Revit's IFC export, on both files tested — looks systemic, not file-specific.
- **`data/ifc/` reorganized (2026-09-18):** `Cleaned/` holds the current/active test files (the properly-connected Kingsway export + its SDNF + SAFI report); `Archived/` holds the older messy-file test artifacts. Still git-ignored/confidential either way.
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, D-001–D-013. Latest: **D-013, G0 = Fail** — matching relies entirely on the Niche geometry mapping layer, no ID signal from SAFI.

---

## Open questions

- Material and SAFI module; what changes after analysis; whether/how the analytical model is used; units and coordinate conventions; who approves structural changes
- Why columns/`IfcMember` lack section profiles in the Revit IFC export (confirmed systemic across 2 files, root cause still unknown)
- Whether SDNF/KISS/Excel carries analysis results
- Manual rebuild time baseline — deprioritized, current focus is the comparison tool (D-005), not time savings

---

## Active risks

- 1:N segment merging not built — matcher misses beams SAFI splits at real connections (new, 2026-09-18).
- Section/material name mismatch needs the dictionary to keep growing with more real data — only 6 pairs confirmed-by-evidence so far, none yet drafter/engineer-signed-off.
- Columns/Members systematically missing section profiles in Revit's export — root cause unknown.
- Only two files tested — not enough for labeling/evaluation yet.

---

## Evidence collected

- `docs/evidence/safi-integration.md`: no API; IFC import-only; identity not retained; two-file connectivity comparison (messy vs. cleaned); geometry matcher results on both files; SectionMapping dictionary.
- `docs/evidence/ifc-test-results.md`: completed results sheet for the original protocol.
- `docs/evidence/ifc-test-protocol.md`: superseded by the geometry-matcher approach actually built and proven.

---

## Next decision gate

**G0: DECIDED — Fail** (D-013). **Next gate: G1** (MVP-1 precision/recall target, drafter trusts the report) — in progress, not yet met.

---

## Next actions

1. Build 1:N segment-merging support in the matcher (a Revit beam may map to multiple SAFI sub-segments after connectivity generation).
2. Grow the SectionMapping dictionary as more real projects are tested; get drafter/engineer sign-off on existing entries.
3. With the drafter: root-cause why columns/`IfcMember` lack section profiles in Revit's export.
4. Decide G1 criteria (target precision/recall) with the drafter.
