from pathlib import Path
import geopandas as gpd

SHAPES_DIR = Path("data/shapes")
SHAPES_DIR.mkdir(parents=True, exist_ok=True)

def build(level: int, in_path: str, out_name: str):
    gdf = gpd.read_file(in_path)
    it = gdf[gdf["CNTR_CODE"] == "IT"][["NUTS_ID", "NAME_LATN", "geometry"]].copy()
    it = it.rename(columns={"NAME_LATN": "AREA_NAME"})
    it.to_parquet(SHAPES_DIR / out_name, engine="pyarrow")

def main():
    build(1, "data/shapes/NUTS_RG_01M_2021_4326_LEVL_1.geojson", "nuts1_it.geoparquet")
    build(2, "data/shapes/NUTS_RG_01M_2021_4326_LEVL_2.geojson", "nuts2_it.geoparquet")
    build(3, "data/shapes/NUTS_RG_01M_2021_4326_LEVL_3.geojson", "nuts3_it.geoparquet")

if __name__ == "__main__":
    main()