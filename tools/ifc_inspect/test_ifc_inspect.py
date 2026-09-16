"""Run: python make_fixtures.py && python -m pytest -q test_ifc_inspect.py"""
import pandas as pd
import pytest

import ifc_inspect as ii


@pytest.fixture(scope="module")
def reports(tmp_path_factory):
    d = tmp_path_factory.mktemp("r")
    r = ii.inspect("revit_like.ifc", str(d / "r.xlsx"), True)
    s = ii.inspect("safi_like.ifc", str(d / "s.xlsx"), True)
    return pd.read_excel(r, sheet_name=None), pd.read_excel(s, sheet_name=None), d


def test_physical_endpoints_axis_and_body_fallback(reports):
    phys = reports[0]["Physical"].set_index("Name")
    b1, b2 = phys.loc["B-A-1-2"], phys.loc["B-1-A-B"]
    assert b1.geom_source == "axis" and (b1.start_x_m, b1.end_x_m, b1.start_z_m) == (0.1, 5.9, 3)
    assert b2.geom_source == "body-pca" and b2.length_m == pytest.approx(5.8, abs=1e-3)
    assert b1.profiles == "W310x60" and b1.materials == "S355" and b1.storey == "Level 2"


def test_storeys_and_grids_in_metres(reports):
    assert reports[0]["Storeys"]["elevation_m"].tolist() == [0, 3]
    assert sorted(reports[0]["Grids"]["tag"].astype(str)) == ["1", "2", "A", "B"]


def test_analytical_centerline_split_and_linked(reports):
    an = reports[1]["Analytical"].set_index("Name")
    assert (an.loc["S1a", "start_x_m"], an.loc["S1b", "end_x_m"]) == (0.0, 6.0)  # grid to grid
    assert an.loc["S1a", "linked"] == an.loc["S1b", "linked"]  # 1 physical : 2 analytical
    assert an.loc["N1", "support"] == "IfcBoundaryNodeCondition"


def test_compare_counts(reports):
    d = reports[2]
    m = pd.read_excel(ii.compare("revit_like.ifc", "safi_like.ifc", str(d / "c.xlsx")), sheet_name="Matches")
    assert (m["match"] == "GlobalId").sum() == 1
    assert (m["match"] == "B linked to A physical").sum() == 2
    m2 = pd.read_excel(ii.compare("revit_like.ifc", "revit_like_reexport.ifc", str(d / "c2.xlsx")),
                       sheet_name="Summary")
    assert m2["GlobalId_found_in_B"].sum() == 0  # new GUIDs on re-export are detected
