import geopandas as gpd

MAPPING_SARDINIA = {
    "ITG2A": "ITG25",
    "ITG2B": "ITG26",
    "ITG2C": "ITG27",
    "ITG29": "ITG28", 
}

def fix_sardinia_codes(gdf: gpd.GeoDataFrame, column: str="NUTS_ID") -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf[column] = gdf[column].replace(MAPPING_SARDINIA)
    return gdf