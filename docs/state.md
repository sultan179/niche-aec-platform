# Niche AEC Project State

**Updated:** 2026-09-23
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1, MVP-1 (read-only reconciliation report). G0 exit gate passed 2026-09-17.
- **Current objective:** three-way diff mechanism (plan.md §6/§11) built and verified on the no-change case. Next: test it against a real or simulated change (the case that actually matters); grow SectionMapping with more real data; decide G1 criteria with the drafter.

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
- **FACT (2026-09-22):** built and verified 1:N/N:N chain matching (`build_chains`/`match_chains` in `match.py`) — groups leftover same-category elements into connected runs, matches by outer-endpoint distance. Verified on the real case: the 2-beam/3-segment run now matches correctly at 0.0mm offset. Report counts moved exactly as predicted (`missing in SAFI` 34→32, `no Revit source found` 3→0).
- **FACT (2026-09-22, drafter):** SAFI is the sizing/material source of truth — decisions finalize during analysis in SAFI, and the drafter manually syncs Revit to match afterward, **for sections**. Confirms the SectionMapping dictionary formalizes an existing manual task rather than solving a hypothetical one, and that there's currently no automated check that the sync happened correctly — exactly the gap the reconciliation report fills. (**Corrected 2026-09-23 below** — this does not hold for materials, only sections.)
- **FACT (2026-09-23, drafter) — corrects the above for materials:** the drafter does not use or manually label Revit's material property, and doesn't actively manage material in SAFI either. Material sync between Revit and SAFI is **out of scope for now**, parked for a later phase. MaterialMapping will not be built until that changes. **Section shape is the only thing the drafter actually cares about being reconciled** — that's the real scope of the reconciliation report, not sections-and-materials as previously assumed.
- **FACT (2026-09-23):** built the three-way diff mechanism (`baseline.py`, `three_way_diff.py`) — `save_baseline()` stores a report snapshot; `diff_against_baseline()` classifies each element as unchanged/new/missing/changed-Revit-only/changed-SAFI-only/conflict, keyed by **Revit GlobalId** (the only side proven stable across time — SAFI's `piece_id` stability across re-exports is unverified, so SAFI-only elements aren't tracked across baselines yet). Found and fixed a real bug: comparing fields with plain `!=` gave 55/78 false "changed" flags on a same-data test, because Python's `nan != nan` is always `True` — fixed by normalizing missing values before comparing.
- **FACT (2026-09-23) — verified end-to-end on genuine real-world changes, 3 of 5 paths:** changed one real Girder's section in Revit (`W18X40` → `W21X44`) → correctly flagged `changed in Revit only`. Changed one real member's section in SAFI (`W460x60` → `W530x66`) → correctly flagged `changed in SAFI only`. Then changed **both sides of the same matched element** (found the SAFI counterpart of the Revit girder via the baseline data — Phys #57, not the earlier M55) → correctly flagged `conflict - changed in both`, right values on both sides. Every run: exactly 1 element flagged, 77/78 unchanged. On top of the earlier same-data (78/78 unchanged) and mutated-data-simulation checks. `new` and `missing` remain simulation-only — real tests would need adding/deleting a live element, more invasive than a section swap.
- Columns/`IfcMember` elements still have no section profile in Revit's IFC export, on both files tested — looks systemic, not file-specific.
- **`data/ifc/` reorganized (2026-09-18):** `Cleaned/` holds the current/active test files (the properly-connected Kingsway export + its SDNF + SAFI report); `Archived/` holds the older messy-file test artifacts. Still git-ignored/confidential either way.
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, D-001–D-013. Latest: **D-013, G0 = Fail** — matching relies entirely on the Niche geometry mapping layer, no ID signal from SAFI.

---

## Open questions

- Material and SAFI module; what changes after analysis; whether/how the analytical model is used; units and coordinate conventions; who approves structural changes
- Whether SAFI's exported `safi_material` value is a real per-element property or a fixed SDNF export default — every matched element so far shows `A36` with zero variation despite 3 distinct Revit material labels present. Deprioritized (material sync is parked), but worth resolving if material work resumes.
- Why columns/`IfcMember` lack section profiles in the Revit IFC export (confirmed systemic across 2 files, root cause still unknown)
- Whether SDNF/KISS/Excel carries analysis results
- Manual rebuild time baseline — deprioritized, current focus is the comparison tool (D-005), not time savings

---

## Active risks

- Chain matching only tested on one real case (2 Revit beams / 3 SAFI segments) — needs more real projects to confirm it generalizes.
- Section/material name mismatch needs the dictionary to keep growing with more real data — only 6 pairs confirmed-by-evidence so far, none yet drafter/engineer-signed-off.
- Columns/Members systematically missing section profiles in Revit's export — root cause unknown.
- Only two files tested — not enough for labeling/evaluation yet.
- Three-way diff can't track SAFI-only elements (no Revit match) across baselines — no key proven stable across re-exports on the SAFI side.
- Real-world edit tests have covered 3 of 5 paths (changed in Revit only, changed in SAFI only, conflict). `new` and `missing` are still simulation-only on real data, not yet confirmed with an actual add/delete edit.
- Chain-matched rows key on a joined-string `revit_id` — a different chain grouping across runs would show as spurious new+missing instead of unchanged.
- The current "baseline" is just the last report generated, not an engineer-approved one — no approval step exists yet (that's Phase 2/G2 in the roadmap).

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

1. Test the three-way diff's remaining paths (new, missing) against real edits if worth the risk of adding/deleting a live element — changed-in-Revit-only, changed-in-SAFI-only, and conflict are all confirmed on genuine real-world changes now.
2. Grow the SectionMapping dictionary as more real projects are tested; get drafter/engineer sign-off on existing entries.
3. With the drafter: root-cause why columns/`IfcMember` lack section profiles in Revit's export.
4. Test chain matching on a second/third real project to confirm it generalizes beyond the one case it was built for.
5. Decide G1 criteria (target precision/recall) with the drafter.
6. ~~Build a MaterialMapping dictionary~~ — parked (2026-09-23, drafter): material sync is out of scope for now, revisit when Revit material integration becomes a priority.
