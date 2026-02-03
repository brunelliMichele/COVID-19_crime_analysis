import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

def main() -> None:
    NUTS_PATH = Path("data/shapes/nuts3_it.geoparquet")
    CRIME_PATH = Path("data/processed/crime_clean.parquet")

    nuts3 = gpd.read_parquet(NUTS_PATH)
    df_crime = pd.read_parquet(CRIME_PATH)

    prov = df_crime[df_crime["REF_AREA"].str.len() == 5].copy()
    
    year = 2020
    crime_code = "ARSON"

    s = prov[(prov["TIME_PERIOD"] == year) & (prov["TYPE_CRIME"] == crime_code)].copy()
    gdf = nuts3.merge(s, left_on="NUTS_ID", right_on="REF_AREA", how="left")

    ax = gdf.plot(column="OBS_VALUE", legend=True)
    ax.set_title(f"{crime_code} ({year})")

    OUT_DIR = Path("outputs")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig_path = OUT_DIR / f"map_{crime_code}_{year}.png"
    plt.savefig(fig_path, dpi=200, bbox_inches="tight")
    print(f"[OK] saved map to {fig_path.resolve()}")

    plt.show()

if __name__ == "__main__":
    main()