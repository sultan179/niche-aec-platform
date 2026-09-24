"""MVP-1 reconciliation report (plan.md §7): Excel diff, no baseline yet —
this run establishes the first baseline once the engineer approves it.
"""
import pandas as pd
from match import load_revit, load_safi, match, match_chains
from section_mapping import check_section

STATUS_BY_SECTION_RESULT = {
    "match": "matched",
    "mismatch": "matched - verify section",
    "unmapped": "matched - no Revit profile to check",
}


def build_report(revit_path=None, safi_path=None):
    revit = {e["id"]: e for e in (load_revit(revit_path) if revit_path else load_revit())}
    safi = {e["id"]: e for e in (load_safi(safi_path) if safi_path else load_safi())}
    matched, revit_unmatched, safi_unmatched = match(list(revit.values()), list(safi.values()))

    rows = []
    for revit_id, safi_id, offset_m in matched:
        r, s = revit[revit_id], safi[safi_id]
        # section names only need formatting normalization now, not a metric<->imperial
        # dictionary, as long as SAFI's export stays in imperial (see §8: "never rely on string equality")
        result = check_section(r["section"], s["section"])
        rows.append({
            "status": STATUS_BY_SECTION_RESULT[result],
            "revit_id": revit_id,
            "safi_id": safi_id,
            "safi_name": s["name"],
            "offset_mm": round(offset_m * 1000, 1),
            "revit_section": r["section"],
            "safi_section": s["section"],
            "revit_material": r["material"],
            "safi_material": s["material"],
        })

    # some leftovers are really one continuous run split differently on each side
    # (e.g. a real small gap in the source model - see docs/evidence/safi-integration.md
    # 2026-09-22), which a strict 1:1 match can't recognize. Try chain-level matching
    # on what's left before giving up on them.
    revit_leftover = [revit[i] for i in revit_unmatched]
    safi_leftover = [safi[i] for i in safi_unmatched]
    chain_matches = match_chains(revit_leftover, safi_leftover)

    chained_revit_ids, chained_safi_ids = set(), set()
    for revit_ids, safi_ids, offset_m in chain_matches:
        chained_revit_ids.update(revit_ids)
        chained_safi_ids.update(safi_ids)
        r_sections = sorted({revit[i]["section"] for i in revit_ids if isinstance(revit[i]["section"], str)})
        s_sections = sorted({safi[i]["section"] for i in safi_ids})
        rows.append({
            "status": "matched (chain)",
            "revit_id": "; ".join(revit_ids),
            "safi_id": "; ".join(str(i) for i in safi_ids),
            "safi_name": "; ".join(safi[i]["name"] for i in safi_ids),
            "offset_mm": round(offset_m * 1000, 1),
            "revit_section": "; ".join(r_sections),
            "safi_section": "; ".join(s_sections),
            "revit_material": "; ".join(sorted({revit[i]["material"] for i in revit_ids if isinstance(revit[i]["material"], str)})),
            "safi_material": "; ".join(sorted({safi[i]["material"] for i in safi_ids})),
        })

    for revit_id in revit_unmatched:
        if revit_id in chained_revit_ids:
            continue
        r = revit[revit_id]
        rows.append({
            "status": "missing in SAFI",
            "revit_id": revit_id,
            "safi_id": None,
            "safi_name": None,
            "offset_mm": None,
            "revit_section": r["section"],
            "safi_section": None,
            "revit_material": r["material"],
            "safi_material": None,
        })

    for safi_id in safi_unmatched:
        if safi_id in chained_safi_ids:
            continue
        s = safi[safi_id]
        rows.append({
            "status": "no Revit source found",
            "revit_id": None,
            "safi_id": safi_id,
            "safi_name": s["name"],
            "offset_mm": None,
            "revit_section": None,
            "safi_section": s["section"],
            "revit_material": None,
            "safi_material": s["material"],
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        revit_path, safi_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        revit_path, safi_path = None, None
        out = r"C:\Users\SultanArafat\niche-aec-platform\data\ifc\reconciliation_report.xlsx"
    df = build_report(revit_path, safi_path)
    df.to_excel(out, index=False)
    print(df["status"].value_counts())
    print(f"report: {out}")