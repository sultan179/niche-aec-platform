# Evidence: SAFI integration

## 2026-09-16

- **FACT (source: email from SAFI support, 2026-09-16):** SAFI has **no API**.
- **Reported by Sultan** (source to confirm): SAFI **can export IFC**.
- The test plan is in `docs/evidence/ifc-test-protocol.md`, run with `ifc_inspect.py`. The tool was tested on synthetic files only; it hasn't run on real Revit or SAFI exports yet.

**Already known** (source: safi.com, 2026-09-15):

- SAFI can import IFC.
- SAFI exports DXF, SDNF, and KISS formats.
- Reports can be saved as Excel, Access, or ASCII.

## Implication (RECOMMENDATION)

- SAFI integration will be file-based. IFC export is the main data path; Excel or Access reports are a secondary path for analysis results such as utilization, which IFC likely doesn't carry (HYPOTHESIS).

## Still unverified (to check with a sample export)

- IFC schema version: IFC2x3, IFC4, or IFC4.3.
- Model type in the file:
  - **physical**: `IfcBeam` / `IfcColumn`
  - **analytical**: `IfcStructuralAnalysisModel`, `IfcStructuralCurveMember`, `IfcStructuralPointConnection`
- Section profiles (`IfcProfileDef` names) and materials.
- GlobalId stability when the same model is exported twice.
- **Round trip:** does a GlobalId from Revit survive Revit IFC → SAFI import → SAFI IFC export?
- Units, coordinate origin, and whether levels are exported (`IfcBuildingStorey`).
- Whether any analysis or design results are included.
