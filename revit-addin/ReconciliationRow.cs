using System.Text.Json.Serialization;

namespace NicheReconciliation;

// Mirrors one row of tools/ifc_inspect/report.py's build_report() output.
public class ReconciliationRow
{
    [JsonPropertyName("status")]
    public string? Status { get; set; }

    [JsonPropertyName("revit_id")]
    public string? RevitId { get; set; }

    [JsonPropertyName("safi_id")]
    public string? SafiId { get; set; }

    [JsonPropertyName("safi_name")]
    public string? SafiName { get; set; }

    [JsonPropertyName("offset_mm")]
    public double? OffsetMm { get; set; }

    [JsonPropertyName("revit_section")]
    public string? RevitSection { get; set; }

    [JsonPropertyName("safi_section")]
    public string? SafiSection { get; set; }

    [JsonPropertyName("revit_material")]
    public string? RevitMaterial { get; set; }

    [JsonPropertyName("safi_material")]
    public string? SafiMaterial { get; set; }

    [JsonPropertyName("ambiguous")]
    public bool Ambiguous { get; set; }

    [JsonPropertyName("reason")]
    public string? Reason { get; set; }
}
