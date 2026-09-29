using Autodesk.Revit.DB;

namespace NicheReconciliation;

public static class RevitElementLookup
{
    // key: 32-char lowercase hex guid (Guid.ToString("N")), matching run_for_addin.py's
    // ifcopenshell.guid.expand() output format
    public static Dictionary<string, ElementId> BuildByGuid(Document doc)
    {
        var categories = new[] { BuiltInCategory.OST_StructuralColumns, BuiltInCategory.OST_StructuralFraming };
        var filter = new ElementMulticategoryFilter(categories);
        var elements = new FilteredElementCollector(doc).WherePasses(filter).WhereElementIsNotElementType();

        var map = new Dictionary<string, ElementId>();
        foreach (var el in elements)
        {
            var guid = ExportUtils.GetExportId(doc, el.Id);
            map[guid.ToString("N")] = el.Id;
        }
        return map;
    }
}
