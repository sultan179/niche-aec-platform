"""Parse a SAFI SDNF export (Packet 10 = linear members) into plain records.
Format reverse-engineered from a real export — see docs/evidence/safi-integration.md.
"""
import re

def parse_sdnf(path):
    try:
        with open(path) as f:
            lines = [l.rstrip("\n") for l in f]
    except FileNotFoundError:
        raise FileNotFoundError(
            f"SDNF export not found at {path!r} — did you re-export it from SAFI?"
        )

    members = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^\d+ 10 0 0 "(\w+)" "(.+?)" 1$', line)
        if not m:
            i += 1
            continue

        category, name = m.groups()
        record_start = i  # for error messages

        if i + 2 >= len(lines):
            raise ValueError(f"SDNF record starting at line {record_start + 1} is truncated (file ends early)")

        section_line = lines[i + 1]
        coord_line = lines[i + 2]

        quoted = re.findall(r'"([^"]*)"', section_line)
        if len(quoted) < 2:
            raise ValueError(
                f"SDNF record at line {record_start + 1} ('{name}'): expected section+material "
                f"quoted fields on the next line, got: {section_line!r}"
            )
        section, material = quoted[:2]

        nums = [float(x) for x in coord_line.split()]
        if len(nums) < 9:
            raise ValueError(
                f"SDNF record at line {record_start + 1} ('{name}'): expected >=9 numeric fields "
                f"on the coordinate line, got {len(nums)}: {coord_line!r}"
            )
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