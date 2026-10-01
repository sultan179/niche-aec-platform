using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using Autodesk.Revit.DB;

namespace NicheReconciliation;

// Reads Revit geometry, category, identity, and section directly from the live
// model, bypassing the IFC export/Excel-report pipeline entirely (2026-10-01).
// Confirmed via GeometryProbe investigation: every Structural Column uses
// LocationPoint (needs Base/Top Level + offset to get real endpoints); every
// Structural Framing element uses LocationCurve with a straight Line.
public static class LiveGeometryReader
{
    private record ElementEntry(
        [property: JsonPropertyName("guid")] string Guid,
        [property: JsonPropertyName("category")] string Category,
        [property: JsonPropertyName("section")] string? Section,
        [property: JsonPropertyName("start_m")] double[] StartM,
        [property: JsonPropertyName("end_m")] double[] EndM);

    private const double FeetToMetres = 0.3048;

    // ToSharedCoordinates only applies a pure translation, which is only correct
    // when the project has zero rotation (confirmed true for every project tested
    // so far). Check it once up front and fail loudly instead of silently handing
    // back wrong coordinates on a future rotated project - a silent-wrong-answer
    // report is worse than a crash here, since drafter trust in the report (G1)
    // is the entire point of this tool (ecc code review, 2026-10-01).
    private const double AngleToleranceRad = 1e-6;

    private static void AssertNoRotation(Document doc)
    {
        var angle = doc.ActiveProjectLocation.GetProjectPosition(XYZ.Zero).Angle;
        if (Math.Abs(angle) > AngleToleranceRad)
            throw new InvalidOperationException(
                $"This project's coordinate system is rotated ({angle:F6} rad) relative to true " +
                "north. Live geometry extraction only supports unrotated projects right now - " +
                "ToSharedCoordinates() would need a rotation term added, not just a translation.");
    }

    public static (string Path, int DroppedCount) WriteGeometryFile(Document doc)
    {
        AssertNoRotation(doc);

        var categories = new[] { BuiltInCategory.OST_StructuralColumns, BuiltInCategory.OST_StructuralFraming };
        var filter = new ElementMulticategoryFilter(categories);
        var elements = new FilteredElementCollector(doc).WherePasses(filter).WhereElementIsNotElementType();

        var entries = new List<ElementEntry>();
        var droppedCount = 0;
        foreach (var el in elements)
        {
            // category names confirmed via GeometryProbe against the real model -
            // not guessing at BuiltInCategory enum/ElementId conversion
            string? category = el.Category?.Name switch
            {
                "Structural Columns" => "Column",
                "Structural Framing" => "Beam",
                _ => null,
            };
            if (category == null) { droppedCount++; continue; }

            var points = GetEndpoints(doc, el);
            if (points == null) { droppedCount++; continue; }
            var (start, end) = points.Value;

            var guid = ExportUtils.GetExportId(doc, el.Id);
            var section = SectionOverrideReader.GetSection(doc, el);
            var sharedStart = ToSharedCoordinates(doc, start);
            var sharedEnd = ToSharedCoordinates(doc, end);
            entries.Add(new ElementEntry(
                guid.ToString("N"), category, section,
                new[] { sharedStart.X * FeetToMetres, sharedStart.Y * FeetToMetres, sharedStart.Z * FeetToMetres },
                new[] { sharedEnd.X * FeetToMetres, sharedEnd.Y * FeetToMetres, sharedEnd.Z * FeetToMetres }));
        }

        var path = Path.Combine(Path.GetTempPath(), $"niche_live_geometry_{System.Guid.NewGuid():N}.json");
        File.WriteAllText(path, JsonSerializer.Serialize(entries));
        return (path, droppedCount);
    }

    // LocationCurve/LocationPoint return internal/project coordinates, but the
    // previously-working IFC path used Shared Coordinates (confirmed via a real
    // 85m mismatch on first live test, 2026-10-01). First attempt used
    // ProjectLocation.GetProjectPosition() (Angle/EastWest/NorthSouth/Elevation) -
    // wrong mechanism, its offsets didn't match the empirically-measured constant
    // delta between internal and shared coordinates at all. Real fix, verified via
    // reflection: the Survey Point element's own Position (internal) and
    // SharedPosition (shared) properties give the exact translation needed -
    // AssertNoRotation() above guarantees this pure translation is valid before
    // we get here.
    private static XYZ ToSharedCoordinates(Document doc, XYZ internalPoint)
    {
        var surveyPoint = BasePoint.GetSurveyPoint(doc);
        var offset = surveyPoint.SharedPosition - surveyPoint.Position;
        return internalPoint + offset;
    }

    private static (XYZ start, XYZ end)? GetEndpoints(Document doc, Element el)
    {
        if (el.Location is LocationCurve lc)
            return (lc.Curve.GetEndPoint(0), lc.Curve.GetEndPoint(1));

        if (el.Location is LocationPoint lp)
        {
            var baseLevel = doc.GetElement(el.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsElementId() ?? ElementId.InvalidElementId) as Level;
            var topLevel = doc.GetElement(el.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.AsElementId() ?? ElementId.InvalidElementId) as Level;
            if (baseLevel == null || topLevel == null) return null;

            var baseOffset = el.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM)?.AsDouble() ?? 0;
            var topOffset = el.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)?.AsDouble() ?? 0;

            var start = new XYZ(lp.Point.X, lp.Point.Y, baseLevel.Elevation + baseOffset);
            var end = new XYZ(lp.Point.X, lp.Point.Y, topLevel.Elevation + topOffset);
            return (start, end);
        }

        return null;
    }
}
