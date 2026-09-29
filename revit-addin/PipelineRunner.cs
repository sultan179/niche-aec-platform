using System.Diagnostics;
using System.IO;
using System.Text.Json;

namespace NicheReconciliation;

public static class PipelineRunner
{
    // absolute path, not "python" - Revit's process doesn't see the same PATH a
    // terminal does, and "python" alone resolves to the Windows Store stub instead
    private const string PythonExe = @"C:\Users\SultanArafat\AppData\Local\Python\pythoncore-3.14-64\python.exe";
    private const string RepoRoot = @"C:\Users\SultanArafat\niche-aec-platform";

    public static List<ReconciliationRow> Run(string revitIfcPath, string safiSdnfPath)
    {
        var toolsDir = Path.Combine(RepoRoot, "tools", "ifc_inspect");
        var scriptPath = Path.Combine(toolsDir, "run_for_addin.py");

        var psi = new ProcessStartInfo
        {
            FileName = PythonExe,
            WorkingDirectory = toolsDir,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        psi.ArgumentList.Add(scriptPath);
        psi.ArgumentList.Add(revitIfcPath);
        psi.ArgumentList.Add(safiSdnfPath);

        using var process = Process.Start(psi)
            ?? throw new InvalidOperationException("failed to start the python process");

        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();

        if (process.ExitCode != 0)
            throw new InvalidOperationException($"reconciliation pipeline failed:\n{stderr}");

        return JsonSerializer.Deserialize<List<ReconciliationRow>>(stdout) ?? new List<ReconciliationRow>();
    }
}
