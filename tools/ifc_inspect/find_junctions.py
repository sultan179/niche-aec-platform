"""Find SAFI points where 3+ members meet - evidence of a real connection
point (e.g. a perpendicular beam framing in), checkable without opening SAFI.
"""
from collections import defaultdict
from parse_sdnf import parse_sdnf
import math

TOLERANCE_M = 0.2
SDNF_PATH = r"..\..\data\ifc\Cleaned\2026_05_13_Kingsway_V1 - TEST, 1 floor Connected.sdnf"


def find_junctions(records, decimals=3):
    counts = defaultdict(set)
    for r in records:
        start = tuple(round(v, decimals) for v in r["start_m"])
        end = tuple(round(v, decimals) for v in r["end_m"])
        counts[start].add(r["safi_name"])
        counts[end].add(r["safi_name"])
    return counts


def nearby_members(records, point, tolerance_m=TOLERANCE_M):
    hits = []
    for r in records:
        for end_name, coord in (("start", r["start_m"]), ("end", r["end_m"])):
            if math.dist(coord, point) <= tolerance_m:
                hits.append((r["safi_name"], end_name, coord))
    return hits


if __name__ == "__main__":
    records = parse_sdnf(SDNF_PATH)
    counts = find_junctions(records)
    for point, members in sorted(counts.items()):
        if len(members) >= 3:
            print(f"{point}: {sorted(members)}")

    print("\nProximity check on the two suspected split points (within 200mm):")
    junctions = [(23.7216, -11.6432, 3.9878), (23.0911, -16.0373, 3.9878)]
    for j in junctions:
        hits = nearby_members(records, j)
        print(f"{j}:")
        for name, end, coord in hits:
            print(f"  {name} ({end}) at {coord}, distance {math.dist(coord, j)*1000:.1f}mm")