"""Inspect IFC exports (Revit / SAFI) and compare identity between two files.

Usage:
  python ifc_inspect.py inspect FILE.ifc [--out report.xlsx] [--no-geom]
  python ifc_inspect.py compare A.ifc B.ifc [--out compare.xlsx]

Requires: pip install ifcopenshell pandas openpyxl numpy
Read-only: never modifies the input files.
"""
import argparse
import sys
from collections import Counter

import numpy as np
import pandas as pd
import ifcopenshell
import ifcopenshell.util.element as uel
import ifcopenshell.util.placement as upl
import ifcopenshell.util.unit as uunit

PHYSICAL = ["IfcBeam", "IfcColumn", "IfcMember", "IfcSlab", "IfcWall", "IfcFooting",
            "IfcPlate", "IfcPile", "IfcBuildingElementProxy"]
ANALYTICAL = ["IfcStructuralCurveMember", "IfcStructuralSurfaceMember",
              "IfcStructuralPointConnection", "IfcStructuralCurveConnection"]
LINEAR = {"IfcBeam", "IfcColumn", "IfcMember", "IfcPile", "IfcStructuralCurveMember"}


def entities(f, types):
    out = []
    for t in types:
        try:
            out += f.by_type(t, include_subtypes=False)
        except RuntimeError:  # type not in this schema (e.g. IFC2x3)
            pass
    return out


# ---------- header / units ----------

def header_info(f, path):
    h = f.header
    fn, fd = h.file_name, h.file_description
    return {
        "file": path,
        "schema": f.schema,
        "view_definition": "; ".join(fd.description),
        "originating_system": fn.originating_system,
        "preprocessor": fn.preprocessor_version,
        "timestamp": fn.time_stamp,
        "length_unit_to_metres": uunit.calculate_unit_scale(f),
    }


# ---------- geometry ----------

def world_matrix(product):
    if getattr(product, "ObjectPlacement", None) is None:
        return np.eye(4)
    return upl.get_local_placement(product.ObjectPlacement)


def xform(m, p, scale):
    p = list(p) + [0.0] * (3 - len(p))
    return (m @ np.array([*p, 1.0]))[:3] * scale


def axis_endpoints(product, scale):
    """Start/end from an 'Axis' representation (Revit exports this for many framing members)."""
    rep = product.Representation
    if not rep:
        return None
    for r in rep.Representations:
        if r.RepresentationIdentifier != "Axis":
            continue
        for item in r.Items:
            pts = None
            if item.is_a("IfcPolyline"):
                pts = [p.Coordinates for p in item.Points]
            elif item.is_a("IfcIndexedPolyCurve"):
                pts = item.Points.CoordList
            if pts and len(pts) >= 2:
                m = world_matrix(product)
                return xform(m, pts[0], scale), xform(m, pts[-1], scale), "axis"
    return None


def topology_endpoints(product, scale):
    """Start/end nodes of an analytical curve member (IfcEdge in a topology representation)."""
    rep = product.Representation
    if not rep:
        return None
    m = world_matrix(product)
    for r in rep.Representations:
        for item in r.Items:
            edge = item.EdgeElement if item.is_a("IfcOrientedEdge") else item
            if edge.is_a("IfcEdge"):
                a = edge.EdgeStart.VertexGeometry.Coordinates
                b = edge.EdgeEnd.VertexGeometry.Coordinates
                return xform(m, a, scale), xform(m, b, scale), "topology"
    return None


def vertex_point(product, scale):
    rep = product.Representation
    if not rep:
        return None
    m = world_matrix(product)
    for r in rep.Representations:
        for item in r.Items:
            if item.is_a("IfcVertexPoint"):
                return xform(m, item.VertexGeometry.Coordinates, scale)
    return None


_geom_settings = None


def body_endpoints(product):
    """Fallback: tessellate the body and take the extent along its principal axis (PCA)."""
    global _geom_settings
    import ifcopenshell.geom
    if _geom_settings is None:
        _geom_settings = ifcopenshell.geom.settings()
        _geom_settings.set("use-world-coords", True)
    shape = ifcopenshell.geom.create_shape(_geom_settings, product)
    v = np.array(shape.geometry.verts).reshape(-1, 3)  # geom output is always metres
    c = v.mean(axis=0)
    axis = np.linalg.svd(v - c, full_matrices=False)[2][0]
    t = (v - c) @ axis
    return c + t.min() * axis, c + t.max() * axis, "body-pca"


def endpoints(product, scale, use_geom):
    res = topology_endpoints(product, scale) if product.is_a("IfcStructuralItem") \
        else axis_endpoints(product, scale)
    if res is None and use_geom and product.is_a() in LINEAR:
        try:
            res = body_endpoints(product)
        except Exception as e:  # geometry kernel can fail on odd shapes
            return None, None, f"geom-failed: {e}"
    return res if res else (None, None, "none")


# ---------- semantics ----------

def material_info(el):
    mat = uel.get_material(el, should_skip_usage=True)
    names, profiles = set(), set()
    if mat is None:
        pass
    elif mat.is_a("IfcMaterial"):
        names.add(mat.Name)
    elif mat.is_a("IfcMaterialProfileSet"):
        for mp in mat.MaterialProfiles:
            if mp.Material:
                names.add(mp.Material.Name)
            if mp.Profile:
                profiles.add(mp.Profile.ProfileName or mp.Profile.is_a())
    elif mat.is_a("IfcMaterialLayerSet"):
        names |= {l.Material.Name for l in mat.MaterialLayers if l.Material}
    elif mat.is_a("IfcMaterialList"):
        names |= {m.Name for m in mat.Materials}
    elif mat.is_a("IfcMaterialConstituentSet"):
        names |= {c.Material.Name for c in mat.MaterialConstituents or [] if c.Material}
    # profile also often lives on the extrusion itself
    if el.Representation:
        for r in el.Representation.Representations:
            for item in r.Items:
                if item.is_a("IfcExtrudedAreaSolid") and item.SweptArea.ProfileName:
                    profiles.add(item.SweptArea.ProfileName)
    return "; ".join(sorted(filter(None, names))), "; ".join(sorted(filter(None, profiles)))


def linked_physical(el):
    """Analytical <-> physical links via IfcRelAssignsToProduct (either direction)."""
    ids = set()
    for rel in getattr(el, "HasAssignments", []) or []:
        if rel.is_a("IfcRelAssignsToProduct"):
            ids.add(rel.RelatingProduct.GlobalId)
    for rel in getattr(el, "ReferencedBy", []) or []:
        if rel.is_a("IfcRelAssignsToProduct"):
            ids |= {o.GlobalId for o in rel.RelatedObjects}
    return "; ".join(sorted(ids))


def element_row(el, scale, use_geom):
    container = uel.get_container(el)
    etype = uel.get_type(el)
    mats, profs = material_info(el)
    a, b, src = endpoints(el, scale, use_geom)
    row = {
        "ifc_class": el.is_a(),
        "GlobalId": el.GlobalId,
        "Name": el.Name,
        "ObjectType": getattr(el, "ObjectType", None),
        "Tag": getattr(el, "Tag", None),
        "type_name": etype.Name if etype else None,
        "predefined": getattr(el, "PredefinedType", None),
        "storey": container.Name if container else None,
        "materials": mats,
        "profiles": profs,
        "linked": linked_physical(el),
        "geom_source": src,
    }
    for k, p in (("start", a), ("end", b)):
        for i, ax in enumerate("xyz"):
            row[f"{k}_{ax}_m"] = round(float(p[i]), 4) if p is not None else None
    row["length_m"] = round(float(np.linalg.norm(b - a)), 4) if a is not None else None
    return row


# ---------- inspect ----------

def inspect(path, out, use_geom):
    f = ifcopenshell.open(path)
    scale = uunit.calculate_unit_scale(f)
    hdr = header_info(f, path)

    counts = Counter(p.is_a() for p in f.by_type("IfcProduct"))
    for t in ("IfcStructuralAnalysisModel", "IfcStructuralLoadGroup", "IfcStructuralResultGroup",
              "IfcRelAssignsToProduct", "IfcGrid", "IfcBuildingStorey"):
        try:
            counts[t] = len(f.by_type(t))
        except RuntimeError:
            pass

    storeys = [{"Name": s.Name, "GlobalId": s.GlobalId,
                "elevation_m": round((s.Elevation or 0) * scale, 4)} for s in f.by_type("IfcBuildingStorey")]

    grids = []
    for g in f.by_type("IfcGrid"):
        m = world_matrix(g)
        for direction in ("UAxes", "VAxes", "WAxes"):
            for ax in getattr(g, direction) or []:
                c = ax.AxisCurve
                pts = [p.Coordinates for p in c.Points] if c.is_a("IfcPolyline") else []
                row = {"grid": g.Name, "dir": direction, "tag": ax.AxisTag}
                if pts:
                    s, e = xform(m, pts[0], scale), xform(m, pts[-1], scale)
                    row.update({"start": np.round(s, 3).tolist(), "end": np.round(e, 3).tolist()})
                grids.append(row)

    rows = [element_row(e, scale, use_geom) for e in entities(f, PHYSICAL)]
    arows = []
    for e in entities(f, ANALYTICAL):
        if e.is_a("IfcStructuralPointConnection"):
            p = vertex_point(e, scale)
            support = e.AppliedCondition.is_a() if e.AppliedCondition else None
            arows.append({"ifc_class": e.is_a(), "GlobalId": e.GlobalId, "Name": e.Name,
                          "support": support, "linked": linked_physical(e),
                          "x_m": None if p is None else round(float(p[0]), 4),
                          "y_m": None if p is None else round(float(p[1]), 4),
                          "z_m": None if p is None else round(float(p[2]), 4)})
        else:
            arows.append(element_row(e, scale, use_geom))

    psets = Counter()
    for e in entities(f, PHYSICAL + ANALYTICAL):
        psets.update(uel.get_psets(e).keys())

    # console summary
    print(f"\n=== {path}")
    for k, v in hdr.items():
        print(f"  {k}: {v}")
    print("  entity counts:")
    for k, v in sorted(counts.items()):
        print(f"    {k}: {v}")
    print(f"  storeys: {len(storeys)} | grid axes: {len(grids)} | physical: {len(rows)} | analytical: {len(arows)}")
    if rows:
        df = pd.DataFrame(rows)
        print(f"  physical with endpoints: {df['start_x_m'].notna().sum()}/{len(df)}"
              f" | with profile: {(df['profiles'] != '').sum()} | with material: {(df['materials'] != '').sum()}")
    if arows:
        print(f"  analytical linked to physical: {sum(1 for r in arows if r['linked'])}/{len(arows)}")
    print(f"  top property sets: {psets.most_common(10)}")

    out = out or path.rsplit(".", 1)[0] + "_report.xlsx"
    with pd.ExcelWriter(out) as xw:
        pd.DataFrame([hdr]).T.rename(columns={0: "value"}).to_excel(xw, sheet_name="Header")
        pd.DataFrame(sorted(counts.items()), columns=["entity", "count"]).to_excel(xw, sheet_name="Counts", index=False)
        pd.DataFrame(storeys).to_excel(xw, sheet_name="Storeys", index=False)
        pd.DataFrame(grids).to_excel(xw, sheet_name="Grids", index=False)
        pd.DataFrame(rows).to_excel(xw, sheet_name="Physical", index=False)
        pd.DataFrame(arows).to_excel(xw, sheet_name="Analytical", index=False)
        pd.DataFrame(psets.most_common(), columns=["pset", "elements"]).to_excel(xw, sheet_name="Psets", index=False)
    print(f"  report: {out}")
    return out


# ---------- compare ----------

def id_table(f):
    return {e.GlobalId: e for e in entities(f, PHYSICAL + ANALYTICAL)}


def compare(path_a, path_b, out):
    fa, fb = ifcopenshell.open(path_a), ifcopenshell.open(path_b)
    ta, tb = id_table(fa), id_table(fb)
    shared = ta.keys() & tb.keys()

    # analytical members in B that point at a physical element whose GlobalId exists in A
    via_link = {}
    for gid, e in tb.items():
        for linked in filter(None, linked_physical(e).split("; ")):
            if linked in ta:
                via_link[gid] = linked

    tags_a = {e.Tag: e for e in ta.values() if getattr(e, "Tag", None)}
    tags_b = {e.Tag: e for e in tb.values() if getattr(e, "Tag", None)}

    rows = []
    for gid in sorted(shared):
        a, b = ta[gid], tb[gid]
        rows.append({"match": "GlobalId", "A_GlobalId": gid, "B_GlobalId": gid,
                     "A_class": a.is_a(), "B_class": b.is_a(), "A_name": a.Name, "B_name": b.Name})
    for gb, ga in sorted(via_link.items()):
        rows.append({"match": "B linked to A physical", "A_GlobalId": ga, "B_GlobalId": gb,
                     "A_class": ta[ga].is_a(), "B_class": tb[gb].is_a(),
                     "A_name": ta[ga].Name, "B_name": tb[gb].Name})
    for tag in sorted(tags_a.keys() & tags_b.keys()):
        a, b = tags_a[tag], tags_b[tag]
        rows.append({"match": f"Tag={tag}", "A_GlobalId": a.GlobalId, "B_GlobalId": b.GlobalId,
                     "A_class": a.is_a(), "B_class": b.is_a(), "A_name": a.Name, "B_name": b.Name})

    by_class_a = Counter(e.is_a() for e in ta.values())
    retained = Counter(ta[g].is_a() for g in shared)
    summary = [{"class_in_A": c, "count_A": n, "GlobalId_found_in_B": retained[c],
                "pct": round(100 * retained[c] / n, 1)} for c, n in sorted(by_class_a.items())]

    print(f"\n=== compare\n  A: {path_a} ({len(ta)} structural entities)\n  B: {path_b} ({len(tb)})")
    print(f"  shared GlobalIds: {len(shared)} ({100 * len(shared) / max(len(ta), 1):.1f}% of A)")
    print(f"  B analytical linked to A physical: {len(via_link)}")
    print(f"  shared Tag values: {len(tags_a.keys() & tags_b.keys())}")
    for s in summary:
        print(f"    {s['class_in_A']}: {s['GlobalId_found_in_B']}/{s['count_A']} ({s['pct']}%)")

    out = out or "compare_report.xlsx"
    with pd.ExcelWriter(out) as xw:
        pd.DataFrame(summary).to_excel(xw, sheet_name="Summary", index=False)
        pd.DataFrame(rows).to_excel(xw, sheet_name="Matches", index=False)
        pd.DataFrame([{"GlobalId": g, "class": ta[g].is_a(), "Name": ta[g].Name}
                      for g in sorted(ta.keys() - shared)]).to_excel(xw, sheet_name="Only_in_A", index=False)
        pd.DataFrame([{"GlobalId": g, "class": tb[g].is_a(), "Name": tb[g].Name}
                      for g in sorted(tb.keys() - shared)]).to_excel(xw, sheet_name="Only_in_B", index=False)
    print(f"  report: {out}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("inspect")
    i.add_argument("file")
    i.add_argument("--out")
    i.add_argument("--no-geom", action="store_true", help="skip body tessellation fallback (faster)")
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--out")
    args = ap.parse_args(argv)
    if args.cmd == "inspect":
        inspect(args.file, args.out, not args.no_geom)
    else:
        compare(args.a, args.b, args.out)


if __name__ == "__main__":
    sys.exit(main())
