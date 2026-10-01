using System.IO;
using System.Windows;
using System.Windows.Controls;
using Autodesk.Revit.DB;
using Microsoft.Win32;

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
        var doc = App.UiApp?.ActiveUIDocument?.Document;
        if (doc == null)
        {
            MessageBox.Show("Open a Revit project first.", "No active document");
            return;
        }

        string? liveGeometryPath = null;
        try
        {
            int droppedCount;
            (liveGeometryPath, droppedCount) = LiveGeometryReader.WriteGeometryFile(doc);

            var rows = await PipelineRunner.RunAsync(SafiPathBox.Text, liveGeometryPath);
            ResultsGrid.ItemsSource = rows;
            _guidToElementId = RevitElementLookup.BuildByGuid(doc);

            // a silently-dropped element would otherwise look identical to a genuine
            // "no Revit source found" row - surface it instead of hiding it (ecc code
            // review, 2026-10-01)
            if (droppedCount > 0)
                MessageBox.Show(
                    $"{droppedCount} structural element(s) were skipped while reading live geometry " +
                    "(unresolved category, or a column missing its Base/Top Level) and won't appear " +
                    "in this report.",
                    "Some elements were skipped");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Reconciliation failed");
        }
        finally
        {
            if (liveGeometryPath != null && File.Exists(liveGeometryPath))
                File.Delete(liveGeometryPath);
        }
    }

    private void BrowseSafiButton_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "SAFI SDNF export (*.sdnf)|*.sdnf|All files (*.*)|*.*",
            Title = "Select SAFI SDNF export",
        };
        if (dialog.ShowDialog() == true)
            SafiPathBox.Text = dialog.FileName;
    }

    private void ResultsGrid_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        var uidoc = App.UiApp?.ActiveUIDocument;
        if (uidoc == null) return;
        if (ResultsGrid.SelectedItem is not ReconciliationRow row) return;
        if (row.RevitGuid == null || !_guidToElementId.TryGetValue(row.RevitGuid, out var elementId)) return;

        uidoc.Selection.SetElementIds(new List<ElementId> { elementId });
    }

    private void ShowUnmatchedButton_Click(object sender, RoutedEventArgs e)
    {
        var uidoc = App.UiApp?.ActiveUIDocument;
        if (uidoc == null) return;
        if (ResultsGrid.ItemsSource is not IEnumerable<ReconciliationRow> rows) return;

        var ids = new List<ElementId>();
        foreach (var row in rows)
        {
            if (row.Status != "matched - verify section" || row.RevitGuid == null) continue;
            if (_guidToElementId.TryGetValue(row.RevitGuid, out var id))
                ids.Add(id);
        }

        uidoc.Selection.SetElementIds(ids);
    }
}
