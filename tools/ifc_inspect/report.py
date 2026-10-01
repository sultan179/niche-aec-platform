"""MVP-1 reconciliation report (plan.md §7): Excel diff, no baseline yet —
this run establishes the first baseline once the engineer approves it.
"""
import pandas as pd
from match import load_revit, load_safi, match, match_chains, find_ambiguous, explain_unmatched
from section_mapping import check_section

STATUS_BY_SECTION_RESULT = {
    "match": "matched",
    "mismatch": "matched - verify section",
    "unmapped": "matched - no Revit profile to check",
}

CHAIN_STATUS_BY_SECTION_RESULT = {
    "match": "matched (chain)",
    "mismatch": "matched (chain) - verify section",
    "unmapped": "matched (chain) - no Revit profile to check",
}


def chain_section_status(r_sections, s_sections):
    """Section-agreement check for a chain match - a chain match only means the
    segments connect geometrically (shared endpoints), it says nothing about
    section. A clean chain has exactly one distinct section per side; anything
    else (multiple distinct sections on either side, or a real mismatch between
    the two single sections) means the pieces don't actually agree and a human
    should look - the same scrutiny a single-element section mismatch already
    gets, not a free pass just because it's a chain (bug caught by Sultan,
    2026-10-01: a 2-floor Revit column split into 2 SAFI segments with
    different sections still came back "matched (chain)" with no warning).
    """
    safi_inconsistent = len(s_sections) > 1
    revit_inconsistent = len(r_sections) > 1

    if len(r_sections) == 1 and len(s_sections) == 1:
        result = check_section(r_sections[0], s_sections[0])
    elif not r_sections:
        # SAFI's own segments disagreeing with each other is a real finding
        # regardless of whether Revit has a profile to compare against -
        # "no Revit profile to check" must not swallow that (ecc code review,
        # 2026-10-01: this was the exact same silent-swallow bug, one level in)
        result = "mismatch" if safi_inconsistent else "unmapped"
    else:
        result = "mismatch"

    reason = None
    if result == "mismatch" and (revit_inconsistent or safi_inconsistent):
        reason = f"chain sections aren't consistent across segments: revit={r_sections or ['?']}, safi={s_sections}"
    return CHAIN_STATUS_BY_SECTION_RESULT[result], reason


def build_report(revit_path=None, safi_path=None, revit_elements=None):
    # revit_elements: pre-loaded elements (e.g. from match.load_revit_live()) -
    # bypasses the Excel/IFC path entirely when given, skipping revit_path
    if revit_elements is not None:
        revit = {e["id"]: e for e in revit_elements}
    else:
        revit = {e["id"]: e for e in (load_revit(revit_path) if revit_path else load_revit())}
    safi = {e["id"]: e for e in (load_safi(safi_path) if safi_path else load_safi())}
    matched, revit_unmatched, safi_unmatched = match(list(revit.values()), list(safi.values()))
    # more than one same-category candidate was within tolerance for these ids -
    # the pairing wasn't a clean unique choice, flag it instead of looking identical
    # to a confident match (plan.md §7 names "ambiguous" as its own status)
    ambiguous_revit_ids, ambiguous_safi_ids = find_ambiguous(list(revit.values()), list(safi.values()))

    rows = []
    for revit_id, safi_id, offset_m in matched:
        r, s = revit[revit_id], safi[safi_id]
        # section names only need formatting normalization now, not a metric<->imperial
        # dictionary, as long as SAFI's export stays in imperial (see §8: "never rely on string equality")
        result = check_section(r["section"], s["section"])
        is_ambiguous = revit_id in ambiguous_revit_ids or safi_id in ambiguous_safi_ids
        # ambiguity is about match confidence, section result is about section shape -
        # keep both signals visible instead of letting one silently hide the other
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
            "ambiguous": is_ambiguous,
            "reason": "ambiguous: another candidate was also within tolerance for this pairing" if is_ambiguous else None,
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
        status, reason = chain_section_status(r_sections, s_sections)
        rows.append({
            "status": status,
            "revit_id": "; ".join(revit_ids),
            "safi_id": "; ".join(str(i) for i in safi_ids),
            "safi_name": "; ".join(safi[i]["name"] for i in safi_ids),
            "offset_mm": round(offset_m * 1000, 1),
            "revit_section": "; ".join(r_sections),
            "safi_section": "; ".join(s_sections),
            "revit_material": "; ".join(sorted({revit[i]["material"] for i in revit_ids if isinstance(revit[i]["material"], str)})),
            "safi_material": "; ".join(sorted({safi[i]["material"] for i in safi_ids})),
            "ambiguous": False,
            "reason": reason,
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
            "ambiguous": False,
            "reason": explain_unmatched(r, list(safi.values())),
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
            "ambiguous": False,
            "reason": explain_unmatched(s, list(revit.values())),
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