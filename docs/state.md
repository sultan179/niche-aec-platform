# Niche AEC Project State

**Updated:** 2026-09-29
**Core plan:** `docs/plan.md` v0.1 (APPROVED, 2026-09-17)

---

## Phase and objective

- **Current phase:** 1 (MVP-1 pipeline, done and tested) running in parallel with 2 (Revit pane) — see D-014, 2026-09-29. G0 exit gate passed 2026-09-17.
- **Current objective:** the Phase 2 Revit add-in works end-to-end on real data, inside Revit — dockable pane, live section reads for columns/members (closing the column/member profile gap entirely), and row-click highlighting. `revit-addin/README.md` has the technical detail. Drafter review will happen against this pane instead of the standalone Excel/PDF report. G1 (precision/recall thresholds, drafter trust) stays open and will be assessed alongside the pane, not before it. Geometry/category/identity still come from the Revit report (`.xlsx`), not a live read — see Active risks.

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
- **FACT (2026-09-29, confirmed):** columns/members missing section profiles in the IFC export is a **Revit IFC-exporter limitation, not a modeling problem** — closes the 2026-09-24 open question. Controlled test: drafter set proper `Section Name Key` values (e.g. `HSS6X6X1/2`) on the flagged columns, re-exported to IFC, re-ran `ifc_inspect.py inspect` — profile count stayed at 24/79 (exactly the beam count) both before and after. Verified directly in Revit's Type Properties that the column's section *is* set correctly; the IFC export still drops it. All 24 beams keep their profiles; 0 of 23 columns + 32 members ever get one, regardless of Revit-side data quality. **Tried and ruled out (2026-09-29):** setting "Export Type to IFC As" = `IfcColumnType` on the test column, re-exporting, re-inspecting — `profiles` still `NaN` for that exact element (materials and type name both correct, only the profile is missing). Not a Type Properties setting anyone can fix from Revit's side; looks like a genuine exporter limitation.
- **FACT (2026-09-29):** built the workaround for the column/member profile gap above — `SectionOverrideReader.cs` reads each Structural Column/Framing element's `Section Name Key` Type parameter live from the open document and patches it into the report (`apply_section_overrides()` in `run_for_addin.py`), bypassing the broken IFC path entirely for this one field. Verified end-to-end on real data: 0/79 elements left without a section, down from 55/79. **Real wrinkle found along the way:** `Section Name Key` can have `HasValue == false` (genuinely unset) even while Revit's Type Properties UI still displays a value for it (a computed/fallback display, not a stored one) — confirmed via a temporary debug dump comparing `paramFound`/`paramHasValue`/`sectionRaw` for a specific stuck element. Fixed by falling back to the Type's own `.Name` when the parameter has no value, which carries the same section designation.
- **FACT (2026-09-29, confirmed):** SAFI's SDNF export **silently excludes members whose "Change Member Type" is set to `Generic`** — only `Beam`/`Column`-classified members get exported, with no warning from SAFI. Found via a real case: Member M11 ("#686 : W-Wide Flang", W16x26) was fully modeled in SAFI and visible in its Member Attributes browser, but absent from *every* SDNF export, including a fresh same-day one — ruling out staleness. Changing its type from `Generic` to `Beam` and re-exporting made it appear immediately (confirmed via `parse_sdnf.py`). **Practical impact:** the report's "missing in SAFI" status can mean either "genuinely never modeled" or "modeled but left as `Generic` type" — these look identical from the Revit side. Worth flagging to the drafter as a habit to check when a "missing in SAFI" result is surprising.
- `data/ifc/`: `Cleaned/` holds current test files; `Archived/` holds older messy-file artifacts; `Cleaned/diff-test-artifacts/` holds three-way-diff test exports. All git-ignored/confidential.
- Details: `docs/evidence/safi-integration.md`.

---

## Validated decisions

See `docs/decisions.md`, D-001–D-013. Latest: **D-013, G0 = Fail** — matching relies entirely on the Niche geometry mapping layer, no ID signal from SAFI.

---

## Open questions

- Whether SDNF/KISS/Excel carries analysis results.
- Manual rebuild time baseline — deprioritized, current focus is the comparison tool (D-005), not time savings.

---

## Active risks

- Chain matching and imperial-SDNF-export both only proven on one real project — need more real data to confirm they generalize.
- **RESOLVED (2026-09-29):** columns/members missing section profiles — the Revit add-in now reads section data live from the model (`SectionOverrideReader.cs`) instead of relying on the broken IFC export path for this one field. Verified on real data: 0 rows left at "no Revit profile to check" (was 55/79). See Known facts for the fix and the one non-obvious wrinkle it needed.
- **Vertical (Z) reference-line inconsistency (2026-09-29, deliberately not fixed yet):** checked every matched beam pair's Z-offset — roughly half show a consistent offset that tracks ~half the section's own depth (W16→~0.20m, W14→~0.18m, W12→~0.15m), the other half show 0.0000m for the *same* section types. Reads as inconsistent Revit modeling (some beams have a Start/End Level Offset applied, some don't), not a single systematic convention. Caused exactly one real "no Revit source found" false negative (a W24x55, offset ~0.30m tracking its larger depth, pushed total distance to 0.628m > the 0.5m tolerance) — horizontal position for that pair was correct within centimeters. **Decision: kept matching tolerance strict/unchanged for now** rather than loosening it (risk of new false-positive matches elsewhere) — the principled fix would be splitting horizontal vs. vertical tolerance (tight horizontal, since it's what actually disambiguates identity; looser vertical, since this offset doesn't indicate a different physical member), not proposed to the drafter or implemented yet.
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
