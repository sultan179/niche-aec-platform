"""Synthetic IFC files to test ifc_inspect.py (NOT real Niche data).

revit_like.ifc : physical beams/columns, mm units, Axis rep on one beam, body-only on another, grid, storeys
safi_like.ifc  : keeps 1 GlobalId from revit_like, plus an analytical model whose curve members
                 are linked (IfcRelAssignsToProduct) to physical elements.
"""
import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.guid


def base(schema, system):
    f = api.run("project.create_file", version=schema)
    f.header.file_name.originating_system = system
    proj = api.run("root.create_entity", f, ifc_class="IfcProject", name="Test")
    api.run("unit.assign_unit", f, length={"is_metric": True, "raw": "MILLIMETERS"})
    ctx = api.run("context.add_context", f, context_type="Model")
    body = api.run("context.add_context", f, context_type="Model", context_identifier="Body",
                   target_view="MODEL_VIEW", parent=ctx)
    axis = api.run("context.add_context", f, context_type="Model", context_identifier="Axis",
                   target_view="GRAPH_VIEW", parent=ctx)
    site = api.run("root.create_entity", f, ifc_class="IfcSite", name="Site")
    bldg = api.run("root.create_entity", f, ifc_class="IfcBuilding", name="Bldg")
    api.run("aggregate.assign_object", f, products=[site], relating_object=proj)
    api.run("aggregate.assign_object", f, products=[bldg], relating_object=site)
    storeys = []
    for name, elev in (("Level 1", 0.0), ("Level 2", 3000.0)):
        s = api.run("root.create_entity", f, ifc_class="IfcBuildingStorey", name=name)
        s.Elevation = elev
        api.run("aggregate.assign_object", f, products=[s], relating_object=bldg)
        api.run("geometry.edit_object_placement", f, product=s,
                matrix=[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, elev / 1000], [0, 0, 0, 1]])
        storeys.append(s)
    return f, body, axis, storeys


def steel(f):
    mat = api.run("material.add_material", f, name="S355", category="steel")
    prof = f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName="W310x60",
                           OverallWidth=203, OverallDepth=303, WebThickness=7.5, FlangeThickness=13.1)
    pset = api.run("material.add_material_set", f, name="W310x60", set_type="IfcMaterialProfileSet")
    api.run("material.add_profile", f, profile_set=pset, material=mat, profile=prof)
    return pset, prof


def member(f, cls, name, storey, body_ctx, axis_ctx, prof, pset, start, length, direction, with_axis, tag):
    """start in metres; direction is 'X', 'Y' or 'Z'."""
    el = api.run("root.create_entity", f, ifc_class=cls, name=name)
    el.Tag = tag
    api.run("spatial.assign_container", f, products=[el], relating_structure=storey)
    api.run("material.assign_material", f, products=[el], type="IfcMaterialProfileSetUsage", material=pset)
    x, y, z = start
    if direction == "X":
        m = [[0, 0, 1, x], [1, 0, 0, y], [0, 1, 0, z], [0, 0, 0, 1]]  # local Z -> world X
    elif direction == "Y":
        m = [[1, 0, 0, x], [0, 0, 1, y], [0, -1, 0, z], [0, 0, 0, 1]]  # local Z -> world Y
    else:
        m = [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]
    api.run("geometry.edit_object_placement", f, product=el, matrix=m)
    rep = api.run("geometry.add_profile_representation", f, context=body_ctx, profile=prof, depth=length)
    reps = [rep]
    if with_axis:
        line = f.createIfcPolyline([f.createIfcCartesianPoint((0.0, 0.0, 0.0)),
                                    f.createIfcCartesianPoint((0.0, 0.0, length * 1000))])
        reps.append(f.createIfcShapeRepresentation(axis_ctx, "Axis", "Curve3D", [line]))
    el.Representation = f.createIfcProductDefinitionShape(None, None, reps)
    return el


def grid(f, storey, axis_ctx):
    g = api.run("root.create_entity", f, ifc_class="IfcGrid", name="Grid")
    api.run("spatial.assign_container", f, products=[g], relating_structure=storey)
    api.run("geometry.edit_object_placement", f, product=g)
    u = [f.createIfcGridAxis(t, f.createIfcPolyline([f.createIfcCartesianPoint((x, -1000.0)),
                                                     f.createIfcCartesianPoint((x, 7000.0))]), True)
         for t, x in (("1", 0.0), ("2", 6000.0))]
    v = [f.createIfcGridAxis(t, f.createIfcPolyline([f.createIfcCartesianPoint((-1000.0, y)),
                                                     f.createIfcCartesianPoint((7000.0, y))]), True)
         for t, y in (("A", 0.0), ("B", 6000.0))]
    g.UAxes, g.VAxes = u, v


def revit_like(path):
    f, body, axis, (l1, l2) = base("IFC4", "Autodesk Revit (synthetic)")
    pset, prof = steel(f)
    grid(f, l1, axis)
    c1 = member(f, "IfcColumn", "C-A1", l1, body, axis, prof, pset, (0, 0, 0), 3.0, "Z", True, "1001")
    c2 = member(f, "IfcColumn", "C-A2", l1, body, axis, prof, pset, (6, 0, 0), 3.0, "Z", True, "1002")
    # beam cut back to column faces (physical): 0.1 m in from each grid line
    b1 = member(f, "IfcBeam", "B-A-1-2", l2, body, axis, prof, pset, (0.1, 0, 3.0), 5.8, "X", True, "2001")
    b2 = member(f, "IfcBeam", "B-1-A-B", l2, body, axis, prof, pset, (0, 0.1, 3.0), 5.8, "Y", False, "2002")
    f.write(path)
    return {e.Name: e.GlobalId for e in (c1, c2, b1, b2)}


def safi_like(path, keep_ids):
    f, body, axis, (l1, l2) = base("IFC4", "SAFI (synthetic)")
    pset, prof = steel(f)
    b1 = member(f, "IfcBeam", "M1", l2, body, axis, prof, pset, (0.1, 0, 3.0), 5.8, "X", True, None)
    b1.GlobalId = keep_ids["B-A-1-2"]  # simulate a preserved Revit GlobalId
    b2 = member(f, "IfcBeam", "M2", l2, body, axis, prof, pset, (0, 0.1, 3.0), 5.8, "Y", True, None)

    model = api.run("root.create_entity", f, ifc_class="IfcStructuralAnalysisModel", name="Analysis")
    model.PredefinedType = "LOADING_3D"
    topo_ctx = api.run("context.add_context", f, context_type="Model", context_identifier="Reference",
                       target_view="GRAPH_VIEW", parent=api.run("context.add_context", f, context_type="Model"))
    origin = f.createIfcLocalPlacement(None, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0))))

    def node(name, xyz, support=False):
        n = api.run("root.create_entity", f, ifc_class="IfcStructuralPointConnection", name=name)
        n.ObjectPlacement = origin
        v = f.createIfcVertexPoint(f.createIfcCartesianPoint(xyz))
        n.Representation = f.createIfcProductDefinitionShape(None, None, [
            f.createIfcTopologyRepresentation(topo_ctx, "Reference", "Vertex", [v])])
        if support:
            n.AppliedCondition = f.createIfcBoundaryNodeCondition("Pinned")
        return n, v

    # analytical = centerline, grid to grid (0..6000), split at mid node -> 1 physical : 2 analytical
    n1, v1 = node("N1", (0.0, 0.0, 3000.0), True)
    n2, v2 = node("N2", (3000.0, 0.0, 3000.0))
    n3, v3 = node("N3", (6000.0, 0.0, 3000.0), True)
    segs = []
    for name, va, vb in (("S1a", v1, v2), ("S1b", v2, v3)):
        s = api.run("root.create_entity", f, ifc_class="IfcStructuralCurveMember", name=name)
        s.PredefinedType = "RIGID_JOINED_MEMBER"
        s.Axis = f.createIfcDirection((0.0, 0.0, 1.0))
        s.ObjectPlacement = origin
        s.Representation = f.createIfcProductDefinitionShape(None, None, [
            f.createIfcTopologyRepresentation(topo_ctx, "Reference", "Edge", [f.createIfcEdge(va, vb)])])
        api.run("material.assign_material", f, products=[s], type="IfcMaterialProfileSet", material=pset)
        segs.append(s)
    f.createIfcRelAssignsToProduct(ifcopenshell.guid.new(), None, None, None, segs, None, b1)
    f.createIfcRelAssignsToGroup(ifcopenshell.guid.new(), None, None, None, segs + [n1, n2, n3], None, model)
    f.write(path)


if __name__ == "__main__":
    ids = revit_like("revit_like.ifc")
    revit_like("revit_like_reexport.ifc")  # new GUIDs -> simulates unstable re-export
    safi_like("safi_like.ifc", ids)
    print("fixtures written", ids)
