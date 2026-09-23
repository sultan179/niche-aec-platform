"""Save/load a reconciliation report as a baseline for the three-way diff (plan.md §6).
A baseline is just a report snapshot someone has agreed is correct.
"""
import pandas as pd

BASELINE_PATH = r"C:\Users\SultanArafat\niche-aec-platform\data\ifc\baseline.json"


def save_baseline(df, path=BASELINE_PATH):
    df.to_json(path, orient="records", indent=2)

    
def load_baseline(path=BASELINE_PATH):
    try:
        return pd.read_json(path, orient="records")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"No baseline found at {path!r} — run save_baseline() first"
        )