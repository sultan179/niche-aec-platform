# Niche AEC Project State

**Updated:** 2026-09-24
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1, MVP-1 (read-only reconciliation report). G0 exit gate passed 2026-09-17.
- **Current objective:** the matching/diff pipeline is technically solid and tested (44 tests, was 0 at the start of today). Scope is confirmed narrower than assumed: **section shape is the only thing that needs reconciling** — materials are explicitly out of scope. What's left is almost entirely about the drafter: confirming his workflow, getting sign-off, testing on more real data. Nothing else can move without him.

---

## Known facts

Drafter interview: PDF modeled in Revit, rebuilt by hand in SAFI, results applied to Revit by hand (print-and-tick). Revit/SAFI IDs differ; coordinates close but not identical; gridlines match.

- **FACT:** SAFI has no API, IFC-import-only. Revit's IFC export is GlobalId/Tag-stable, but **SAFI discards Revit's identity on import** — ID-based matching isn't viable (D-013, G0 = Fail). A geometry matcher (`parse_sdnf.py`, `match.py`, `section_mapping.py`, `report.py`, `three_way_diff.py`) replaces it: 90° coordinate transform (`SAFI_x=Revit_y, SAFI_y=-Revit_x`), mutual-best matching, 1:N/N:N chain matching for SAFI's segment splits (verified on one real case so far).
- **FACT (2026-09-24):** SAFI can export SDNF in **imperial** (Revit-style section names) — removes the metric↔imperial translation problem entirely. The old SectionMapping CSV dictionary (6 pairs, needed sign-off) is replaced by simple formatting normalization (`normalize_section()` — case, spaces, stray dashes, unicode `×`; digits/decimals/`/` untouched since those are real differences). Verified: 22/22 real matched sections compare exactly equal. **Going forward, SAFI's SDNF export must stay in imperial.** Also fixed a real bug found along the way: the imperial export's coordinates are in inches, not mm — `parse_sdnf.py` now reads the SDNF's own units line instead of assuming one unit.
- **FACT (2026-09-24):** the whole matching/diff pipeline had **zero automated tests** this morning. Now has 44, across all 4 modules (`section_mapping`, `match`, `report` implicitly, `three_way_diff`). Two rounds of code review caught 4 real bugs along the way (all fixed, verified): a false "matched a closer element" claim in `explain_unmatched`, an `"ambiguous"` status silently hiding a real section mismatch, a stale baseline making everything look falsely "newly ambiguous," and fragile string-matching for the ambiguous flag (now a real boolean column). Full detail in `docs/evidence/safi-integration.md`.
- **FACT (2026-09-24):** added `find_ambiguous()` (flags ties — 2+ same-category candidates within tolerance) and `explain_unmatched()` (deterministic reason codes for unmatched elements). On real data: 0 ambiguous matches, and all 32 "missing in SAFI" elements are 3–9m from anything — genuinely unmodeled, not near-misses. **Open judgment call, not a bug:** `find_ambiguous()` doesn't weigh how much closer the winner was (0mm vs. 480mm runner-up still counts ambiguous) — not yet known to cause noise, worth tightening if it does.
- **FACT (2026-09-22, verified):** SAFI splits well-connected Revit beams into multiple SDNF sub-segments at real (sub-200mm) gaps that already exist in Revit's model, not an IFC/SAFI artifact — confirmed by cross-referencing SAFI's 0mm-tolerance joint coordinates against Revit's data. This is what chain matching handles.
- **FACT (2026-09-22/23, drafter):** SAFI is the sizing source of truth for **sections only** — no automated check exists today for whether the drafter's manual Revit sync matches, which is the gap the reconciliation report fills. Materials are explicitly out of scope (drafter doesn't use/label Revit material or manage SAFI material) — investigated and parked 2026-09-23.
- **FACT (2026-09-23):** built the three-way diff (`baseline.py`, `three_way_diff.py`), keyed by **Revit GlobalId** (the only side proven stable across time). Verified end-to-end on 3 of 5 real-world change paths with actual controlled Revit/SAFI edits, not simulation: Revit-only change, SAFI-only change, and conflict (both sides changed) all classified correctly. `new`/`missing` remain simulation-only.
- **FACT/DECISION (2026-09-24):** G1 will **not** be measured by having the drafter manually confirm/correct every match — that would recreate the exact manual burden the tool exists to remove. Instead: precision is largely self-verifying (tight geometry rarely coincides by accident), recall needs only a small targeted review of genuinely unresolved elements, plus controlled real-edit tests (same method used to verify the three-way diff).
- **FACT (2026-09-24), narrows a known gap:** checked one real column directly — it's modeled cleanly (proper Type, Structural Material), same as beams, so the missing section-profile issue isn't a modeling problem. The IFC export itself carries no named-profile data for columns, even though beams get it. Points at Revit's IFC exporter treating Structural Columns differently from Structural Framing — a specific, checkable question for the drafter now, not a vague "why is data missing."
- `data/ifc/`: `Cleaned/` holds current test files; `Archived/` holds older messy-file artifacts; `Cleaned/diff-test-artifacts/` holds three-way-diff test exports. All git-ignored/confidential.
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, D-001–D-013. Latest: **D-013, G0 = Fail** — matching relies entirely on the Niche geometry mapping layer, no ID signal from SAFI.

---

## Open questions

- Why columns/`IfcMember` lack section profiles in Revit's IFC export — narrowed to a specific export-settings question (see above), still needs the drafter.
- Whether SDNF/KISS/Excel carries analysis results.
- Manual rebuild time baseline — deprioritized, current focus is the comparison tool (D-005), not time savings.

---

## Active risks

- Chain matching and imperial-SDNF-export both only proven on one real project — need more real data to confirm they generalize.
- Columns/Members systematically missing section profiles — root cause narrowed but unconfirmed.
- Three-way diff can't track SAFI-only elements across baselines (no stable SAFI-side ID); `new`/`missing` paths are simulation-only; chain-matched rows use a joined-string key that could misbehave if grouping changes across runs.
- The current "baseline" is just the last report generated, not an engineer-approved one — no approval step exists yet (Phase 2/G2).
- `find_ambiguous()` doesn't weigh how much closer the winning candidate was — see Known facts.

---

## Evidence collected

- `docs/evidence/safi-integration.md`: no API; IFC import-only; identity not retained; connectivity comparisons; geometry matcher results; SectionMapping simplification; three-way diff build and real-world verification; material-scope correction; code review findings.
- `docs/evidence/ifc-test-results.md`: completed results sheet for the original protocol.
- `docs/evidence/ifc-test-protocol.md`: superseded by the geometry-matcher approach actually built and proven.

---

## Next decision gate

**G0: DECIDED — Fail** (D-013). **Next gate: G1** (MVP-1 precision/recall target, drafter trusts the report) — in progress, not yet met. Measurement approach decided (self-verifying geometry + targeted review, not full drafter labeling); actual thresholds still need agreeing.

---

## Next actions

1. With the drafter: root-cause the column section-profile gap (specific export-settings question now, see Known facts).
2. Test chain matching and the imperial-SDNF workflow on a second/third real project.
3. Agree G1's actual precision/recall thresholds with the drafter (method already decided).
4. Optional: test the three-way diff's `new`/`missing` paths against a real add/delete edit; drop now-pointless `revit_material`/`safi_material` columns from `report.py`'s output.
