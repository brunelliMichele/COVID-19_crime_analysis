from __future__ import annotations
from pathlib import Path
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://esploradati.istat.it/SDMXWS/rest/data"
DATAFLOW_ID = "IT1,73_67_DF_DCCV_DELITTIPS_9,1.0"
DATAFLOW_KEY = "delittips_9"

OUT_RAW = PROJECT_ROOT / "data" / "raw"
OUT_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUT_RAW.mkdir(parents=True, exist_ok=True)
OUT_PROCESSED.mkdir(parents=True, exist_ok=True)

HEADERS = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}

YEARS = list(range(2014, 2024))

def fetch_one_year(year: int, current: int, total: int) -> Path:
    """Fetch crime rate data for specific year from ISTAT APIs."""
    url = f"{BASE_URL}/{DATAFLOW_ID}"
    params = {"startPeriod": str(year), "endPeriod": str(year)}
    out = OUT_RAW / f"{DATAFLOW_KEY}_{year}.csv"

    if out.exists() and out.stat().st_size > 0:
        print(f"[{current}/{total}] {DATAFLOW_KEY} {year} - already exists, skipping")
        return out
    
    print(f"[{current}/{total}] Downloading {year}...")
    r = requests.get(url, params=params, headers=HEADERS, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)
    print(f"[{current}/{total}] {DATAFLOW_KEY} {year} - done ({len(r.content) / 1024:.1f} KB)")
    return out

def load_concat_csv(paths: list[Path]) -> pd.DataFrame:
    """Load and concatenate CSV files, removing duplicates"""
    dfs = []
    for p in paths:
        dfs.append(pd.read_csv(p))
    df = pd.concat(dfs, ignore_index=True)

    # remove duplicates caused by overlapping year ranges in source files
    rows_before = len(df)
    df = df.drop_duplicates(subset=["REF_AREA", "TYPE_CRIME", "TIME_PERIOD"], keep="first")
    rows_after = len(df)

    if rows_before > rows_after:
        print(f" !! Removed {rows_before - rows_after:,} duplicate rows")
    
    return df

def main() -> None:
    """Download and process crime rate data from ISTAT."""
    print(f"Downloading {len(YEARS)} years of crime rate data...")
    print("=" * 50)


    paths = []
    for i, year in enumerate(YEARS, start=1):
        path = fetch_one_year(year, i, len(YEARS))
        paths.append(path)
    
    df = load_concat_csv(paths)
    out_parquet = OUT_PROCESSED / f"{DATAFLOW_KEY}_2014_2023.parquet"
    df.to_parquet(out_parquet, index=False)
    print(f"[OK] {DATAFLOW_KEY}: {df.shape[0]:,} rows saved to {out_parquet.name}")
    
    print("=" * 50)
    print("All downloads complete!")

if __name__ == "__main__":
    main()