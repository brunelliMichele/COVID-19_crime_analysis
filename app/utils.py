import streamlit as st
import pandas as pd
import geopandas as gpd
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data"

MAPPING_SARDINIA: dict[str, str] = {
    "ITG2A": "ITG25",
    "ITG2B": "ITG26",
    "ITG2C": "ITG27",
    "ITG29": "ITG28", 
}

@st.cache_data
def load_crime_data() -> pd.DataFrame:
    return pd.read_parquet(DATA_PATH / "processed/crime_clean.parquet")

@st.cache_data
def load_shapes() -> gpd.GeoDataFrame:
    gdf = gpd.read_parquet(DATA_PATH / "shapes/nuts3_it.geoparquet")
    gdf["NUTS_ID"] = gdf["NUTS_ID"].replace(MAPPING_SARDINIA)
    return gdf.to_crs(epsg=4326)

def calc_variation(crime: pd.DataFrame, crime_type: str) -> pd.DataFrame:
    df = crime[crime["TYPE_CRIME"] == crime_type]

    pre = df[df["TIME_PERIOD"].between(2014, 2019)]
    pre_mean = pre.groupby("REF_AREA")["OBS_VALUE"].mean()

    covid = df[df["TIME_PERIOD"] == 2020]
    covid_sum = covid.groupby("REF_AREA")["OBS_VALUE"].sum()

    var = ((covid_sum - pre_mean) / pre_mean * 100).reset_index()
    var.columns = ["REF_AREA", "VAR"]

    return var



def fix_sardinia_codes(gdf: gpd.GeoDataFrame, column: str="NUTS_ID") -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf[column] = gdf[column].replace(MAPPING_SARDINIA)
    return gdf