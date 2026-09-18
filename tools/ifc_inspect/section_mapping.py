"""SectionMapping dictionary lookup (plan.md §8: 'its own subsystem,
never rely on string equality'). Every row starts unconfirmed until a
drafter or engineer signs off — see docs/decisions.md.
"""
import csv
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "section_mapping.csv")


def load_mapping(path=None):
    path = path or DEFAULT_PATH
    mapping = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            mapping[row["imperial"]] = row
    return mapping


def check_section(revit_section, safi_section, mapping):
    if not isinstance(revit_section, str) or not revit_section:
        return "unmapped"  # no Revit profile to check against (e.g. columns in this export)
    entry = mapping.get(revit_section)
    if entry is None:
        return "unmapped"
    return "match" if entry["metric"] == safi_section else "mismatch"
