from pathlib import Path
import pandas as pd

OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEEP = ["REF_AREA", "TIME_PERIOD", "TYPE_CRIME", "OBS_VALUE", "UNIT_MEAS", "UNIT_MULT"]

def clean_data(in_path: Path, out_path: Path):
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

def main():
    clean_data(Path("data/processed/delittips_1_2014_2023.parquet"), OUT_DIR / "crime_clean.parquet")
    clean_data(Path("data/processed/delittips_9_2014_2023.parquet"), OUT_DIR / "criminality_clean.parquet")

if __name__ == "__main__":
    main()