"""Parse a SAFI SDNF export (Packet 10 = linear members) into plain records.
Format reverse-engineered from a real export — see docs/evidence/safi-integration.md.
"""
import re

# SAFI can export SDNF in either unit - the file declares which one on its own
# units line (e.g. '"millimeters" 48' or '"inches" 48'), so read that instead
# of assuming millimeters always.
UNIT_TO_METRES = {"millimeters": 0.001, "inches": 0.0254}


def parse_sdnf(path):
    try:
        with open(path) as f:
            lines = [l.rstrip("\n") for l in f]
    except FileNotFoundError:
        raise FileNotFoundError(
            f"SDNF export not found at {path!r} — did you re-export it from SAFI?"
        )

    unit_scale = None
    members = []
    i = 0
    while i < len(lines):
        line = lines[i]

        m_units = re.match(r'^"(\w+)" \d+$', line)
        if m_units and m_units.group(1) in UNIT_TO_METRES:
            unit_scale = UNIT_TO_METRES[m_units.group(1)]
            i += 1
            continue

        m = re.match(r'^(\d+) 10 0 0 "(\w+)" "(.+?)" 1$', line)
        if not m:
            i += 1
            continue

        if unit_scale is None:
            raise ValueError(
                f"SDNF record at line {i + 1}: no recognized units line "
                f"(e.g. '\"millimeters\" 48') found before the first member record"
            )

        piece_id, category, name = m.groups()
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
            "piece_id": piece_id,    # the SDNF record number - the only guaranteed-unique key;
                                      # safi_name can repeat across pieces (seen in real data)
            "safi_name": name,       # e.g. "#114 : HSS Square-C" — SAFI's own numbering, not Revit's
            "category": category,    # "Beam" or "Column"
            "section": section,
            "material": material,
            "start_m": (sx * unit_scale, sy * unit_scale, sz * unit_scale),
            "end_m": (ex * unit_scale, ey * unit_scale, ez * unit_scale),
        })
        i += 6  # each record is 6 lines

    return members


if __name__ == "__main__":
    import sys
    for rec in parse_sdnf(sys.argv[1]):
        print(rec)