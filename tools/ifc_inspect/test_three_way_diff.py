"""Unit tests for the three-way diff (three_way_diff.py)."""
import pandas as pd
from three_way_diff import diff_against_baseline


def row(revit_id, revit_section="W18X40", safi_section="W18X40", ambiguous=False):
    return {
        "revit_id": revit_id,
        "revit_section": revit_section,
        "revit_material": None,
        "safi_section": safi_section,
        "safi_material": None,
        "ambiguous": ambiguous,
    }


def test_ambiguous_in_both_baseline_and_current_is_not_newly_ambiguous():
    baseline_df = pd.DataFrame([row("r1", ambiguous=True)])
    current_df = pd.DataFrame([row("r1", ambiguous=True)])
    rows = diff_against_baseline(baseline_df, current_df)
    r = rows[0]
    assert r["three_way_status"] == "unchanged"
    assert r["currently_ambiguous"] is True
    assert r["newly_ambiguous"] is False


def test_ambiguous_only_in_current_is_newly_ambiguous():
    baseline_df = pd.DataFrame([row("r1", ambiguous=False)])
    current_df = pd.DataFrame([row("r1", ambiguous=True)])
    rows = diff_against_baseline(baseline_df, current_df)
    r = rows[0]
    assert r["currently_ambiguous"] is True
    assert r["newly_ambiguous"] is True


def test_baseline_with_no_ambiguous_column_falls_back_to_false():
    # an old baseline saved before this feature existed - no crash, and every
    # currently-ambiguous row will read as "newly" ambiguous, since the old
    # baseline never recorded ambiguity to compare against (known caveat -
    # re-save the baseline after adding this feature to start clean)
    baseline_df = pd.DataFrame([{
        "revit_id": "r1", "revit_section": "W18X40", "revit_material": None,
        "safi_section": "W18X40", "safi_material": None,
    }])
    current_df = pd.DataFrame([row("r1", ambiguous=True)])
    rows = diff_against_baseline(baseline_df, current_df)
    r = rows[0]
    assert r["three_way_status"] == "unchanged"
    assert r["currently_ambiguous"] is True
    assert r["newly_ambiguous"] is True


def test_new_element_ambiguity_reflects_current_only():
    baseline_df = pd.DataFrame([row("r1")])
    current_df = pd.DataFrame([row("r1"), row("r2", ambiguous=True)])
    rows = diff_against_baseline(baseline_df, current_df)
    r2 = next(r for r in rows if r["revit_id"] == "r2")
    assert r2["three_way_status"] == "new"
    assert r2["currently_ambiguous"] is True
    assert r2["newly_ambiguous"] is True
