"""Parse a SAFI SDNF export (Packet 10 = linear members) into plain records.
Format reverse-engineered from a real export — see docs/evidence/safi-integration.md.
"""
import re

def parse_sdnf(path):
    with open(path) as f:
        lines = [l.rstrip("\n") for l in f]

    members = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^\d+ 10 0 0 "(\w+)" "(.+?)" 1$', line)
        if not m:
            i += 1
            continue

        category, name = m.groups()
        section_line = lines[i + 1]
        coord_line = lines[i + 2]

        section, material = re.findall(r'"([^"]*)"', section_line)[:2]

        nums = [float(x) for x in coord_line.split()]
        # dir_x dir_y dir_z, start_x start_y start_z, end_x end_y end_z, then 2 trailing
        sx, sy, sz, ex, ey, ez = nums[3:9]

        members.append({
            "safi_name": name,       # e.g. "#114 : HSS Square-C" — SAFI's own numbering, not Revit's
            "category": category,    # "Beam" or "Column"
            "section": section,
            "material": material,
            "start_m": (sx / 1000, sy / 1000, sz / 1000),
            "end_m": (ex / 1000, ey / 1000, ez / 1000),
        })
        i += 6  # each record is 6 lines

    return members


if __name__ == "__main__":
    import sys
    for rec in parse_sdnf(sys.argv[1]):
        print(rec)