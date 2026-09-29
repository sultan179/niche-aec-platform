"""JSON entrypoint for the Revit add-in. Same pipeline as report.py, just
machine-readable stdout instead of an .xlsx file, so the C# side can parse it.

Usage: python run_for_addin.py <revit_ifc_path> <safi_sdnf_path>
"""
import sys
from report import build_report


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    revit_path, safi_path = (argv[0], argv[1]) if len(argv) >= 2 else (None, None)
    df = build_report(revit_path, safi_path)
    # df.to_json (not json.dumps(df.to_dict())) - stdlib json.dumps emits a bare
    # NaN token for missing values, which isn't valid JSON and .NET's parser rejects
    print(df.to_json(orient="records"))


if __name__ == "__main__":
    main()
