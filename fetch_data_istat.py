from __future__ import annotations
from pathlib import Path
import requests
import pandas as pd

BASE_URL = "https://esploradati.istat.it/SDMXWS/rest/data"
DATAFLOWS = {
    "delittips_1": "IT1,73_67_DF_DCCV_DELITTIPS_1,1.0",
    "delittips_9": "IT1,73_67_DF_DCCV_DELITTIPS_9,1.0",
}
OUT_RAW = Path("data/raw")
OUT_PROCESSED = Path("data/processed")
OUT_RAW.mkdir(parents=True, exist_ok=True)
OUT_PROCESSED.mkdir(parents=True, exist_ok=True)

HEADERS = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}

YEARS = list(range(2014, 2024))

def fetch_one_year(flow_key: str, flow_id: str, year: int) -> Path:
    url = f"{BASE_URL}/{flow_id}"
    params = {"startPeriod": str(year), "endPeriod": str(year)}
    out = OUT_RAW / f"{flow_key}_{year}.csv"

    if out.exists() and out.stat().st_size > 0:
        return out
    
    r = requests.get(url, params=params, headers=HEADERS, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)
    return out

def load_concat_csv(paths: list[Path]) -> pd.DataFrame:
    dfs = []
    for p in paths:
        dfs.append(pd.read_csv(p))
    return pd.concat(dfs, ignore_index=True)

def main() -> None:
    for key, flow in DATAFLOWS.items():
        paths = [fetch_one_year(key, flow, y) for y in YEARS]
        df = load_concat_csv(paths)

        out_parquet = OUT_PROCESSED / f"{key}_2014_2023.parquet"
        df.to_parquet(out_parquet, index=False)
        print(f"[OK] {key}: {df.shape} -> {out_parquet}")

if __name__ == "__main__":
    main()