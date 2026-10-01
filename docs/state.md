# Niche AEC Project State

**Updated:** 2026-10-01
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1 (MVP-1 pipeline, done and tested) running in parallel with 2 (Revit pane) — see D-014, 2026-09-29. G0 exit gate passed 2026-09-17.
- **Current objective:** the Phase 2 Revit add-in is confirmed working **end-to-end on real data, inside real Revit** (not just the earlier synthetic-data check) — dockable pane, row-click highlighting, a "highlight all unmatched sections" button, and the entire Revit side reads live from the open model (`LiveGeometryReader.cs`): geometry, category, identity, and section. The dead Revit-report-path fallback was removed entirely this session (live geometry is now required, not optional); a SAFI file picker (Browse button) replaced manual path typing. `revit-addin/README.md` has the technical detail. G1 (precision/recall thresholds, drafter trust) stays open, assessed alongside the pane.

---

## Known facts

Drafter interview: PDF modeled in Revit, rebuilt by hand in SAFI, results applied to Revit by hand (print-and-tick). Revit/SAFI IDs differ; coordinates close but not identical; gridlines match.

- **FACT:** SAFI has no API, IFC-import-only. Revit's IFC export is GlobalId/Tag-stable, but **SAFI discards Revit's identity on import** — ID-based matching isn't viable (D-013, G0 = Fail). A geometry matcher (`parse_sdnf.py`, `match.py`, `section_mapping.py`, `report.py`, `three_way_diff.py`) replaces it: 90° coordinate transform (`SAFI_x=Revit_y, SAFI_y=-Revit_x`), mutual-best matching, 1:N/N:N chain matching for SAFI's segment splits.
- **FACT (2026-09-24):** SAFI can export SDNF in **imperial** (Revit-style section names), removing the metric↔imperial translation problem. Section comparison is now pure formatting normalization (`normalize_section()`), not a dictionary. **SAFI's SDNF export must stay in imperial.**
- **FACT (2026-09-24):** pipeline test suite built from zero to 44 tests; two review rounds caught 4 real bugs (false "matched a closer element" claim, ambiguous status hiding a real mismatch, stale baseline, fragile string-matching). Full detail: `docs/evidence/safi-integration.md`.
- **FACT (2026-09-22, verified):** SAFI splits well-connected Revit beams into multiple SDNF sub-segments at real sub-200mm gaps already in Revit's model — what chain matching handles.
- **FACT (2026-09-22/23, drafter):** SAFI is the sizing source of truth for **sections only** — materials are explicitly out of scope.
- **FACT (2026-09-23):** three-way diff (`baseline.py`, `three_way_diff.py`) keyed by Revit GlobalId, verified on 3 of 5 real-world change paths (Revit-only, SAFI-only, conflict). `new`/`missing` remain simulation-only.
- **FACT/DECISION (2026-09-24):** G1 measured by self-verifying geometry + targeted review of unresolved elements + controlled real-edit tests — not full drafter labeling of every match.
- **FACT (2026-09-29, confirmed):** columns/members missing section profiles in the IFC export is a Revit IFC-exporter limitation, not a modeling problem. Worked around by `SectionOverrideReader.cs` reading `Section Name Key` live from the model — 0/79 elements left without a section, was 55/79.
- **FACT (2026-09-29, confirmed):** SAFI's SDNF export silently excludes members whose "Change Member Type" is `Generic` — a "missing in SAFI" result can mean "never modeled" or "modeled but left Generic," indistinguishable from the Revit side.
- **FACT (2026-10-01):** closed the remaining Revit-side gap — geometry, category, and identity now read live (`LiveGeometryReader.cs`), not just section. Every Structural Column here uses `LocationPoint` (real endpoints need Base/Top Level + offset); every Structural Framing element uses `LocationCurve` (direct read). Confirmed end-to-end in real Revit, not just the synthetic-data check from the first pass.
- **FACT (2026-10-01):** hit and fixed a real coordinate-frame bug going live — `Element.Location` returns Revit's **internal/project coordinates**, but the proven pipeline needs **Shared Coordinates**. Root-caused via a direct ~85m distance check on real data. First fix attempt (`ProjectLocation.GetProjectPosition`) was the wrong API and made it worse (117–171m off). Real fix, verified via reflection against the real `RevitAPI.dll`: `BasePoint.GetSurveyPoint(doc).SharedPosition - .Position` (a pure translation, valid since this project's rotation angle is 0). A runtime guard (`AssertNoRotation`) now throws instead of silently producing wrong coordinates if a future project is rotated — added after code review flagged the unverified assumption. Full narrative: `docs/evidence/safi-integration.md`.
- **FACT (2026-10-01):** chain-matched rows never ran the section-agreement check at all — always showed "matched (chain)" regardless of whether segments' sections agreed. Caught live by Sultan: one 2-floor Revit HSS column (`HSS6X6X1/2`) matched to 2 SAFI segments, one wrongly modeled as `W16x26` — a genuine SAFI modeling mistake, not a matcher bug. Fixed (`chain_section_status()` in `report.py`, 5 new tests); a follow-up gap (SAFI-internal disagreement silently read as "no Revit profile to check" when Revit had no section) was caught in code review and fixed the same session. Test suite now at 57 (was 44).
- **FACT (2026-10-01, not yet solved):** this add-in can't be handed to other staff as-is. `PipelineRunner.PythonExe` is hardcoded to Sultan's own Python install path; `NicheReconciliation.addin`'s `<Assembly>` path is hardcoded to Sultan's repo location; the Python pipeline isn't bundled into the DLL, it's shelled out to at runtime, so any machine running this needs the full repo + Python 3.11+ + `pip install -r requirements.txt`. Discussed only, no code changes made.
- `data/ifc/`: `Cleaned/` holds current test files; `Archived/` holds older messy-file artifacts. All git-ignored/confidential.
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, D-001–D-013. Latest: **D-013, G0 = Fail** — matching relies entirely on the Niche geometry mapping layer, no ID signal from SAFI.

---

## Open questions

- Whether SDNF/KISS/Excel carries analysis results.
- Manual rebuild time baseline — deprioritized, current focus is the comparison tool (D-005), not time savings.
- Discussed (not decided): a live backend + database so engineers can write persistent notes against a reconciliation run. This is already the shape of `plan.md`'s architecture (Projects/Approvals/Audit in PostgreSQL) — treat as G2 scope, not an ad hoc addition to the current read-only pane.

---

## Active risks

- Chain matching and imperial-SDNF-export both only proven on one real project — need more real data to confirm they generalize.
- **Incomplete (started 2026-10-01, not finished):** Sultan asked to split the match tolerance into separate horizontal/vertical components (tight horizontal, loose vertical) to address the Z-offset false-negative below. Investigated `match.py`'s `pair_distance()`/tolerance plumbing but got pulled onto other urgent fixes before implementing it — `match.py` still uses one combined `MATCH_TOL_M = 0.5` tolerance. **Next session should pick this up directly**, not assume it's done.
- **Vertical (Z) reference-line inconsistency (2026-09-29):** roughly half of matched beams show a Z-offset tracking ~half the section's own depth (inconsistent Start/End Level Offset usage in Revit), the other half show 0.0000m for the same section types. Caused one real false negative (W24x55, 0.628m > 0.5m tolerance) — horizontal position was correct within centimeters. Tolerance kept strict for now; the tolerance-split item above is the intended fix.
- Three-way diff can't track SAFI-only elements across baselines; `new`/`missing` paths are simulation-only; chain-matched rows use a joined-string key that could misbehave if grouping changes across runs.
- The current "baseline" is just the last report generated, not an engineer-approved one — no approval step exists yet (Phase 2/G2).
- `find_ambiguous()` doesn't weigh how much closer the winning candidate was.

---

## Evidence collected

- `docs/evidence/safi-integration.md`: no API; IFC import-only; identity not retained; geometry matcher results; SectionMapping simplification; three-way diff build and real-world verification; material-scope correction; code review findings; live-geometry coordinate-frame bug and fix; chain-match section-check bug.
- `docs/evidence/ifc-test-results.md`: completed results sheet for the original protocol.
- `docs/evidence/ifc-test-protocol.md`: superseded by the geometry-matcher approach actually built and proven.

---

## Next decision gate

**G0: DECIDED — Fail** (D-013). **Next gate: G1** (MVP-1 precision/recall target, drafter trusts the report) — in progress, not yet met. Measurement approach decided; actual thresholds still need agreeing.

---

## Next actions

1. **Finish the horizontal/vertical tolerance split** in `match.py` — started 2026-10-01, not completed (see Active risks).
2. Get the drafter reviewing results in the Revit pane itself — now confirmed working end-to-end on real data, not just synthetic. Unblocked, ready now.
3. Agree G1's actual precision/recall thresholds with the drafter (method already decided).
4. Test chain matching and the imperial-SDNF workflow on a second/third real project.
5. Solve distribution for other staff: auto-detect Python instead of the hardcoded path; decide how the `.addin` file and repo get onto each machine (see Known facts).
6. Optional: test the three-way diff's `new`/`missing` paths against a real add/delete edit; drop unused `revit_material`/`safi_material` columns from `report.py`'s output.
