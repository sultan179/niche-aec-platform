"""JSON entrypoint for the Revit add-in. Same pipeline as report.py, just
machine-readable stdout instead of an .xlsx file, so the C# side can parse it.

Usage: python run_for_addin.py <revit_ifc_path> <safi_sdnf_path> [section_overrides_path]
"""
import sys
import json
import ifcopenshell.guid
from report import build_report, STATUS_BY_SECTION_RESULT
from section_mapping import check_section


def expand_guid(revit_id):
    # only single, non-chain ids expand cleanly - "id1; id2" (chain matches) and
    # None (no Revit source) aren't valid compressed IFC GUIDs
    if not isinstance(revit_id, str) or "; " in revit_id:
        return None
    try:
        return ifcopenshell.guid.expand(revit_id)
    except Exception:
        return None


def apply_section_overrides(df, overrides_path):
    """Revit's IFC exporter doesn't carry section profiles for columns or for structural
    framing exported as IfcMember/braces (confirmed 2026-09-29 - modeled correctly in
    Revit, verified empty in the IFC export regardless). overrides_path is a JSON file
    the add-in writes from a live read of each element's "Section Name Key" Type
    parameter, keyed by the same export guid used elsewhere (see PipelineRunner.cs /
    SectionOverrideReader.cs). Only patches rows still stuck at "no Revit profile to
    check" - never overwrites a real comparison.
    """
    if not overrides_path:
        return df
    with open(overrides_path, encoding="utf-8") as f:
        overrides = json.load(f)
    section_by_revit_id = {ifcopenshell.guid.compress(o["guid"]): o["section"] for o in overrides}

    for idx, row in df.iterrows():
        if row["status"] != "matched - no Revit profile to check":
            continue
        section = section_by_revit_id.get(row["revit_id"])
        if not section:
            continue
        result = check_section(section, row["safi_section"])
        df.at[idx, "revit_section"] = section
        df.at[idx, "status"] = STATUS_BY_SECTION_RESULT[result]
    return df


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    revit_path = argv[0] if len(argv) >= 1 else None
    safi_path = argv[1] if len(argv) >= 2 else None
    overrides_path = argv[2] if len(argv) >= 3 else None
    df = build_report(revit_path, safi_path)
    df = apply_section_overrides(df, overrides_path)
    df["revit_guid"] = df["revit_id"].apply(expand_guid)
    # df.to_json (not json.dumps(df.to_dict())) - stdlib json.dumps emits a bare
    # NaN token for missing values, which isn't valid JSON and .NET's parser rejects
    print(df.to_json(orient="records"))


if __name__ == "__main__":
    main()
