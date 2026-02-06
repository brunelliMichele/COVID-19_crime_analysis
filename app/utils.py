import warnings
import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from libpysal.weights import Queen, KNN, attach_islands
from esda.moran import Moran, Moran_Local

# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
warnings.filterwarnings("ignore", message="The weights matrix is no fully connected")

DATA_PATH = Path(__file__).parent.parent / "data"

MAPPING_SARDINIA: dict[str, str] = {
    "ITG2A": "ITG25",
    "ITG2B": "ITG26",
    "ITG2C": "ITG27",
    "ITG29": "ITG28", 
}

PERIODS: dict[str, tuple[int, int]] = {
    "During COVID (2020-2021)": (2020, 2021),
    "Post-COVID (2022-2023)": (2022, 2023),
}

PERIODS_WITH_BASELINE: dict[str, tuple[int, int]] = {
    "Pre-COVID (2014-2019)": (2014, 2019),
    "During COVID (2020-2021)": (2020, 2021),
    "Post-COVID (2022-2023)": (2022, 2023),
}

PERIOD_COLORS: dict[str, str] = {
    "Pre-COVID (2014-2019)": "#2166ac",
    "During COVID (2020-2021)": "#b2182b",
    "Post-COVID (2022-2023)": "#1b7837",
}

BASELINE: tuple[int, int] = (2014, 2019)

GEO_LEVELS: dict[str, str] = {
    "Provinces": "provinces",
    "Regions": "regions",
    "Macro-areas": "macro-areas",
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

QUADRANT_COLORS: dict[int, str] = {
    1: "#d73027",
    2: "#4575b4", 
    3: "#fdae61", 
    4: "#abd9e9", 
    0: "#999999"
}

QUADRANT_LABELS: dict[int, str] = {
    1: "High-High", 
    2: "Low-Low", 
    3: "High-Low", 
    4: "Low-High", 
    0: "Center"
}

LISA_COLORS: dict[str, str] = {
    "High-High": "#d73027",
    "Low-Low": "#4575b4",
    "High-Low": "#fdae61",
    "Low-High": "#abd9e9",
    "Not significant": "#f0f0f0"
}

TRANSITION_COLORS: dict[str, str] = {
    "Stable Hot Spot": "#d73027",           
    "Stable Cold Spot": "#4575b4",          
    "New Hot Spot": "#ff7f00",              
    "New Cold Spot": "#1f78b4",             
    "Disappeared Hot Spot": "#ffcccc",      
    "Disappeared Cold Spot": "#cce5ff",     
    "Stable Outlier": "#984ea3",            
    "Stable Not Significant": "#f0f0f0",    
    "Other Transition": "#bdbdbd"          
}

CRIMES_TO_CHECK: list[tuple[str, str]] = [
    ("PICKTHEF", "Pickpocketing"),
    ("BANKROB", "Bank Robbery"),
    ("THEFT", "Theft (Total)"),
    ("ROBBER", "Robbery (Total)"),
    ("BURGTHEF", "Residential Burglary"),
    ("CARTHEF", "Car Theft"),
    ("STREETROB", "Street Robbery"),
    ("CYBERCRIM", "Cybercrime"),
    ("SWINCYB", "Online Fraud"),
    ("TOT", "Total Crimes"),
]


# ---------- Data loading ----------
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


# ---------- Filtering ----------
def filter_crime_by_level(crime: pd.DataFrame, level: str) -> pd.DataFrame:
    nuts_len = {
        "provinces": 5,
        "regions": 4,
        "macro-areas": 3,
    }
    length = nuts_len[level]
    return crime[crime["REF_AREA"].str.len() == length]


# ---------- Variation calculations ----------
def calc_period_variation(df: pd.DataFrame, crime_type: str, baseline: tuple, target: tuple) -> pd.DataFrame:
    """Calculate variation between baseline period and target period"""
    filtered = df[df["TYPE_CRIME"] == crime_type]

    # baseline mean
    base_data = filtered[filtered["TIME_PERIOD"].between(baseline[0], baseline[1])]
    base_mean = base_data.groupby("REF_AREA", as_index=False)["OBS_VALUE"].mean()
    base_mean.columns = ["REF_AREA", "BASELINE"]

    # target mean
    target_data = filtered[filtered["TIME_PERIOD"].between(target[0], target[1])]
    target_mean = target_data.groupby("REF_AREA", as_index=False)["OBS_VALUE"].mean()
    target_mean.columns = ["REF_AREA", "TARGET"]

    # merge and calculate variation
    result = base_mean.merge(target_mean, on="REF_AREA", how="outer")
    result["VAR"] = (result["TARGET"] - result["BASELINE"]) / result["BASELINE"] * 100
    result.loc[result["BASELINE"] == 0, "VAR"] = None

    return result

@st.cache_data
def get_all_variations() -> pd.DataFrame:
    """Calculate variations for all key crime types using national data"""
    crime = load_crime_data()

    # filter to national level (REF_AREA = "IT")
    national = crime[crime["REF_AREA"].str.len() == 2]

    results = []
    for code, name in CRIMES_TO_CHECK:
        data = national[national["TYPE_CRIME"] == code]
        if len(data) == 0:
            continue

        pre = data[data["TIME_PERIOD"].between(2014, 2019)]["OBS_VALUE"].mean()
        during = data[data["TIME_PERIOD"].between(2020, 2021)]["OBS_VALUE"].mean()

        var = (during - pre) / pre * 100 if pre > 0 else 0

        results.append({
            "code": code,
            "name": name,
            "pre_covid_avg": during,
            "during_covid_avg": during,
            "variation_pct": var
        })
    return pd.DataFrame(results)

    

# ---------- Moran's I ----------

def calc_period_values(df: pd.DataFrame, crime_type: str, start: int, end: int) -> pd.DataFrame:
    """Calculate mean values for specific period"""
    filtered = df[
        (df["TYPE_CRIME"] == crime_type) &
        (df["TIME_PERIOD"].between(start, end))
    ]
    result = filtered.groupby("REF_AREA")["OBS_VALUE"].mean().reset_index()
    return result


def compute_moran_for_period(
        gdf: gpd.GeoDataFrame,
        raw_data: pd.DataFrame,
        crime_type: str,
        start_year: int,
        end_year: int
) -> dict | None:
    """Compute Moran statistics for a single period"""

    period_data = calc_period_values(raw_data, crime_type, start_year, end_year)

    merged = gdf.merge(period_data, left_on="NUTS_ID", right_on="REF_AREA")
    merged = merged.dropna(subset=["OBS_VALUE"])

    if len(merged) < 5:
        return None
    
    # build weights with island handling
    w = Queen.from_dataframe(merged, use_index=False)
    if w.n_components > 1:
        w = attach_islands(w, KNN.from_dataframe(merged, k=1, use_index=False))
    w.transform = "R" 

    y = merged["OBS_VALUE"].values


    moran_global = Moran(y, w) # Global Moran

    moran_local = Moran_Local(y, w) # Local Moran

    # standardized values for scatter plot
    y_std = (y - y.mean()) / y.std()
    y_lag = w.sparse.dot(y_std)

    # quadrant assignment
    quadrant = np.zeros(len(y_std), dtype=int)
    quadrant[(y_std > 0) & (y_lag > 0)] = 1 # HH
    quadrant[(y_std < 0) & (y_lag < 0)] = 2 # LL
    quadrant[(y_std > 0) & (y_lag < 0)] = 3 # HL
    quadrant[(y_std < 0) & (y_lag > 0)] = 4 # LH

    # LISA classification
    sig = moran_local.p_sim < 0.05
    lisa_labels = []
    for i in range(len(merged)):
        if not sig[i]:
            lisa_labels.append("Not significant")
        else:
            q = moran_local.q[i]
            lisa_labels.append({
                1: "High-High",
                2: "Low-High",
                3: "Low-Low",
                4: "High-Low"
            }[q])
        
    merged = merged.copy()
    merged["y_std"] = y_std
    merged["y_lag"] = y_lag
    merged["quadrant"] = quadrant
    merged["LISA_LABEL"] = lisa_labels
    merged["LISA_P"] = moran_local.p_sim

    return {
        "gdf": merged,
        "moran_I": moran_global.I,
        "moran_EI": moran_global.EI,
        "moran_p": moran_global.p_sim,
        "moran_z": moran_global.z_sim,
        "y_std": y_std,
        "y_lag": y_lag,
        "quadrant": quadrant,
    }

# ---------- Transitions ----------
def classify_transition(from_label: str, to_label: str) -> str:
    """Classify the type of transition between LISA clusters"""
    if from_label == to_label:
        if from_label == "High-High":
            return "Stable Hot Spot"
        elif from_label == "Low-Low":
            return "Stable Cold Spot"
        elif from_label in ["High-Low", "Low-High"]:
            return "Stable Outlier"
        else:
            return "Stable Not Significant Spot"
        
    # new clusters
    if to_label == "High-High":
        return "New Hot Spot"
    if to_label == "Low-Low":
        return "New Cold Spot"

    # disappeared clusters
    if from_label == "High-High":
        return "Disappeared Hot Spot"
    if from_label == "Low-Low":
        return "Disappeared Cold Spot"
    
    return "Other Transition"

def compute_transitions(gdf_from: gpd.GeoDataFrame, gdf_to: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Compute transitions between two periods"""
    # merge on NUTS_ID
    merged = gdf_from[["NUTS_ID", "AREA_NAME", "LISA_LABEL", "geometry"]].merge(
        gdf_to[["NUTS_ID", "LISA_LABEL"]],
        on="NUTS_ID",
        suffixes=("_from", "_to")
    )

    # classify transitions
    merged["TRANSITION"] = merged.apply(
        lambda row: classify_transition(row["LISA_LABEL_from"], row["LISA_LABEL_to"]),
        axis=1
    )

    return gpd.GeoDataFrame(merged, geometry="geometry")
