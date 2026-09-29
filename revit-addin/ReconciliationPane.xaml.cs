using System.IO;
using System.Windows;
using System.Windows.Controls;
using Autodesk.Revit.DB;

namespace NicheReconciliation;

public partial class ReconciliationPane : UserControl
{
    private Dictionary<string, ElementId> _guidToElementId = new();

    public ReconciliationPane()
    {
        InitializeComponent();
    }

    private async void RunButton_Click(object sender, RoutedEventArgs e)
    {
        string? sectionOverridesPath = null;
        try
        {
            var doc = App.UiApp?.ActiveUIDocument?.Document;
            sectionOverridesPath = doc != null ? SectionOverrideReader.WriteOverridesFile(doc) : null;

            var rows = await PipelineRunner.RunAsync(RevitPathBox.Text, SafiPathBox.Text, sectionOverridesPath);
            ResultsGrid.ItemsSource = rows;

            _guidToElementId = doc != null ? RevitElementLookup.BuildByGuid(doc) : new Dictionary<string, ElementId>();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Reconciliation failed");
        }
        finally
        {
            if (sectionOverridesPath != null && File.Exists(sectionOverridesPath))
                File.Delete(sectionOverridesPath);
        }
    }

    private void ResultsGrid_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        var uidoc = App.UiApp?.ActiveUIDocument;
        if (uidoc == null) return;
        if (ResultsGrid.SelectedItem is not ReconciliationRow row) return;
        if (row.RevitGuid == null || !_guidToElementId.TryGetValue(row.RevitGuid, out var elementId)) return;

        uidoc.Selection.SetElementIds(new List<ElementId> { elementId });
    }
}
