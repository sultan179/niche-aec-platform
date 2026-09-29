# Niche Reconciliation — Revit add-in (Phase 2, read-only first)

Minimal dockable pane that runs `tools/ifc_inspect/`'s reconciliation pipeline
and shows the results inside Revit. No highlighting or approval flow yet —
that comes after this shows real data correctly (plan.md §8).

## Build

```
dotnet build
```

If it fails on the `RevitAPI`/`RevitAPIUI` references, check that Revit 2026
is installed at `C:\Program Files\Autodesk\Revit 2026`. If not, edit
`RevitInstallDir` in `NicheReconciliation.csproj`.

## Install (per machine, one-time)

1. Build the project (above) — produces `bin\Debug\net8.0-windows\NicheReconciliation.dll`.
2. Copy `NicheReconciliation.addin` into `%ProgramData%\Autodesk\Revit\Addins\2026\`.
3. Start Revit. Look for a "Niche Reconciliation" ribbon tab with a
   "Reconciliation" button — click it to open the pane.

## How it runs

The pane's "Run Reconciliation" button shells out to
`tools/ifc_inspect/run_for_addin.py` (a thin JSON wrapper around the same
`build_report()` used by `report.py`), passing the two file paths typed into
the pane, and binds the returned rows to the results grid.
