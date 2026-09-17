# IFC Round-Trip Test Results

Completed results sheet for `docs/evidence/ifc-test-protocol.md`, run on `Kingsway Apartments - 1 floor test.ifc` (2026-09-17). The protocol's exact method (`compare R1.ifc S1.ifc`) couldn't run as written since SAFI has no IFC export — see notes below each row.

| Item | Result |
|---|---|
| Revit / SAFI versions, material | Revit 26.4.10.51 (original export); 26.0.4.409 (host app during an unrelated linked-file mixup). SAFI version: TBD. Material: structural steel (A36 + 2 unrecognized custom names). |
| IFC version used | IFC2X3, CoordinationView 2.0. |
| Import: element counts, warnings | 95 physical elements imported (24 beam, 23 column, 48 `IfcMember`) → 95-107 SAFI members depending on connectivity tolerance. 2/4 materials unrecognized by SAFI. |
| Correction list + total minutes | Not measured — deprioritized in favor of the comparison-tool goal (D-005) over time-savings measurement. |
| Manual rebuild baseline (measured/estimate) | Not measured — deprioritized, same reason. |
| Import + correction time as % of rebuild | TBD (depends on the two rows above). |
| GlobalId retained, R1 → S1 | **0%.** SAFI has no IFC export at all (confirmed via its Import/Export menu — Export SDNF/KISS/AutoCAD, Import IFC/STAAD only), and internally after import it discards the source Revit GlobalId/Tag entirely, replacing it with SAFI's own numbering (confirmed via the Member Attributes dialog and the SDNF export's Name field). |
| Export stability (R1/R1b, S1/S1b) | R1/R1b: **100% stable** (95/95 GlobalId and Tag match on an unchanged re-export). S1/S1b: not testable — SAFI produces no IFC to compare. |
| ID stability after edits (S1/S2, R1/R2) | Not tested — parked once GlobalId round-trip via IFC was ruled out. |
| SAFI export content (physical/analytical/results) | SDNF export contains **physical member data only** (category, section, material, endpoint geometry) — no analysis results. Excel/Access report content untested. |
| **Verdict: full / partial / fail** | **Fail**, per the §7 outcome scale in `CLAUDE_INSTRUCTIONS.md` — logged as D-013. GlobalId gives zero signal on the SAFI side, so the Niche mapping layer must do all the matching work. |

## What came after the "Fail" verdict

The Fail verdict triggered building the geometry-based matcher the plan's §8 architecture already assumed as the fallback:

- Found an exact coordinate transform between the two systems (90° rotation, no offset: `SAFI_x = Revit_y, SAFI_y = -Revit_x`), derived from 5 real column positions.
- A mutual-best-match geometry matcher (`tools/ifc_inspect/match.py`) matched **47/47 SAFI elements to Revit elements at sub-millimeter precision** using this transform.
- Built a first reconciliation report (`tools/ifc_inspect/report.py`) — all 47 matched pairs got flagged "verify section" because Revit uses imperial section names (`W18X40`) and SAFI uses metric (`W460x60`) for the same physical section. Confirms the plan's existing requirement for a dedicated SectionMapping subsystem (string equality was never going to work).

**Net assessment:** the IFC/GlobalId path specifically failed, but it surfaced the exact transform needed, and geometry-based matching then worked essentially perfectly. The "Fail" verdict is a fail for *this specific hypothesis* (GlobalId matching), not a fail for the overall integration approach.
