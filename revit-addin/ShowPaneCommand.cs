using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace NicheReconciliation;

[Transaction(TransactionMode.ReadOnly)]
public class ShowPaneCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        var pane = commandData.Application.GetDockablePane(App.PaneId);
        if (pane.IsShown())
            pane.Hide();
        else
            pane.Show();
        return Result.Succeeded;
    }
}
