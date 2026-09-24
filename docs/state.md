# Niche AEC Project State

**Updated:** 2026-09-24
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1, MVP-1 (read-only reconciliation report). G0 exit gate passed 2026-09-17.
- **Current objective:** three-way diff mechanism (plan.md §6/§11) built and verified end-to-end on 3 of 5 real-world change paths. Real scope confirmed narrower than assumed: **section shape is the only thing the drafter cares about being reconciled** — materials are parked. The old SectionMapping dictionary is gone too — SAFI exporting in imperial + simple formatting normalization replaces it. Next: decide G1 criteria with the drafter; test chain matching on a 2nd/3rd real project.

---

## Known facts

Drafter interview: PDF modeled in Revit, rebuilt by hand in SAFI, results applied to Revit by hand (print-and-tick). Revit/SAFI IDs differ; coordinates close but not identical; gridlines match.

- **FACT:** SAFI has no API, IFC-import-only. Revit's IFC export is GlobalId/Tag-stable, but **SAFI discards Revit's identity on import** — own numbering replaces it. ID-based matching isn't viable (D-013, G0 = Fail).
- **FACT:** built a geometry matcher (`parse_sdnf.py`, `match.py`, `report.py`, `section_mapping.py`). Coordinate transform: 90° rotation, `SAFI_x=Revit_y, SAFI_y=-Revit_x`, no offset. 1:N/N:N chain matching built and verified on one real case (2 Revit beams / 3 SAFI segments).
- **FACT (2026-09-24):** SAFI can export SDNF in **imperial** (Revit-style section names), removing the metric↔imperial translation problem entirely — only formatting (case, spacing) differs now. Found and fixed a real bug: the imperial export's coordinates are in inches, not mm; `parse_sdnf.py` now reads the SDNF's own units line instead of hardcoding mm. `section_mapping.py`'s old CSV dictionary (6 pairs, required sign-off) is replaced by `normalize_section()` — strips whitespace/case/stray dashes/unicode `×`, leaves digits and `/` untouched. Verified on real data: 22/22 real matched sections now compare exactly equal, zero mismatches; all 4 tests still pass. `section_mapping.csv`/`build_section_mapping.py` are now orphaned (left in place, unreferenced). **Going forward, SAFI's SDNF export must be in imperial, not metric.**
- **FACT (2026-09-24):** found the matching/diff pipeline (`parse_sdnf.py`, `match.py`, `section_mapping.py`, `three_way_diff.py`) had **zero automated tests** — only `ifc_inspect.py`'s IFC-parsing layer was covered. Added `test_section_mapping.py` (15 tests) covering `normalize_section`/`check_section` edge cases from today's work (case, spaces, unicode `×`, hyphens, HSS fraction/decimal preservation, empty-string handling). Fixed a real bug surfaced while designing the tests: `normalize_section("")` returned `""` instead of `None`, so `check_section` would try to compare an empty string instead of treating it as "no profile" — fixed. Added `test_match.py` (15 more tests) covering `match.py`'s core algorithm: coordinate transform, mutual-best tie-breaking (two Revit elements near one SAFI element — only the closer wins), category filtering, tolerance cutoff, chain building (touching/non-touching/junction topology), and chain matching (1:N splits, and the documented single-element-chain skip rule). All 34 tests (4+15+15) pass. `three_way_diff.py` still has no unit tests.
- **FACT (2026-09-18, drafter):** SAFI's connectivity tolerance is ~200mm; import never auto-connects fully — drafter always manually fixes connections in SAFI or rebuilds from scratch. A clean Revit model reduces but doesn't eliminate this.
- **FACT (2026-09-22, verified not guessed):** SAFI's connectivity-generation splits well-connected Revit beams into multiple SDNF sub-segments at real (sub-200mm) gaps that already exist in Revit's model — not an IFC/SAFI artifact. Root cause confirmed by cross-referencing SAFI's 0mm-tolerance joint coordinates against Revit's exported data (exact match to 4 decimals). This is what chain matching (above) now handles.
- **FACT (2026-09-22, drafter):** SAFI is the sizing source of truth for **sections** — decisions finalize in SAFI analysis, drafter manually syncs Revit's section afterward. No automated check exists today; that's the gap the reconciliation report fills.
- **FACT (2026-09-23, drafter) — corrects the above for materials:** the drafter does not use/label Revit's material property and doesn't actively manage material in SAFI either. Material sync is **out of scope for now**, parked for a later phase. **Section shape is the only real target of reconciliation.** (Investigation before this correction found Revit material labels never get rewritten to match SAFI, and SAFI's exported material was `A36` with zero variation across 46 matched elements — likely a fixed export default, never confirmed, now deprioritized.)
- **FACT (2026-09-23):** built the three-way diff (`baseline.py`, `three_way_diff.py`) — `save_baseline()` stores a report snapshot; `diff_against_baseline()` classifies each element as unchanged/new/missing/changed-Revit-only/changed-SAFI-only/conflict, keyed by **Revit GlobalId** (the only side proven stable across time; SAFI's `piece_id` stability across re-exports is unverified). Fixed a real bug: `nan != nan` in Python gave false "changed" flags on missing fields — fixed by normalizing before comparing.
- **FACT (2026-09-23) — verified end-to-end on 3 of 5 real-world change paths**, each isolated to exactly one matched element with everything else unchanged: Revit-only section change → `changed in Revit only`; SAFI-only section change → `changed in SAFI only`; same element changed on both sides → `conflict - changed in both`. `new` and `missing` remain simulation-only (would need a live add/delete edit).
- Columns/`IfcMember` elements still have no section profile in Revit's IFC export, on both files tested — looks systemic, root cause unknown.
- `data/ifc/`: `Cleaned/` holds current test files; `Archived/` holds older messy-file artifacts; `Cleaned/diff-test-artifacts/` holds today's three-way-diff test exports. All git-ignored/confidential.
- **FACT/DECISION (2026-09-24):** re-thought how G1 (precision/recall) actually gets measured. Plan.md §7's "drafter confirms/corrects every match" would recreate the exact manual print-and-tick burden the tool exists to remove — rejected as the approach. Instead: **precision** is largely self-verifying (a sub-millimeter, category-matched geometry pair essentially can't be a coincidental false match — no row-by-row human review needed); **recall** only needs the drafter's eyes on the small set of genuinely unresolved elements (today: a subset of 32 "missing in SAFI," most already explained by the known profile-loss issue), not a full report review. A second, zero-drafter-effort measurement method: real controlled edits (like the 2026-09-23 girder/member tests) where we already know the ground truth because we made the change ourselves. No labeling infrastructure was built for this — the collection mechanism was never confirmed with the drafter, and building it risked repeating the MaterialMapping mistake (assuming a process nobody asked for).
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, D-001–D-013. Latest: **D-013, G0 = Fail** — matching relies entirely on the Niche geometry mapping layer, no ID signal from SAFI.

---

## Open questions

- Why columns/`IfcMember` lack section profiles in the Revit IFC export (confirmed systemic across 2 files, root cause still unknown)
- Whether SAFI's `safi_material` is a real per-element value or a fixed export default (deprioritized — material sync is parked)
- Whether SDNF/KISS/Excel carries analysis results
- Manual rebuild time baseline — deprioritized, current focus is the comparison tool (D-005), not time savings

---

## Active risks

- Chain matching only tested on one real case — needs more real projects to confirm it generalizes.
- Section comparison now depends on SAFI exporting SDNF in imperial — if the drafter's normal export workflow defaults to metric, this breaks silently unless re-checked.
- Only case/spacing formatting differences confirmed so far (one project) — other real-world formatting quirks may still turn up.
- Columns/Members systematically missing section profiles in Revit's export — root cause unknown.
- Three-way diff can't track SAFI-only elements (no Revit match) across baselines — no key proven stable across SAFI re-exports.
- `new`/`missing` diff paths are simulation-only, not yet confirmed with a real add/delete edit.
- Chain-matched rows key on a joined-string `revit_id` — a different chain grouping across runs would show as spurious new+missing instead of unchanged.
- The current "baseline" is just the last report generated, not an engineer-approved one — no approval step exists yet (Phase 2/G2).
- `three_way_diff.py` still has no unit tests — `section_mapping.py` and `match.py` are covered now.

---

## Evidence collected

- `docs/evidence/safi-integration.md`: no API; IFC import-only; identity not retained; connectivity comparisons; geometry matcher results; SectionMapping; three-way diff build and real-world verification; material-scope correction.
- `docs/evidence/ifc-test-results.md`: completed results sheet for the original protocol.
- `docs/evidence/ifc-test-protocol.md`: superseded by the geometry-matcher approach actually built and proven.

---

## Next decision gate

**G0: DECIDED — Fail** (D-013). **Next gate: G1** (MVP-1 precision/recall target, drafter trusts the report) — in progress, not yet met. Measurement approach (2026-09-24): precision via geometric tightness (largely self-verifying), recall via a small targeted review of unresolved elements + controlled real-edit tests — not full drafter review of every match.

---

## Next actions

1. With the drafter: root-cause why columns/`IfcMember` lack section profiles in Revit's export.
2. Test chain matching on a second/third real project to confirm it generalizes beyond the one case it was built for.
3. Decide G1 criteria (target precision/recall numbers) with the drafter — measurement approach already decided (see above), just needs the actual thresholds agreed.
4. Confirm with the drafter that exporting SDNF in imperial is a workflow they'll actually do going forward, not just a one-off test.
5. Optionally test the three-way diff's `new`/`missing` paths against a real add/delete edit.
6. Consider dropping `revit_material`/`safi_material` from `report.py`'s output now that material sync is confirmed out of scope (not done yet, harmless to leave).
7. Add unit tests for `three_way_diff.py` — `section_mapping.py` and `match.py` are covered now, that one isn't.
