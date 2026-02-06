import pandas as pd
from pathlib import Path

crime = pd.read_parquet(Path("data/processed/crime_clean.parquet"))

# Vediamo quali REF_AREA esistono
print("REF_AREA unique values (sorted by length):")
areas = crime["REF_AREA"].unique()
for area in sorted(areas, key=len):
    print(f"  {area} (len={len(area)})")
    if len(area) > 5:  # Mostra solo i primi corti
        break

# Oppure più semplice - conta per lunghezza
print("\nCount by REF_AREA length:")
print(crime.groupby(crime["REF_AREA"].str.len()).size())