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

CRIME_CATEGORIES: dict[str, dict[str, str]] = {
    "Homicide": {
        "INTENHOM": "Intentional homicide - [TOTAL]",
        "ROBBHOM": "Intentional homicide committed for robbery of theft",
        "MAFIAHOM": "Mafia-related intentional homicide",
        "TERRORHOM": "Terrorism-related intentional homicide",
        "UNINTHOM": "Manslaughter - [TOTAL]",
        "ROADHOM": "Road traffic manslaughter",
        "ATTEMPHOM": "Attempted homicide",
        "INFANTHOM": "Infanticide",
        "MANSHOM": "Unintentional homicide resulting from assult",
        "MASSMURD": "Mass murder",
    },
    "Theft": {
        "THEFT": "Theft - [TOTAL]",
        "BAGTHEF": "Snatch theft",
        "PICKTHEF": "Pickpocketing",
        "BURGTHEF": "Residential burglary",
        "SHOPTHEF": "Shoplifting",
        "VEHITHEF": "Theft from parked vehicles",
        "ARTTHEF": "Theft of artworks and archaeological materials",
        "TRUCKTHEF": "Truck theft",
        "MOPETHEF": "Moped theft",
        "MOTORTHEF": "Motorcycle theft",
        "CARTHEF": "Car theft",
    },
    "Robbery": {
        "ROBBER": "Robbery - [TOTAL]",
        "HOUSEROB": "Home robbery",
        "BANKROB": "Bank robbery",
        "POSTROB": "Post office robbery",
        "SHOPROB": "Commercial robbery",
        "STREETROB": "Street robbery",
    },
    "Sexual offences": {
        "RAPE": "Sexual assault",
        "RAPEUN18": "Sexual act with a minor",
        "CORRUPN18": "Corruption of a minor",
        "PROSTI": "Exploitation and facilitation of prostitution",
        "PORNO": "Child pornography and possesion of child sexual abuse material (CSAM)",
    },
    "Digital crimes": {
        "SWINCYB": "Online fraud and cyber scams",
        "CYBERCRIM": "Cybercrime",
    },
    "Economic crimes": {
        "EXTORT": "Extortion",
        "COUNTER": "Conterfeiting of trademarks and industrial products",
        "INTPROP": "Intellectual property infringement",
        "RECEIV": "Receiving stolen goods",
        "MONEYLAU": "Money laundering",
        "USURY": "Usury",
    },
    "Other crimes": {
        "ARSON": "Arson",
        "FOREARS": "Wildfires",
        "BLOWS": "Assault",
        "CULPINJU": "Intentional bodily injury",
        "MENACE": "Threats",
        "KIDNAPP": "Kidnapping",
        "OFFENCE": "Insults",
        "DAMAGE": "Criminal damage",
        "DAMARS": "Criminal damage followed by arson",
        "DRUG": "Drug-related offences",
        "ATTACK": "Terrorist attacks",
        "CRIMASS": "Criminal association",
        "MAFIASS": "Mafia-type criminal association",
        "SMUGGL": "Smuggling",
        "OTHCRIM": "Other crimes",
    },
    "Total": {
        "TOT": "Total",
    }
}

@st.cache_data
def load_crime_data() -> pd.DataFrame:
    return pd.read_parquet(DATA_PATH / "processed/crime_clean.parquet")

@st.cache_data
def load_criminality_data() -> pd.DataFrame:
    return pd.read_parquet(DATA_PATH / "processed/criminality_clean.parquet")

@st.cache_data
def load_shapes(level: str = "provinces") -> gpd.GeoDataFrame:
    files = {
        "provinces": "nuts3_it.geoparquet",
        "regions": "nuts2_it.geoparquet",
        "macro-areas": "nuts1_it.geoparquet",
    }
    gdf = gpd.read_parquet(DATA_PATH / f"shapes/{files[level]}")
    gdf["NUTS_ID"] = gdf["NUTS_ID"].replace(MAPPING_SARDINIA)
    return gdf.to_crs(epsg=4326)

def filter_crime_by_level(crime: pd.DataFrame, level: str) -> pd.DataFrame:
    nuts_len = {
        "provinces": 5,
        "regions": 4,
        "macro-areas": 3,
    }
    length = nuts_len[level]
    return crime[crime["REF_AREA"].str.len() == length]
    

def calc_variation(crime: pd.DataFrame, crime_type: str) -> pd.DataFrame:
    df = crime[crime["TYPE_CRIME"] == crime_type]

    pre = df[df["TIME_PERIOD"].between(2014, 2019)]
    pre_mean = pre.groupby("REF_AREA")["OBS_VALUE"].mean()

    covid = df[df["TIME_PERIOD"] == 2020]
    covid_sum = covid.groupby("REF_AREA")["OBS_VALUE"].sum()

    result = pd.DataFrame({
        "REF_AREA": pre_mean.index,
        "MEAN_PRE": pre_mean.values,
        "COVID_2020": covid_sum.reindex(pre_mean.index).values,
    })
    
    result["VAR"] = (result["COVID_2020"] - result["MEAN_PRE"]) / result["MEAN_PRE"] * 100

    result.loc[result["MEAN_PRE"] == 0, "VAR"] = None

    return result

def calc_rate_variation(criminality: pd.DataFrame, crime_type: str) -> pd.DataFrame:
    df = criminality[criminality["TYPE_CRIME"] == crime_type]

    pre = df[df["TIME_PERIOD"].between(2014, 2019)]
    pre_mean = pre.groupby("REF_AREA")["OBS_VALUE"].mean()

    covid = df[df["TIME_PERIOD"] == 2020]
    covid_val = covid.groupby("REF_AREA")["OBS_VALUE"].first() 

    result = pd.DataFrame({
        "REF_AREA": pre_mean.index,
        "MEAN_PRE": pre_mean.values,
        "COVID_2020": covid_val.reindex(pre_mean.index).values,
    })

    result["VAR"] = (result["COVID_2020"] - result["MEAN_PRE"]) / result["MEAN_PRE"] * 100
    result.loc[result["MEAN_PRE"] == 0, "VAR"] = None

    return result

def fix_sardinia_codes(gdf: gpd.GeoDataFrame, column: str="NUTS_ID") -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf[column] = gdf[column].replace(MAPPING_SARDINIA)
    return gdf

def get_crime_options() -> list[tuple[str, str, str]]:
    options = []
    for category, crimes in CRIME_CATEGORIES.items():
        for code, name in crimes.items():
            options.append((category, code, name))
    return options
