using System.Reflection;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;

namespace NicheReconciliation;

public class App : IExternalApplication
{
    public static readonly DockablePaneId PaneId = new(new Guid("6d3a1b2e-6f21-4d5e-9c3a-1f2b3c4d5e6f"));

    // the pane's WPF code has no other way to reach the active document for row-click
    // selection. ShowPaneCommand only runs on an actual button click, but Revit can
    // restore a dockable pane's visibility on startup without one - Idling always
    // fires once the UI is up, regardless, and hands us a live UIApplication via sender
    public static UIApplication? UiApp;

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

        application.Idling += OnIdling;

        return Result.Succeeded;
    }

    private void OnIdling(object? sender, IdlingEventArgs e)
    {
        if (sender is not UIApplication uiApp) return;
        UiApp = uiApp;
        uiApp.Idling -= OnIdling;
    }

    public Result OnShutdown(UIControlledApplication application) => Result.Succeeded;
}
