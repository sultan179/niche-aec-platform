"""Unit tests for the column-section-override patching (run_for_addin.py)."""
import json
import ifcopenshell.guid
import pandas as pd
from run_for_addin import apply_section_overrides


def row(status, revit_id="2Pp7MUdlL0aOEVFLrT2DaW", safi_section="HSS6X6X1/2", revit_section=None):
    return {
        "status": status,
        "revit_id": revit_id,
        "safi_id": "1",
        "safi_section": safi_section,
        "revit_section": revit_section,
    }


def write_overrides(tmp_path, pairs):
    path = tmp_path / "overrides.json"
    path.write_text(json.dumps([{"guid": g, "section": s} for g, s in pairs]))
    return str(path)


def test_no_overrides_path_returns_df_unchanged():
    df = pd.DataFrame([row("matched - no Revit profile to check")])
    out = apply_section_overrides(df, None)
    assert out.iloc[0]["status"] == "matched - no Revit profile to check"
    assert pd.isna(out.iloc[0]["revit_section"])


def test_override_patches_matching_section(tmp_path):
    raw_guid = ifcopenshell.guid.expand("2Pp7MUdlL0aOEVFLrT2DaW")
    overrides_path = write_overrides(tmp_path, [(raw_guid, "HSS6X6X1/2")])
    df = pd.DataFrame([row("matched - no Revit profile to check", safi_section="HSS6X6X1/2")])

    out = apply_section_overrides(df, overrides_path)
    assert out.iloc[0]["status"] == "matched"
    assert out.iloc[0]["revit_section"] == "HSS6X6X1/2"


def test_override_flags_real_mismatch(tmp_path):
    raw_guid = ifcopenshell.guid.expand("2Pp7MUdlL0aOEVFLrT2DaW")
    overrides_path = write_overrides(tmp_path, [(raw_guid, "HSS6X6X1/2")])
    df = pd.DataFrame([row("matched - no Revit profile to check", safi_section="HSS8X8X1/2")])

    out = apply_section_overrides(df, overrides_path)
    assert out.iloc[0]["status"] == "matched - verify section"
    assert out.iloc[0]["revit_section"] == "HSS6X6X1/2"


def test_override_never_touches_rows_with_a_real_status(tmp_path):
    # a row that already has a real section comparison result must not be
    # silently overwritten by override data, even if the guid happens to match
    raw_guid = ifcopenshell.guid.expand("2Pp7MUdlL0aOEVFLrT2DaW")
    overrides_path = write_overrides(tmp_path, [(raw_guid, "HSS6X6X1/2")])
    df = pd.DataFrame([row("matched", safi_section="HSS6X6X1/2", revit_section="HSS6X6X1/2")])

    out = apply_section_overrides(df, overrides_path)
    assert out.iloc[0]["status"] == "matched"
    assert out.iloc[0]["revit_section"] == "HSS6X6X1/2"


def test_override_with_no_matching_guid_leaves_row_unchanged(tmp_path):
    unrelated_guid = ifcopenshell.guid.expand("36CK1ojAv5wf$AQ$syw$5p")
    overrides_path = write_overrides(tmp_path, [(unrelated_guid, "HSS6X6X1/2")])
    df = pd.DataFrame([row("matched - no Revit profile to check")])

    out = apply_section_overrides(df, overrides_path)
    assert out.iloc[0]["status"] == "matched - no Revit profile to check"
    assert pd.isna(out.iloc[0]["revit_section"])
