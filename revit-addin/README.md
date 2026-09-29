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

1. **Revit report path**: an `.xlsx` file from `python ifc_inspect.py inspect
   <ifc_file>` (run manually beforehand — see the main project README/CLAUDE.md
   for that command). This is *not* the raw IFC file.
2. **SAFI SDNF path**: a SAFI export, in **imperial** units (required, see
   `docs/state.md`).
3. Click **Run Reconciliation** — populates the results grid.
4. **Click a row** to select/highlight the corresponding Revit element in the
   active view (no zoom/pan, just selection). Rows with no single Revit
   element (chain matches, "no Revit source found") don't highlight anything.

## How it runs

- `RunButton_Click` (`ReconciliationPane.xaml.cs`) first calls
  `SectionOverrideReader.WriteOverridesFile(doc)`, which reads every
  Structural Column/Framing element's **live** section (`Section Name Key`
  Type parameter, falling back to the Type's own name if that parameter has
  no stored value) directly from the open document, and writes it to a temp
  JSON file. This exists because **Revit's IFC exporter doesn't carry section
  profiles for columns or for framing exported as `IfcMember`** (confirmed
  2026-09-29 — modeled correctly, empty in every IFC export regardless).
- `PipelineRunner.Run` then shells out to `tools/ifc_inspect/run_for_addin.py`
  (a JSON wrapper around `report.py`'s `build_report()`), passing the Revit
  report path, SAFI path, and that overrides file path.
  `apply_section_overrides()` patches only the rows still stuck at "no Revit
  profile to check" with the live data — never overwrites a real comparison.
- The returned rows bind to the results grid. Note: **geometry, category, and
  Revit-side element identity still come from the Revit report** (the IFC
  export → `ifcopenshell` pipeline), not a live read — only the section field
  was replaced. See `docs/state.md` for the open question of making the rest
  live too.
- Clicking a row calls `SectionOverrideReader`'s sibling,
  `RevitElementLookup.BuildByGuid(doc)` (built once per "Run Reconciliation"
  click), which maps every column/framing element's `ExportUtils.GetExportId`
  guid to its `ElementId`. The row's `revit_guid` (expanded from the
  compressed IFC GlobalId via `ifcopenshell.guid.expand()` in
  `run_for_addin.py`) looks up that table and calls
  `uidoc.Selection.SetElementIds`.
- `App.UiApp` (needed for the active document/selection, since the pane's
  WPF code has no other way to reach it) is captured via Revit's `Idling`
  event in `OnStartup`, not the ribbon button's click handler — Revit can
  restore a previously-open dockable pane on startup without ever running
  the button's command, so relying on the button click alone left `UiApp`
  null in that case.
