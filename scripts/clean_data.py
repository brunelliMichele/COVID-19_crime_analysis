from __future__ import annotations
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEEP = ["REF_AREA", "TIME_PERIOD", "TYPE_CRIME", "OBS_VALUE", "UNIT_MEAS", "UNIT_MULT"]

def clean_data(in_path: Path, out_path: Path) -> None:
    """Clean and normalize crime data"""
    print(f"Cleaning {in_path.name}...")

    df = pd.read_parquet(in_path)

    # normalize
    df["REF_AREA"] = df["REF_AREA"].astype(str)
    df["TIME_PERIOD"] = pd.to_numeric(df["TIME_PERIOD"], errors="coerce")
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")

    # filter columns
    cols = [c for c in KEEP if c in df.columns]
    df = df[cols].copy()

    df.to_parquet(out_path, engine="pyarrow", index=False)
    print(f"[OK] {out_path} shape={df.shape}")

def main() -> None:
    files_to_clean = [
        (
            PROJECT_ROOT / "data" / "processed" / "delittips_1_2014_2023.parquet",
            OUT_DIR / "crime_clean.parquet"
        ),
        (
            PROJECT_ROOT / "data" / "processed" / "delittips_9_2014_2023.parquet",
            OUT_DIR / "criminality_clean.parquet"
        ),
    ]

    for in_path, out_path in files_to_clean:
        if not in_path.exists():
            print(f"File not found: {in_path}")
            continue
        clean_data(in_path, out_path)

if __name__ == "__main__":
    main()