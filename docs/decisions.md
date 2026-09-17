# Niche AEC Decision Log

All decisions below were reached in the design discussion between Sultan, Claude, and ChatGPT on 2026-09-15.

**Status: APPROVED** (Sultan). **Evidence:** design reasoning only; none are validated by project data yet.

---

### D-001 · Niche identity layer

- **Chosen:** keep a Niche identity and mapping layer between Revit and SAFI.
- **Why:** SAFI may split members, and neither application should own the other's identity.
- **Rejected:** a direct Revit ID → SAFI ID link.
- **Plan impact:** core.

### D-002 · Deterministic matching first

- **Chosen:** rules- and geometry-based matching first. ML only after a labeled dataset exists.
- **Why:** results must be explainable, and there is no training data yet.
- **Rejected:** ML or LLM matching from day one.
- **Plan impact:** core.

### D-003 · Confidence ≠ authority

- **Chosen:** write-back requires a human-confirmed mapping and engineer approval.
- **Why:** engineering safety.
- **Rejected:** automatic write-back for high-confidence matches.
- **Plan impact:** core.

### D-004 · Change Contract with optimistic concurrency

- **Chosen:** the Revit add-in applies only approved contracts, and a contract expires if the model changed after its `base_revision`.
- **Why:** stops stale analysis results from overwriting newer human edits.
- **Plan impact:** core.

### D-005 · Three-way diff

- **Chosen:** compare baseline, current Revit, and current SAFI. The baseline is the first engineer-approved reconciliation.
- **Why:** it's the only way to tell who changed what.
- **Rejected:** a two-way Revit vs SAFI comparison.
- **Plan impact:** core.

### D-006 · Modular monolith with PostgreSQL

- **Chosen:** one backend, PostgreSQL (relational + JSONB), object storage.
- **Why:** complexity at the right size for the MVP.
- **Rejected for now:** microservices, PostGIS, event buses.
- **Plan impact:** core.

### D-007 · Report before UI; Revit-first UX

- **Chosen:** MVP-1 is an Excel/PDF diff. Then a Revit dockable pane. The portal comes later.
- **Why:** fastest value, and the drafter works inside Revit.
- **Rejected:** building the web portal first.
- **Plan impact:** core.

### D-008 · Restricted write-back

- **Chosen:** only section/type swaps can be written back. Position, members, connectivity, bearing, supports, connections, and analytical assumptions stay manual.
- **Why:** engineering safety.
- **Plan impact:** core.

### D-009 · Narrow canonical model

- **Chosen:** the canonical model covers identity, mapping, revisions, approvals, and audit only.
- **Why:** avoid spending years building a BIM ontology.
- **Rejected:** a generalized canonical AEC model.
- **Plan impact:** core.

### D-010 · Phase 0 discovery and IFC/GlobalId first

- **Chosen:** workflow capture, SAFI support, and the IFC round-trip experiment happen before the sync build. The read-only diff runs in parallel.
- **Why:** the results may change the architecture.
- **Plan impact:** core.

### D-011 · Labeling and evaluation

- **Chosen:** the matcher proposes, the drafter confirms or corrects, and evaluation is leave-one-project-out.
- **Why:** labeling everything by hand is too costly.
- **Plan impact:** implementation.

### D-012 · Defer AI grid extraction and multi-agent

- **Chosen:** allow only bounded AI early (section-name suggestions, diff explanations). No multi-agent in the MVP.
- **Why:** grid errors propagate, the payoff is low, and there's no measured need for multiple agents.
- **Plan impact:** core.

### D-013 · G0 verdict: Fail (GlobalId gives no signal via SAFI)

- **Status:** APPROVED (Sultan), 2026-09-17.
- **Evidence:** real test on `Kingsway Apartments - 1 floor test.ifc` (not design reasoning, unlike D-001–D-012). Revit's IFC export is 100% GlobalId/Tag stable on re-export. SAFI is IFC-import-only (no export). SAFI discards the source Revit identity on import — the imported member's Name field shows SAFI's own numbering (`#5184 : W Shapes:W1`, truncated), not the Revit Tag/GlobalId. 78–83% of members come in floating or half-connected. Columns/`IfcMember` elements are missing section profiles; 2/4 materials went unrecognized by SAFI. Full detail: `docs/evidence/safi-integration.md`.
- **Chosen:** G0 = **Fail**, per the §7 outcome scale in `CLAUDE_INSTRUCTIONS.md` — GlobalId isn't usable even as a weak signal on the SAFI side, since nothing of it survives import.
- **Why:** matching must rely entirely on the Niche mapping layer (§8: hard filters, geometry/grid normalization, scoring) — exactly the fallback case that architecture already assumed.
- **Rejected:** Full or Partial verdicts — both require some surviving GlobalId signal, which doesn't exist post-SAFI-import.
- **Plan impact:** none — confirms §8's existing layered matching design was necessary, not a change to `plan.md`.
