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

MATCH_TOL_M = 0.5  # default acceptance tolerance, shared by match(), find_ambiguous(), explain_unmatched(), match_chains()


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


def match(revit_elements, safi_elements, tolerance_m=MATCH_TOL_M):
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


def _ids_with_multiple_candidates(elements, other_side, tolerance_m):
    ids = set()
    for e in elements:
        candidates = [o for o in other_side if o["category"] == e["category"]]
        within = [o for o in candidates if pair_distance(e, o) <= tolerance_m]
        if len(within) >= 2:
            ids.add(e["id"])
    return ids


def find_ambiguous(revit_elements, safi_elements, tolerance_m=MATCH_TOL_M):
    """Ids that have more than one same-category candidate within tolerance
    on the other side. A mutual-best match might confidently pick one, but
    if a second candidate was also close enough to accept, it wasn't a
    clean unique choice and a human should double check it.
    """
    ambiguous_revit_ids = _ids_with_multiple_candidates(revit_elements, safi_elements, tolerance_m)
    ambiguous_safi_ids = _ids_with_multiple_candidates(safi_elements, revit_elements, tolerance_m)
    return ambiguous_revit_ids, ambiguous_safi_ids


def explain_unmatched(element, other_side_elements, tolerance_m=MATCH_TOL_M):
    """Deterministic reason `element` has no match among other_side_elements."""
    candidates = [o for o in other_side_elements if o["category"] == element["category"]]
    if not candidates:
        return f"no {element['category']} elements exist on the other side"

    nearest = min(candidates, key=lambda o: pair_distance(element, o))
    d = pair_distance(element, nearest)
    if d > tolerance_m:
        return f"nearest candidate is {d:.2f}m away, exceeds {tolerance_m:.2f}m tolerance"
    # don't claim the candidate "matched someone else" - it may have lost its own tie-break and be unmatched too
    return f"nearest candidate {nearest['id']} is within tolerance ({d:.2f}m) but wasn't a mutual best match"


# --- chain matching (1:N / N:N): handles cases where a real small gap in the
# source model - e.g. a secondary member framing in without landing exactly on
# a beam - causes SAFI to split one Revit run into a different number of
# segments (see docs/evidence/safi-integration.md, 2026-09-22). ---

JOIN_TOL_M = 0.01  # real internal connections in this data are exact to sub-mm; this just absorbs float noise


def build_chains(elements, join_tol_m=JOIN_TOL_M):
    """Group same-category elements into connected runs via shared endpoints.
    Returns a list of {"ids": [...], "category": ..., "outer_points": [...]}.
    A normal run has exactly 2 outer points (the two free ends).
    """
    from collections import defaultdict

    by_category = defaultdict(list)
    for e in elements:
        by_category[e["category"]].append(e)

    chains = []
    for category, els in by_category.items():
        parent = {e["id"]: e["id"] for e in els}

        def find(x):
            while parent[x] != x:
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for i, a in enumerate(els):
            for b in els[i + 1:]:
                if (dist(a["start"], b["start"]) <= join_tol_m or
                        dist(a["start"], b["end"]) <= join_tol_m or
                        dist(a["end"], b["start"]) <= join_tol_m or
                        dist(a["end"], b["end"]) <= join_tol_m):
                    union(a["id"], b["id"])

        groups = defaultdict(list)
        for e in els:
            groups[find(e["id"])].append(e)

        for group in groups.values():
            point_count = defaultdict(int)

            def key(p, decimals=3):
                return tuple(round(v, decimals) for v in p)

            for e in group:
                point_count[key(e["start"])] += 1
                point_count[key(e["end"])] += 1
            outer_points = [p for p, c in point_count.items() if c == 1]
            chains.append({
                "ids": [e["id"] for e in group],
                "category": category,
                "outer_points": outer_points,
            })
    return chains


def chain_distance(a, b):
    # only a simple run (exactly 2 free ends) has a well-defined span to compare
    if len(a["outer_points"]) != 2 or len(b["outer_points"]) != 2:
        return None
    p1, p2 = a["outer_points"]
    q1, q2 = b["outer_points"]
    straight = dist(p1, q1) + dist(p2, q2)
    flipped = dist(p1, q2) + dist(p2, q1)
    return min(straight, flipped)


def match_chains(revit_elements, safi_elements, tolerance_m=MATCH_TOL_M):
    """Match leftover (already-unmatched) elements at the chain level.
    Skips the case where both chains are single elements - that's exactly
    what match() already tried and failed."""
    revit_chains = build_chains(revit_elements)
    safi_chains = build_chains(safi_elements)

    matched_chains = []
    used_safi = set()
    for rc in revit_chains:
        candidates = [
            (si, sc) for si, sc in enumerate(safi_chains)
            if sc["category"] == rc["category"] and si not in used_safi
            and not (len(rc["ids"]) == 1 and len(sc["ids"]) == 1)
        ]
        best_si, best_sc, best_d = None, None, None
        for si, sc in candidates:
            d = chain_distance(rc, sc)
            if d is not None and (best_d is None or d < best_d):
                best_si, best_sc, best_d = si, sc, d
        if best_sc is not None and best_d <= tolerance_m:
            matched_chains.append((rc["ids"], best_sc["ids"], best_d))
            used_safi.add(best_si)

    return matched_chains


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