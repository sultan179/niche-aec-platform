"""MVP-1 reconciliation report (plan.md §7): Excel diff, no baseline yet —
this run establishes the first baseline once the engineer approves it.
"""
import pandas as pd
from match import load_revit, load_safi, match
from section_mapping import load_mapping, check_section

STATUS_BY_SECTION_RESULT = {
    "match": "matched",
    "mismatch": "matched - verify section",
    "unmapped": "matched - section not in dictionary",
}


def build_report():
    revit = {e["id"]: e for e in load_revit()}
    safi = {e["id"]: e for e in load_safi()}
    matched, revit_unmatched, safi_unmatched = match(list(revit.values()), list(safi.values()))
    section_mapping = load_mapping()

    rows = []
    for revit_id, safi_id, offset_m in matched:
        r, s = revit[revit_id], safi[safi_id]
        # material names differ by convention (e.g. Revit "01 Steel Main Framing" vs SAFI "A36"),
        # so flag mismatches for a human to check rather than trusting string equality (see §8: "never rely on string equality")
        result = check_section(r["section"], s["section"], section_mapping)
        rows.append({
            "status": STATUS_BY_SECTION_RESULT[result],
            "revit_id": revit_id,
            "safi_id": safi_id,
            "offset_mm": round(offset_m * 1000, 1),
            "revit_section": r["section"],
            "safi_section": s["section"],
            "revit_material": r["material"],
            "safi_material": s["material"],
        })

    for revit_id in revit_unmatched:
        r = revit[revit_id]
        rows.append({
            "status": "missing in SAFI",
            "revit_id": revit_id,
            "safi_id": None,
            "offset_mm": None,
            "revit_section": r["section"],
            "safi_section": None,
            "revit_material": r["material"],
            "safi_material": None,
        })

    for safi_id in safi_unmatched:
        s = safi[safi_id]
        rows.append({
            "status": "no Revit source found",
            "revit_id": None,
            "safi_id": safi_id,
            "offset_mm": None,
            "revit_section": None,
            "safi_section": s["section"],
            "revit_material": None,
            "safi_material": s["material"],
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build_report()
    out = r"C:\Users\SultanArafat\niche-aec-platform\data\ifc\reconciliation_report.xlsx"
    df.to_excel(out, index=False)
    print(df["status"].value_counts())
    print(f"report: {out}")