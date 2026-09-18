"""Extract SectionMapping candidates from matched pairs (real geometry-verified
data, not a guessed imperial<->metric formula). Per plan.md's labeling workflow:
this proposes candidates; the drafter/engineer must confirm before they're trusted.
"""
from collections import defaultdict
from match import load_revit, load_safi, match

def build_candidates():
    revit = {e["id"]: e for e in load_revit()}
    safi = {e["id"]: e for e in load_safi()}
    matched, _, _ = match(list(revit.values()), list(safi.values()))

    pairs = defaultdict(set)
    for revit_id, safi_id, _ in matched:
        r_section = revit[revit_id]["section"]
        r_section = r_section if isinstance(r_section, str) else "(no Revit profile)"
        s_section = safi[safi_id]["section"]
        pairs[r_section].add(s_section)

    consistent, ambiguous = {}, {}
    for r_section, s_sections in pairs.items():
        if len(s_sections) == 1:
            consistent[r_section] = next(iter(s_sections))
        else:
            ambiguous[r_section] = s_sections

    return consistent, ambiguous


if __name__ == "__main__":
    consistent, ambiguous = build_candidates()
    print(f"Consistent candidates ({len(consistent)}):")
    for r, s in sorted(consistent.items()):
        print(f"  {r!r:25s} -> {s!r}")
    if ambiguous:
        print(f"\nAmbiguous ({len(ambiguous)}) — same Revit section matched multiple SAFI sections:")
        for r, s_set in ambiguous.items():
            print(f"  {r!r}: {s_set}")