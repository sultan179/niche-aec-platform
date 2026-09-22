"""Geometry-based matcher: Revit physical elements <-> SAFI SDNF members.
Baseline per CLAUDE_INSTRUCTIONS.md §8-9: hard filter by category, then
nearest-endpoint mutual-best matching. No ID matching — see D-013.
"""
import math
import pandas as pd
from parse_sdnf import parse_sdnf

REVIT_REPORT = r"C:\Users\SultanArafat\niche-aec-platform\data\ifc\Kingsway Apartments - 1 floor test_report.xlsx"
SAFI_SDNF = r"C:\Users\SultanArafat\niche-aec-platform\data\ifc\Safi Export.sdnf"

# rotation found by comparing real column coordinates: SAFI_x = Revit_y, SAFI_y = -Revit_x
def revit_to_safi(x, y, z):
    return (y, -x, z)

CATEGORY_MAP = {"IfcColumn": "Column", "IfcBeam": "Beam", "IfcMember": "Beam"}  # HYPOTHESIS on IfcMember


def load_revit(path=REVIT_REPORT):
    try:
        df = pd.read_excel(path, sheet_name="Physical")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Revit report not found at {path!r} — run ifc_inspect.py inspect first"
        )
    elements = []
    for _, r in df.iterrows():
        if r["ifc_class"] not in CATEGORY_MAP:
            continue
        start = revit_to_safi(r["start_x_m"], r["start_y_m"], r["start_z_m"])
        end = revit_to_safi(r["end_x_m"], r["end_y_m"], r["end_z_m"])
        elements.append({
            "id": r["GlobalId"],
            "category": CATEGORY_MAP[r["ifc_class"]],
            "section": r["profiles"],
            "material": r["materials"],
            "start": start,
            "end": end,
        })
    return elements


def load_safi(path=SAFI_SDNF):
    try:
        records = parse_sdnf(path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"SAFI export not found at {path!r} — export SDNF from SAFI first"
        )
    elements = []
    for r in records:
        elements.append({
            "id": r["piece_id"],      # SDNF record number - guaranteed unique, unlike safi_name
            "name": r["safi_name"],
            "category": r["category"],
            "section": r["section"],
            "material": r["material"],
            "start": r["start_m"],
            "end": r["end_m"],
        })
    return elements


def dist(p, q):
    return math.dist(p, q)


def pair_distance(a, b):
    # a member's start/end can be flipped relative to the other system, so try both directions
    straight = dist(a["start"], b["start"]) + dist(a["end"], b["end"])
    flipped = dist(a["start"], b["end"]) + dist(a["end"], b["start"])
    return min(straight, flipped)


def match(revit_elements, safi_elements, tolerance_m=0.5):
    # nearest match per side, keep only mutual best (both sides agree it's their closest)
    revit_best = {}
    for a in revit_elements:
        candidates = [b for b in safi_elements if b["category"] == a["category"]]
        if not candidates:
            continue
        best = min(candidates, key=lambda b: pair_distance(a, b))
        revit_best[a["id"]] = (best["id"], pair_distance(a, best))

    safi_best = {}
    for b in safi_elements:
        candidates = [a for a in revit_elements if a["category"] == b["category"]]
        if not candidates:
            continue
        best = min(candidates, key=lambda a: pair_distance(a, b))
        safi_best[b["id"]] = (best["id"], pair_distance(a=best, b=b))

    matched, revit_unmatched, safi_unmatched = [], [], []
    matched_safi_ids = set()
    for revit_id, (safi_id, d) in revit_best.items():
        if safi_best.get(safi_id, (None,))[0] == revit_id and d <= tolerance_m:
            matched.append((revit_id, safi_id, d))
            matched_safi_ids.add(safi_id)
        else:
            revit_unmatched.append(revit_id)

    matched_revit_ids = {m[0] for m in matched}
    for a in revit_elements:
        if a["id"] not in matched_revit_ids and a["id"] not in revit_unmatched:
            revit_unmatched.append(a["id"])
    for b in safi_elements:
        if b["id"] not in matched_safi_ids:
            safi_unmatched.append(b["id"])

    return matched, revit_unmatched, safi_unmatched


if __name__ == "__main__":
    import sys
    revit_path, safi_path = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else (REVIT_REPORT, SAFI_SDNF)
    revit_elements = load_revit(revit_path)
    safi_elements = load_safi(safi_path)
    matched, revit_unmatched, safi_unmatched = match(revit_elements, safi_elements)

    print(f"Revit elements: {len(revit_elements)} | SAFI elements: {len(safi_elements)}")
    print(f"Matched: {len(matched)}")
    for revit_id, safi_id, d in matched:
        print(f"  {revit_id[:8]}...  <->  {safi_id}   (offset {d*1000:.1f} mm)")
    print(f"Revit unmatched: {len(revit_unmatched)}")
    print(f"SAFI unmatched: {len(safi_unmatched)}")