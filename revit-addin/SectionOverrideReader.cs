using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using Autodesk.Revit.DB;

namespace NicheReconciliation;

public static class SectionOverrideReader
{
    private record SectionEntry(
        [property: JsonPropertyName("guid")] string Guid,
        [property: JsonPropertyName("section")] string Section);

    // Revit's IFC export doesn't carry section profiles for columns or for structural
    // framing exported as IfcMember (braces) - confirmed 2026-09-29, modeled correctly
    // in Revit, empty in every export regardless. This reads the live "Section Name Key"
    // Type parameter instead, writing {guid, section} pairs to a temp file that
    // run_for_addin.py reads to patch rows the IFC path can't fill in. Safe to run over
    // every element here even though only some rows need it - the Python side only
    // patches rows already stuck at "no Revit profile to check".
    public static string WriteOverridesFile(Document doc)
    {
        var categories = new[] { BuiltInCategory.OST_StructuralColumns, BuiltInCategory.OST_StructuralFraming };
        var filter = new ElementMulticategoryFilter(categories);
        var elements = new FilteredElementCollector(doc).WherePasses(filter).WhereElementIsNotElementType();

        var overrides = new List<SectionEntry>();
        foreach (var el in elements)
        {
            var typeId = el.GetTypeId();
            if (typeId == ElementId.InvalidElementId) continue;
            var type = doc.GetElement(typeId);

            // "Section Name Key" is sometimes an unset parameter that Revit's UI still
            // displays a computed value for (confirmed 2026-09-29 via paramHasValue=false
            // on a real element) - Type.Name carries the same designation either way
            var section = type?.LookupParameter("Section Name Key")?.AsString();
            if (string.IsNullOrWhiteSpace(section))
                section = type?.Name;
            if (string.IsNullOrWhiteSpace(section)) continue;

            var guid = ExportUtils.GetExportId(doc, el.Id);
            overrides.Add(new SectionEntry(guid.ToString("N"), section));
        }

        var path = Path.Combine(Path.GetTempPath(), $"niche_section_overrides_{System.Guid.NewGuid():N}.json");
        File.WriteAllText(path, JsonSerializer.Serialize(overrides));
        return path;
    }
}
