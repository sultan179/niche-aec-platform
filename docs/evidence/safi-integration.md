# Evidence: SAFI integration

## 2026-09-16

- **FACT (source: email from SAFI support, 2026-09-16):** SAFI has **no API**.
- ~~Reported by Sultan (source to confirm): SAFI can export IFC.~~ **Corrected 2026-09-17, see below.**
- The test plan is in `docs/evidence/ifc-test-protocol.md`, run with `ifc_inspect.py`. The tool was tested on synthetic files only; it hasn't run on real Revit or SAFI exports yet.

**Already known** (source: safi.com, 2026-09-15):

- SAFI can import IFC.
- SAFI exports DXF, SDNF, and KISS formats.
- Reports can be saved as Excel, Access, or ASCII.

## 2026-09-17

- **FACT (source: SAFI Import/Export menu, direct observation):** SAFI's Import/Export menu offers **Export SDNF, Export KISS, AutoCAD (DXF)**, and **Import IFC** / **Import STAAD**. **There is no Export IFC option.** SAFI is IFC-import-only — this reverses the earlier unconfirmed report.
- **FACT (source: `ifc_inspect.py` run on real file `data/ifc/Kingsway Apartments - 1 floor test.ifc`, 2026-09-17):**
  - Schema: IFC2X3, CoordinationView 2.0. Exported by Revit 26.4.10.51.
  - Units: feet internally (scale 0.3048 to metres); tool converts automatically.
  - 95 physical elements (24 `IfcBeam`, 23 `IfcColumn`, 48 `IfcMember`), all 95 with materials recognized.
  - **Only the 24 beams have a recognized section profile name — all columns and `IfcMember` elements have none.**
  - Zero analytical content (no `IfcStructuralAnalysisModel`, no members/nodes/supports, no `IfcRelAssignsToProduct` links) — this is a physical-geometry-only export.
  - `Tag` field is populated on physical elements (Revit's element ID) — a candidate for matching now that GlobalId round-trip can't go through IFC.

## Implication (RECOMMENDATION)

- SAFI integration will be file-based, but **IFC is import-only, one direction (Revit → SAFI)**. The return path (SAFI → Niche) has to use SDNF, KISS, DXF, or the Excel/Access reports — `ifc_inspect.py` cannot read any of those formats.
- The round-trip GlobalId test in `docs/evidence/ifc-test-protocol.md` (`compare R1.ifc S1.ifc`) **cannot run as written** — there is no `S1.ifc`. The protocol needs revision: either read GlobalId/Tag preservation from SDNF/KISS text output directly, or accept that matching must rely on **Tag** and geometry (position/grid), not GlobalId, for the SAFI side.
- Whether SDNF/KISS preserve Revit's `Tag` value is now the key open question for identity matching (HYPOTHESIS: worth checking before assuming Tag survives export any better than GlobalId would have).

## 2026-09-18 — Connectivity is a modeling-quality issue, not a platform limitation

- **FACT (source: drafter, 2026-09-18):** SAFI's connectivity tolerance is approximately 200mm (drafter's estimate, not an exact spec). Revit→IFC→SAFI import doesn't always auto-connect in their normal workflow. This matters — our earlier tests only tried 10mm and 50mm tolerances, far below what's actually used in practice.
- **FACT (source: drafter-provided "cleaned"/properly-connected file, `data/ifc/Cleaned/Kingsway Apartments - 1 floor test.ifc`, same building as the original test):** 79 physical elements (24 beam/23 column/32 `IfcMember` — fewer Members than the original 48). Same systemic gap as before: only beams have a section profile name; columns/Members don't.
- **FACT (source: SAFI import report, `Safi Report Cleaned Import.rtf`):** **0/172 floating members, 36/172 (21%) cantilever** — roughly 79% fully connected. This is essentially the inverse of the original file's 78–83% broken rate.
- **Conclusion:** the earlier connectivity failure was a **real modeling-quality issue in that specific source file**, not a SAFI/IFC platform limitation. When the Revit model is properly connected before export, SAFI's import connectivity is excellent. This substantially changes the outlook on Problem A/B — the integration path is workable when the source model is clean.

## 2026-09-18 — Matcher validated on a second file; new gap found (segment splitting)

- **FACT (source: `match.py`/`report.py` re-run against the Cleaned file's SDNF export, `2026_05_13_Kingsway_V1 - TEST, 1 floor Connected.sdnf`):** the 90° coordinate transform and the SectionMapping dictionary (both built from the first file) **generalized cleanly** to this second, independently-connected export — 22/24 beams matched, zero new section mismatches.
- **FACT:** SAFI's connectivity generation **splits well-connected beams into multiple shorter sub-segments** at real connection points (the raw physical member count went from 79 to 172 after connectivity processing — same splitting behavior seen on the first file, now much more pronounced since more real connections exist). This broke 2 beams' 1:1 matching — the current matcher has no way to recognize "one Revit beam = several SAFI segments."
- **Implication (RECOMMENDATION):** this is exactly the "merge SAFI segments" normalization step `CLAUDE_INSTRUCTIONS.md` §8 already names as required, not a new architectural surprise. Next build priority: 1:N segment-merging support in the matcher.

## 2026-09-17 (continued) — Revit export stability

- **FACT (source: `ifc_inspect.py compare`, real re-export test on `Kingsway Apartments - 1 floor test.ifc` vs an unchanged re-export `..._V2.ifc`):** **100% GlobalId match (95/95) and 100% Tag match (95/95)** across all classes (`IfcBeam`, `IfcColumn`, `IfcMember`). Revit's IFC export is GlobalId-stable and Tag-stable for this project/version, when nothing in the model changes. (Note: this contradicts the synthetic fixture's assumption of unstable re-export GUIDs — that fixture was a deliberately pessimistic test case, not a claim about real Revit behavior.)
- Practical implication: GlobalId (and Tag) can be trusted as an identity key **on the Revit side**. The remaining unknown is entirely on SAFI's side — whether Tag survives into SDNF/KISS output, since SAFI can't export IFC to compare GlobalId directly.

## 2026-09-17 (continued) — SAFI import: identity not retained

- **FACT (source: SAFI Member Attributes dialog, direct observation, member Phys #90):** after IFC import, the member's **Name** field is `#5184 : W Shapes:W1` — truncated (the original Revit type name, e.g. "W18X40", is cut off), and the leading number (`5184`) does not match any Revit Tag/GlobalId seen in the source IFC (Tags were in the 1,280,000s). This looks like SAFI's own internal numbering, not a preserved Revit identifier.
- **Implication (RECOMMENDATION):** SAFI does not retain a usable Revit identity (Tag or GlobalId) anywhere after import — not because SAFI can't export IFC, but because it appears to discard/replace the source ID on import itself. **ID-based matching (GlobalId or Tag) is not viable for the SAFI side.** Matching for the comparison tool must rely on **geometry/position** (coordinates, grid reference), which does survive — this doesn't create a new problem, it confirms the plan's existing D-002 choice (geometry-based matching first, ML later) was correct.
- **FACT (source: SAFI Import report, `data/ifc/SAFI report.rtf`, two import runs on the same file):** at 10mm offset tolerance, 57/95 members floating + 22/95 cantilever (83% with a connectivity issue). At a larger tolerance, 53/107 floating + 30/107 cantilever (78%) — member count grew from 95→107 (tolerance increase caused unwanted member splitting), while the problem rate barely improved. This points to a real geometry/connection gap in the source model, not an import-tolerance issue — needs the drafter to confirm by inspecting specific floating members.
- **FACT:** on import, 2 of 4 materials were unrecognized by SAFI (`01 Steel 6x6`, `01 Steel Main Framing` — custom Revit material names not in SAFI's library).

## Still unverified (to check with a sample export)

- ~~IFC schema version~~ — confirmed IFC2X3 for this Revit export (may vary by project/version).
- Model type in the file — confirmed physical-only for this export; whether Revit can also export an analytical model (`IfcStructuralAnalysisModel`, `IfcStructuralCurveMember`, `IfcStructuralPointConnection`) via different export settings is unverified.
- ~~Section profiles and materials~~ — confirmed: materials always present, profiles only on beams (columns/members missing). Root cause unverified — Revit export setting vs. modeling method.
- ~~GlobalId stability when the same Revit model is exported twice~~ — confirmed 100% stable, see above.
- ~~Whether Tag values survive into SAFI~~ — confirmed: no, SAFI discards/replaces source identity on import.
- Whether the ~80% connectivity failure is a real model gap or scope artifact (partial "1 floor test" export) — needs drafter confirmation.
- Whether SAFI's SDNF/KISS/Excel output carries analysis results (utilization, etc.) — not yet tested.

## 2026-09-17 (continued) — Geometry-based matcher: first real result

- **FACT (source: `tools/ifc_inspect/parse_sdnf.py` + `match.py`, real data — Revit physical elements vs. `Safi Export.sdnf`):** a real coordinate transform exists between Revit and SAFI: **`SAFI_x = Revit_y, SAFI_y = -Revit_x`** (a clean 90° rotation, no offset, no scaling), derived from 5 exactly-matching column positions. Z (elevation) matches directly, no transform needed.
- **FACT:** applying that transform, a mutual-best-match geometry matcher (hard filter by category, nearest endpoint pair) matched **47/47 SAFI elements to Revit elements at sub-millimeter precision** (0.0–1.2mm offsets — effectively exact). All beams and columns in the SAFI export matched correctly.
- **48 Revit elements (all `IfcMember`) went unmatched** — this is exactly the count of `IfcMember` elements in the source IFC. Cause unconfirmed: Sultan suspects this may be an export setting/mistake on the SAFI side (not everything selected for export), not necessarily a SAFI limitation. **Not investigated further — deprioritized per Sultan.**
- **Implication (RECOMMENDATION):** this is strong positive evidence for the geometry-based matching approach in §8/§9 of `CLAUDE_INSTRUCTIONS.md` — once the coordinate transform is known, matching is effectively exact, not just "good enough." This meaningfully de-risks Phase 1 (MVP-1).
