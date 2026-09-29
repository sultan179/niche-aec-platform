using System.Windows;
using System.Windows.Controls;

namespace NicheReconciliation;

public partial class ReconciliationPane : UserControl
{
    public ReconciliationPane()
    {
        InitializeComponent();
    }

    private void RunButton_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var rows = PipelineRunner.Run(RevitPathBox.Text, SafiPathBox.Text);
            ResultsGrid.ItemsSource = rows;
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Reconciliation failed");
        }
    }
}
