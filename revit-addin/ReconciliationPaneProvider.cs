using Autodesk.Revit.UI;

namespace NicheReconciliation;

public class ReconciliationPaneProvider : IDockablePaneProvider
{
    private readonly ReconciliationPane _pane = new();

    public void SetupDockablePane(DockablePaneProviderData data)
    {
        data.FrameworkElement = _pane;
        data.InitialState = new DockablePaneState
        {
            DockPosition = DockPosition.Right,
        };
    }
}
