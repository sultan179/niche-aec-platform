# Niche AEC Platform — Core Plan

**Version:** 0.1 · 2026-09-15
**Status:** DRAFT, awaiting Sultan's approval. Once approved, changes follow the protocol in `CLAUDE_INSTRUCTIONS.md` §23.

---

## 1. Objective

Remove duplicated manual work in the chain **architectural PDF → Revit → SAFI → optimization → Revit revision**, while engineers keep the final engineering authority.

The system is built to production and portfolio standard, and delivered incrementally with measurable results.

---

## 2. Current workflow

The drafter described this workflow in an interview. It still needs to be captured in detail.

1. The drafter receives an architectural PDF from an external architect.
2. He loads the PDF into Revit and models the structure on top of it: gridlines first, then columns, then beams, then other elements.
3. He rebuilds the elements needed for analysis in SAFI.
4. He runs the load analysis and optimizes members for material vs cost.
5. He applies the resulting changes to Revit by hand.
6. He prints both models and ticks off each element to confirm they match.

**What the drafter reported (FACT):**

- Revit and SAFI element IDs don't match.
- Coordinates are close but not identical.
- Gridlines match in both programs.

---

## 3. Problems

| | Problem | Current cost |
|---|---|---|
| **A: Model creation** | The SAFI model is rebuilt by hand from the Revit model | Duplicate modeling (time TBD) |
| **B: Model synchronization** | SAFI results are applied to Revit by hand and checked by print-and-tick | Manual edits plus manual checking (time TBD) |

**Why B is hard:**

- There is no shared ID between the two programs.
- Physical geometry differs from analytical geometry (**HYPOTHESIS**, to be verified).
- SAFI may split one member into several.
- Section names differ between the programs.
- SAFI's automation interface is unknown.

**Priority:** investigate Problem A first. If it is solved, it may save the most time. Problem B is the long-term core of the product.

---

## 4. Conceptual model

**Physical representation (Revit) → Analytical representation (SAFI) → Cross-system identity (Niche) → Reconciliation**

| Party | Role |
|---|---|
| Revit | Physical BIM and drafting representation |
| SAFI | Analytical representation |
| Niche | Identity, sync state, change history, approvals |
| Engineer | Final engineering authority |

---

## 5. Initial architecture

```
Revit Add-in (C#, read-only first)
        │
        ▼
Modular backend: Projects · Snapshots · Identity · Mapping · Diff · Approvals · Audit · Integration
        │
        ├── PostgreSQL (relational + JSONB)
        ├── Object storage (immutable source files and snapshots)
        └── SAFI / IFC adapter
```

**Data model:**

- Project
- Revision / Snapshot
- NicheElement
- ExternalRepresentation
- Mapping (1:1, 1:N, N:1)
- SectionMapping
- ChangeSet (Change Contract)
- Approval
- AuditEvent

**Deferred until a decision gate requires them:**

- microservices
- PostGIS
- web portal
- agent swarms
- a generalized BIM ontology
- event buses

**Open:** backend language (decide at the G1 gate).

---

## 6. Safety boundaries

- **Three-way diff:** compare BASELINE, CURRENT REVIT, and CURRENT SAFI. The baseline is the first engineer-approved reconciliation.
- **Confidence ≠ authority:** a confident match never authorizes a model change.
- **Write-back** is limited to section/type swaps. Each one requires:
  - a human-confirmed mapping
  - engineer approval
  - a valid Change Contract whose base revision matches the current model
  - a successful transaction
  - verification after the change
  - an audit record
- **Always manual:**
  - position
  - member creation or deletion
  - connectivity
  - bearing
  - supports
  - connections
  - analytical assumptions
- **Before any write:** check worksharing ownership, and report exactly which changes succeeded or failed.
- **Client and company data** is never sent to external AI services without approval.

---

## 7. MVP-1: read-only reconciliation report

**Inputs:**

- Revit model, through the read-only extractor
- SAFI export or IFC import path
- section-mapping dictionary

**Output:** an Excel/PDF diff that marks each element as matched, changed, new, missing, ambiguous, or conflict. Each result includes:

- the confidence
- the reason for the match
- the three-way status

**Excluded:** writing to Revit, any UI beyond the report, and the web portal.

**Labeling:**

1. The deterministic matcher proposes matches.
2. The drafter confirms or corrects them.
3. The corrections become the labeled dataset.
4. Evaluate leave-one-project-out.

---

## 8. Roadmap and decision gates

| Phase | Scope | Exit gate |
|---|---|---|
| **0: Discovery / POC** *(current)* | Workflow capture, SAFI support questions, Revit → IFC → SAFI and GlobalId round-trip test, first read-only diff (in parallel) | **G0:** IFC/GlobalId verdict (full / partial / fail) and a proven Revit → SAFI data path on one real project |
| 1: MVP-1 | Reconciliation report on 2–3 projects | **G1:** target precision and recall agreed and met (TBD); the drafter trusts the report |
| 2: Revit review | Dockable pane, highlighting, approval flow | G2: engineer approval workflow accepted |
| 3: Restricted write-back | Section/type swap through the Change Contract, verification after each change | G3: zero unverified writes in pilot |
| 4: Bounded AI | Section-name suggestions, diff explanations | Measured value on the evaluation set |
| 5: Broader AEC | Document intelligence, HVAC/energy team use, other features | Case by case |

**The G0 result may reshape Phases 1–3.** For example, an IFC path could replace most of the manual SAFI rebuild.

---

## 9. Success metrics

All values are TBD until measured.

- Manual SAFI rebuild time: TBD
- IFC import plus correction time: TBD
- Print-and-tick check time: TBD
- Report generation time: TBD
- Matcher precision / recall: TBD
- Discrepancies caught per project: TBD
- Errors found after issue: TBD

---

## 10. Open questions

**For the drafter / engineer:**

- Which material: wood, steel, concrete, or a mix? Which SAFI module?
- What changes after analysis: sizes only, or also positions and members?
- Is Revit's analytical model used?
- How does he create the analytical model?
- Is the Revit model workshared? Which Revit version?
- Which units and coordinate conventions are used?
- Who signs off on structural changes?
- Can he provide a sample SAFI export?
- How long does a manual SAFI rebuild take?
- What exactly does the print-and-tick step check?

**For SAFI support:**

- Is there an API, COM interface, SDK, or batch mode?
- Which import and export formats are supported?
- Can SAFI export IFC, and does IFC import create analytical members?
- Is the IFC GlobalId kept?
- Do member IDs persist across saves?
- Can SAFI store external IDs?
- Which report and export formats are available?
- Are there licensing limits on automation?
