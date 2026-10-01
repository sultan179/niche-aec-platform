# Niche Reconciliation — Revit add-in (Phase 2)

Dockable pane that runs `tools/ifc_inspect/`'s reconciliation pipeline and
shows the results inside Revit, with row-click highlighting. No approval flow
yet (plan.md §8) — this is still read-only.

## Build

```
dotnet build
```

If it fails on the `RevitAPI`/`RevitAPIUI` references, check that Revit 2026
is installed at `C:\Program Files\Autodesk\Revit 2026`. If not, edit
`RevitInstallDir` in `NicheReconciliation.csproj`.

**Revit must be fully closed to rebuild** — it locks the DLL while the
add-in is loaded (`Access to the path ... is denied` / `MSB3027`). Close
every Revit window, rebuild, then reopen.

## Install (per machine, one-time)

1. Build the project (above) — produces `bin\Debug\net8.0-windows\NicheReconciliation.dll`.
2. Copy `NicheReconciliation.addin` into `%ProgramData%\Autodesk\Revit\Addins\2026\`.
3. Start Revit. Look for a "Niche Reconciliation" ribbon tab with a
   "Reconciliation" button — click it to open the pane. Revit will prompt
   with an "unsigned add-in" security warning the first time (and again
   after every rebuild, unless you choose "Always Load") — this is expected,
   since the DLL isn't code-signed.

## Using the pane

1. **SAFI SDNF path**: a SAFI export, in **imperial** units (required, see
   `docs/state.md`) — type it or use **Browse...** to pick the `.sdnf` file.
2. Click **Run Reconciliation** — reads the live Revit model (see "How it
   runs" below) and populates the results grid. Requires an open document;
   shows an error instead of running if there isn't one.
3. **Click a row** to select/highlight the corresponding Revit element in the
   active view (no zoom/pan, just selection). Rows with no single Revit
   element (chain matches, "no Revit source found") don't highlight anything.
4. **"Highlight All Unmatched Sections"** selects every element whose section
   genuinely disagrees with SAFI (`matched - verify section` status — these
   rows also render in red in the grid) all at once.

## How it runs

- `RunButton_Click` (`ReconciliationPane.xaml.cs`) calls
  `LiveGeometryReader.WriteGeometryFile(doc)`, which reads every Structural
  Column/Framing element **entirely from the live model** — geometry,
  category, identity, and section — bypassing the IFC export/Excel-report
  pipeline completely (2026-10-01). This closed the last gap from the
  column/member section-profile fix: that fix only replaced the *section*
  field; this replaces geometry, category, and identity too, so the whole
  Revit side no longer depends on a stale, manually-regenerated report.
  - **Geometry**: Structural Framing uses `LocationCurve` (straight endpoint
    read). Structural Columns use `LocationPoint` — the real start/end come
    from Base Level/Top Level elevation + offset parameters, not the point
    itself. Confirmed via a real-data investigation before writing this (not
    assumed): every column in this project is `LocationPoint`-based, every
    framing element is `LocationCurve`-based, no other case exists here.
  - **Section**: shared with the (now-fallback) `SectionOverrideReader.cs`
    via `SectionOverrideReader.GetSection()` — same `Section Name Key` /
    `Type.Name`-fallback logic (see the 2026-09-29 fact in `docs/state.md`).
  - **Identity**: `ExportUtils.GetExportId(doc, el.Id)`, same mechanism row
    highlighting already used.
- `PipelineRunner.RunAsync` shells out to `tools/ifc_inspect/run_for_addin.py`
  with this file as `live_geometry_path` (4th positional arg; `revit_path`/
  `section_overrides_path` are always passed as empty strings now — see
  below). When given, `live_geometry_path` takes over entirely —
  `match.py`'s new `load_revit_live()` reads it, applies the same
  `revit_to_safi()` transform and matching logic as the Excel path (verified
  identical matching results against the Excel path on real data before
  building the C# side).
- There is **no more Excel/IFC-report fallback** — `RunButton_Click` requires
  an open document (`doc != null`) and shows an error instead of running if
  there isn't one, since the pane has no other way to get geometry.
  `SectionOverrideReader.WriteOverridesFile()` and `run_for_addin.py`'s
  `apply_section_overrides()` still exist (and are still tested) but aren't
  called from the live flow.
- Clicking a row calls `RevitElementLookup.BuildByGuid(doc)` (built once per
  "Run Reconciliation" click), which maps every column/framing element's
  `ExportUtils.GetExportId` guid to its `ElementId`. The row's `revit_guid`
  (expanded from the compressed IFC GlobalId via `ifcopenshell.guid.expand()`
  in `run_for_addin.py`) looks up that table and calls
  `uidoc.Selection.SetElementIds`.
- `App.UiApp` (needed for the active document/selection, since the pane's
  WPF code has no other way to reach it) is captured via Revit's `Idling`
  event in `OnStartup`, not the ribbon button's click handler — Revit can
  restore a previously-open dockable pane on startup without ever running
  the button's command, so relying on the button click alone left `UiApp`
  null in that case.
