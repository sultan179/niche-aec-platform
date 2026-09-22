# Niche AEC Project State

**Updated:** 2026-09-22
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1, MVP-1 (read-only reconciliation report). G0 exit gate passed 2026-09-17.
- **Current objective:** root cause of segment splitting found (Rigid Members). Next: widen outer-endpoint tolerance in the matcher to absorb it; grow SectionMapping.

---

## Known facts

Drafter interview: PDF modeled in Revit, rebuilt by hand in SAFI, results applied to Revit by hand (print-and-tick). Revit/SAFI IDs differ; coordinates close but not identical; gridlines match.

- **FACT:** SAFI has no API, IFC-**import-only** (SAFI support + UI, 2026-09-16/17).
- **FACT:** Revit's IFC export is GlobalId/Tag-stable (100% on re-export), but **SAFI discards Revit's identity on import** entirely — own numbering replaces it. ID-based matching isn't viable (D-013, G0 = Fail).
- **FACT:** built a geometry matcher (`tools/ifc_inspect/parse_sdnf.py`, `match.py`, `report.py`, `section_mapping.py`). Coordinate transform: 90° rotation, `SAFI_x=Revit_y, SAFI_y=-Revit_x`, no offset. SectionMapping dictionary built from real matched pairs (imperial↔metric), every row unconfirmed until drafter/engineer sign-off.
- **FACT (2026-09-18, drafter):** SAFI's connectivity tolerance is ~200mm (drafter's estimate); Revit→SAFI import doesn't always auto-connect.
- **FACT (2026-09-18):** tested a second, properly-connected file (`data/ifc/Cleaned/`) from the drafter. SAFI import connectivity: **0/172 floating, 36/172 (21%) cantilever, ~79% fully connected** — inverse of the first (messy) file's 78–83% broken rate. Better Revit modeling clearly reduces the failure rate (nuanced 2026-09-22 below — doesn't eliminate manual fixing entirely).
- **FACT (2026-09-18):** matcher re-run on this second file — the coordinate transform and SectionMapping dictionary both **generalized cleanly** (22/24 beams matched, zero new mismatches). But SAFI's connectivity-generation **splits well-connected beams into multiple sub-segments** (79→172 members), which the current 1:1-only matcher can't handle — 2 beams/2 SAFI elements fell out of matching because of it. This is the "merge SAFI segments" step plan.md §8 already names but isn't built yet.
- **FACT (2026-09-22):** fixed a real correctness bug — `parse_sdnf.py` discarded the SDNF piece-ID number, using SAFI's display name as the unique key instead. Since SAFI can reuse the same name across two different pieces (proven on real data), this silently dropped elements from every matcher run. Fixed: `piece_id` is now the key, `name` kept separately for readability.
- **FACT (2026-09-22) — root cause of segment splitting found (verified, not guessed):** the mystery split points are a **real small gap that already exists in Revit's own model** — a secondary diagonal member (`IfcMember`, profile `W16X26`) frames in near the main beam but doesn't land exactly on its line. Proven by cross-referencing SAFI's 0mm-tolerance joint coordinates against Revit's exported data: elevations match to 4 decimal places (3788.41mm ≈ 3.7884m). SAFI's ~200mm connectivity tolerance decides whether to bridge that real gap with an auto-inserted **Rigid Member** (`Offset/Dummy` type, excluded from SDNF since it's not real steel — why `find_junctions.py` found nothing) or leave it visibly disconnected. Not an IFC/SAFI pipeline artifact. **Resolved without needing the drafter** — my first hypothesis ("IFC coordinate rounding") was wrong and got corrected by checking real data.
- **FACT (2026-09-22, drafter):** the real workflow is: draft in Revit → export IFC → import into SAFI → **connections always come in broken to some degree** → drafter manually fixes them in SAFI, or rebuilds from scratch. Always true, not an edge case. The "native SAFI file" we treated as a clean reference is **the drafter's manually-corrected result**, not proof that clean Revit modeling alone yields a connected import. Reinforces plan.md's Problem A/B rather than undermining them.
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

- 1:N segment merging not built — matcher misses beams SAFI splits when it inserts Rigid Members to bridge IFC-import coordinate gaps. Root cause now known (2026-09-22); fix is a tolerance widening, not detection of the rigid links themselves (they aren't in SDNF).
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

1. Build 1:N segment-merging in the matcher: group collinear connected SAFI segments into runs, match against Revit runs with a wider outer-endpoint tolerance (to absorb Rigid-Member-sized gaps, bounded by SAFI's ~200mm tolerance).
2. Grow the SectionMapping dictionary as more real projects are tested; get drafter/engineer sign-off on existing entries.
3. With the drafter: root-cause why columns/`IfcMember` lack section profiles in Revit's export.
4. Decide G1 criteria (target precision/recall) with the drafter.
