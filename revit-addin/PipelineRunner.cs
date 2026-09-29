using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text.Json;

namespace NicheReconciliation;

public static class PipelineRunner
{
    // absolute path, not "python" - Revit's process doesn't see the same PATH a
    // terminal does, and "python" alone resolves to the Windows Store stub instead.
    // Single-machine dev setup for now - update this if it doesn't match the machine.
    private const string PythonExe = @"C:\Users\SultanArafat\AppData\Local\Python\pythoncore-3.14-64\python.exe";
    private static readonly string RepoRoot = GetRepoRoot();

    // bin/Debug/net8.0-windows -> revit-addin -> repo root
    private static string GetRepoRoot()
    {
        var assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!;
        return Path.GetFullPath(Path.Combine(assemblyDir, "..", "..", "..", ".."));
    }

    public static async Task<List<ReconciliationRow>> RunAsync(string revitIfcPath, string safiSdnfPath, string? sectionOverridesPath = null)
    {
        if (!File.Exists(PythonExe))
            throw new InvalidOperationException(
                $"Python interpreter not found at {PythonExe} - update PipelineRunner.PythonExe to match this machine's install.");

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
        if (!string.IsNullOrEmpty(sectionOverridesPath))
            psi.ArgumentList.Add(sectionOverridesPath);

        using var process = Process.Start(psi)
            ?? throw new InvalidOperationException("failed to start the python process");

        // read both streams concurrently, not sequentially - if the child fills the
        // stderr pipe buffer while we're still blocked reading all of stdout (or vice
        // versa), sequential ReadToEnd() calls deadlock: the child can't write more
        // until we drain it, but we won't get there until the first stream finishes
        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();
        await Task.WhenAll(stdoutTask, stderrTask);
        await process.WaitForExitAsync();

        if (process.ExitCode != 0)
            throw new InvalidOperationException($"reconciliation pipeline failed:\n{stderrTask.Result}");

        return JsonSerializer.Deserialize<List<ReconciliationRow>>(stdoutTask.Result) ?? new List<ReconciliationRow>();
    }
}
