# IFC Round-Trip Test Protocol (Phase 0)

**Goal:** find out whether **Revit → IFC → SAFI** removes the manual SAFI rebuild (Problem A), and whether element IDs survive the trip (Problem B).
**Tool:** `ifc_inspect.py`, which reads IFC files and never modifies them.
**Status:** not run yet. All values below are TBD.

---

## 0. Before starting

1. **Agree on pass/fail criteria** with the drafter, and fill them in below *before* the test:

| Criterion | Target |
|---|---|
| IFC import + correction time vs manual rebuild | ≤ ___ % |
| Members that import usable (section, material, connected) | ≥ ___ % |
| Revit GlobalIds still present in SAFI's IFC export | ≥ ___ % (or "not needed") |
| GlobalIds stable when the same model is exported twice | 100 % |

2. **Pick the test scope:** one small, representative project, or one floor of one.
3. **Work on copies only.** Never test on the live Revit or SAFI model.
4. **Record:**
   - Revit version
   - SAFI version and module
   - structural material
   - units
   - whether the Revit model is workshared
5. **Baseline:** how long did the manual SAFI rebuild take for this scope? Mark it as either *measured* or *estimate*.

---

## 1. Revit export

1. Create a 3D view that shows **only structural elements**: columns, framing, foundations, plus floors and walls if SAFI uses them.
2. In the IFC export setup, choose the settings below and save them as **"Niche-SAFI-Test"** so every export uses identical settings. Option names can vary slightly between Revit versions.
   - **IFC version:** IFC4 Reference View. If SAFI import fails, repeat the test with IFC2x3 Coordination View 2.0.
   - **Export only elements visible in view:** ON
   - **Export Revit property sets:** ON
   - **Export base quantities:** ON
   - **Store the IFC GUID in an element parameter after export:** ON (lets us trace GlobalIds back to Revit elements)
3. Export the model as **`R1.ifc`**.
4. Without changing anything, export again as **`R1b.ifc`** (stability check).

---

## 2. SAFI import

1. **Start a timer**, then import `R1.ifc`.
2. Record:
   - what came in (counts by element type)
   - warnings and errors
   - whether members are **connected at nodes** (use SAFI's model check or an analysis run)
   - whether **sections** and **materials** were recognized
   - whether **supports** came in
3. Fix the model until it's ready for analysis. **Log every correction** (what was fixed, which member, how many minutes).
4. **Stop the timer** and save the model as **S1**.

---

## 3. SAFI export

1. Export S1 as **`S1.ifc`**.
2. Without changing anything, export again as **`S1b.ifc`** (stability check).
3. If a hand-built SAFI model of the same project exists, export it as **`S0.ifc`**. That shows what SAFI's export normally contains.

---

## 4. Round-trip edits

1. **In SAFI:** change the section of 1–2 members, save, close, reopen, then export as **`S2.ifc`**. Note which members you changed.
2. **In Revit:** change the type of one beam, then export with the same saved setup as **`R2.ifc`**. Note which beam.

---

## 5. Run the inspector

**Inspect every file:**

```
python ifc_inspect.py inspect R1.ifc
python ifc_inspect.py inspect S1.ifc
python ifc_inspect.py inspect S0.ifc
```

Repeat for the other files. Each run writes a `*_report.xlsx` with these sheets:

- Header (includes schema and originating software)
- Counts
- Storeys
- Grids
- Physical
- Analytical
- Psets

**Compare pairs of files:**

| Command | Question it answers |
|---|---|
| `compare R1.ifc R1b.ifc` | Is Revit's export stable? (expect 100%) |
| `compare S1.ifc S1b.ifc` | Is SAFI's export stable? |
| `compare R1.ifc S1.ifc` | **Do Revit IDs survive into SAFI?** |
| `compare S1.ifc S2.ifc` | Are SAFI IDs stable after edits? |
| `compare R1.ifc R2.ifc` | Are Revit IDs stable after edits? |

`compare` finds matches three ways:

- **GlobalId:** the same GlobalId appears in both files
- **Analytical → physical link:** an analytical member in file B is linked to a physical element in file A
- **Tag:** the same `Tag` value appears in both files (Revit usually writes its element ID into `Tag`; to be verified)

---

## 6. What to look for in the reports

| Question | Where to look |
|---|---|
| IFC version and exporting software | `Header` sheet |
| Does SAFI export physical elements, analytical members, or both? | `Counts` sheet (`IfcBeam` vs `IfcStructuralCurveMember`) |
| Are analytical members linked to physical ones? | `Analytical` sheet, `linked` column |
| Are section names readable, and do they match Revit's? | `profiles` column |
| Physical vs analytical offsets | `start_*` / `end_*` columns: compare Revit and SAFI coordinates for the same member |
| Are members split into segments? | Several analytical rows linked to one physical element |
| Supports | `Analytical` sheet, `support` column |
| Analysis results included? | `Counts` sheet, `IfcStructuralResultGroup` |
| Are grids and levels exported? | `Grids` and `Storeys` sheets |

---

## 7. Results sheet (fill in after the test)

| Item | Result |
|---|---|
| Revit / SAFI versions, material | |
| IFC version used | |
| Import: element counts, warnings | |
| Correction list + total minutes | |
| Manual rebuild baseline (measured / estimate) | |
| Import + correction time as % of rebuild | |
| GlobalId retained, R1 → S1 | |
| Export stability (R1/R1b, S1/S1b) | |
| ID stability after edits (S1/S2, R1/R2) | |
| SAFI export content (physical / analytical / results) | |
| Verdict: full / partial / fail | |

Save the completed results in `docs/evidence/ifc-test-results.md`.

**Data handling:** files stay on company machines. Share only the `*_report.xlsx` outputs, and only if Sultan approves (Instructions §19).
