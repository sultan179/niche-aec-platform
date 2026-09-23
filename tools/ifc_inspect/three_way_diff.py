"""Three-way diff (plan.md §6/§11): classify each element as unchanged,
changed-in-Revit, changed-in-SAFI, changed-in-both, new, or missing,
by comparing today's report against a saved baseline.
"""
from baseline import load_baseline
from report import build_report

# fields we actually compare - not offset_mm, since that's a match-quality
# number, not a modeling fact the drafter changed
COMPARE_FIELDS = ["revit_section", "revit_material", "safi_section", "safi_material"]


def _norm(v):
    return v if isinstance(v, str) else None


def diff_against_baseline(baseline_df, current_df):
    baseline_by_id = {row["revit_id"]: row for _, row in baseline_df.iterrows() if row["revit_id"]}
    current_by_id = {row["revit_id"]: row for _, row in current_df.iterrows() if row["revit_id"]}

    all_ids = set(baseline_by_id) | set(current_by_id)
    rows = []
    for revit_id in all_ids:
        base, cur = baseline_by_id.get(revit_id), current_by_id.get(revit_id)

        if base is None:
            status = "new"
        elif cur is None:
            status = "missing"
        else:
            revit_changed = (_norm(base["revit_section"]) != _norm(cur["revit_section"])
                              or _norm(base["revit_material"]) != _norm(cur["revit_material"]))
            safi_changed = (_norm(base["safi_section"]) != _norm(cur["safi_section"])
                             or _norm(base["safi_material"]) != _norm(cur["safi_material"]))
            if revit_changed and safi_changed:
                status = "conflict - changed in both"
            elif revit_changed:
                status = "changed in Revit only"
            elif safi_changed:
                status = "changed in SAFI only"
            else:
                status = "unchanged"

        rows.append({"revit_id": revit_id, "three_way_status": status, "baseline": base, "current": cur})

    return rows