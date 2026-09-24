"""Section comparison (plan.md §8: 'never rely on string equality').
SAFI can export sections in imperial to match Revit's own naming
convention (confirmed 2026-09-24) - once both sides use the same catalog,
the only real difference left is formatting (case, spacing, stray
characters), not a metric<->imperial translation. See
docs/evidence/safi-integration.md for the investigation that established
this - the old imperial<->metric SectionMapping dictionary is no longer
needed as long as SAFI's export stays in imperial.
"""

UNICODE_MULTIPLY = "×"  # "×" - common from copy-pasting a spec sheet/PDF


def normalize_section(s):
    """Normalize formatting-only differences (case, spaces, stray dashes,
    the unicode multiply sign) so W18X40 == w 18x40 == W18×40. Digits,
    decimals, and '/' (e.g. HSS wall thickness) are left untouched - those
    are real, meaningful differences, not formatting noise.
    """
    if not isinstance(s, str):
        return None
    s = s.strip().upper()
    s = s.replace(" ", "")
    s = s.replace(UNICODE_MULTIPLY, "X")
    s = s.replace("-", "")
    return s


def check_section(revit_section, safi_section):
    r_norm = normalize_section(revit_section)
    if r_norm is None:
        return "unmapped"  # no Revit profile to check against (e.g. columns in this export)
    return "match" if r_norm == normalize_section(safi_section) else "mismatch"
