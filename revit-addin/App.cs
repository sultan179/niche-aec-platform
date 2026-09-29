using System.Reflection;
using Autodesk.Revit.UI;

namespace NicheReconciliation;

public class App : IExternalApplication
{
    public static readonly DockablePaneId PaneId = new(new Guid("6d3a1b2e-6f21-4d5e-9c3a-1f2b3c4d5e6f"));

    public Result OnStartup(UIControlledApplication application)
    {
        application.RegisterDockablePane(PaneId, "Niche Reconciliation", new ReconciliationPaneProvider());

        var panel = application.CreateRibbonPanel("Niche Reconciliation");
        var buttonData = new PushButtonData(
            "ShowReconciliationPane",
            "Reconciliation",
            Assembly.GetExecutingAssembly().Location,
            typeof(ShowPaneCommand).FullName);
        panel.AddItem(buttonData);

        return Result.Succeeded;
    }

    public Result OnShutdown(UIControlledApplication application) => Result.Succeeded;
}
