import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from libpysal.weights import Queen
from esda.moran import Moran, Moran_Local
from utils import(
    load_crime_data, load_criminality_data, load_shapes,
    filter_crime_by_level, CRIME_CATEGORIES
)
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false

st.set_page_config(
    page_title="Spatial Autocorrelation Analysis",
    layout="wide"
)
st.title("Spatial Autocorrelation Analysis")
st.markdown("""
Moran's I measures whether similar values cluster spatially across three periods:
- **Pre-COVID (2014-2019)**: baseline period
- **During COVID (2020-2021)**: pandemic restrictions
- **Post-COVID (2022-2023)**: recovery phase
""")

# -------- PERIOD definitions ----------
PERIODS = {
    "Pre-COVID (2014-2019)": (2014, 2019),
    "During COVID (2020-2021)": (2020, 2021),
    "Post-COVID (2022-2023)": (2022, 2023),
}

PERIOD_COLORS = {
    "Pre-COVID (2014-2019)": "#2166ac",
    "During COVID (2020-2021)": "#b2182b",
    "Post-COVID (2022-2023)": "#1b7837",
}

# -------------- Functions ---------------
def calc_period_values(df: pd.DataFrame, crime_type: str, start: int, end: int) -> pd.DataFrame:
    """Calculate mean values for specific period"""
    filtered = df[
        (df["TYPE_CRIME"] == crime_type) &
        (df["TIME_PERIOD"].between(start, end))
    ]
    result = filtered.groupby("REF_AREA")["OBS_VALUE"].mean().reset_index()
    return result

@st.cache_data
def compute_weights_cached(gdf_wkt: str, index_list: list):
    """Cache weights using WKT representation"""
    gdf = gpd.GeoDataFrame(
        {"geometry": gpd.GeoSeries.from_wkt(gdf_wkt.split("|||"))},
        index=index_list
    )
    w = Queen.from_dataframe(gdf)
    w.transform = "R" 
    return w

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
    
    # build weights
    w = Queen.from_dataframe(merged)
    w.transform = "R" 

    y = merged["OBS_VALUE"].values


    moran_global = Moran(y, w) # global Moran

    moran_local = Moran_Local(y, w) # local moran

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

# ---------- Sidebar filters ---------------
st.sidebar.header("Filters")

data_type = st.sidebar.radio(
    "Data type",
    ["Absolute crimes", "Criminality rate (per 100k)"],
    horizontal=True
)

geo_level = st.sidebar.radio(
    "Geographical level",
    ["provinces", "regions"],
    format_func=lambda x: x.capitalize(),
    horizontal=True
)

categories = list(CRIME_CATEGORIES.keys())
selected_category = st.sidebar.selectbox("Category", categories)

crimes_in_category = CRIME_CATEGORIES[selected_category]
crime_labels = list(crimes_in_category.values())
crime_codes = list(crimes_in_category.keys())

selected_label = st.sidebar.selectbox("Type of crime", crime_labels)
selected_crime = crime_codes[crime_labels.index(selected_label)]


# ---------------- Load data ------------------
if data_type == "Absolute crimes":
    raw_data = load_crime_data()
else:
    raw_data = load_criminality_data()

raw_data = filter_crime_by_level(raw_data, geo_level)
shapes = load_shapes(geo_level)


# ------- Compute Moran for all periods --------
results = {}

for period_name, (start, end) in PERIODS.items():
    result = compute_moran_for_period(shapes, raw_data, selected_crime, start, end)
    if result:
        results[period_name] = result
if len(results) == 0:
    st.error("Not enough data for any period")
    st.stop()

# ============ SECTION 1: Global Moran's I comparison =========
st.subheader("Global Moran's I - Temporal Comparison")

# metrics table
metrics_data = []
for period_name, res in results.items():
    metrics_data.append({
        "Period": period_name,
        "Moran's I": res["moran_I"],
        "Expected I": res["moran_EI"],
        "z-score": res["moran_z"],
        "p-value": res["moran_p"],
        "Significant": "✓" if res["moran_p"] < 0.05 else "✗"
    })

metrics_df = pd.DataFrame(metrics_data)

# display as columns
cols = st.columns(len(results))
for i, (period_name, res) in enumerate(results.items()):
    with cols[i]:
        st.markdown(f"**{period_name}**")
        st.metric("Moran's I", f"{res['moran_I']:.3f}")
        st.metric("p-value", f"{res['moran_p']:.4f}")
        if res["moran_p"] < 0.05:
            if res["moran_p"] > 0:
                st.success("Clustered")
            else:
                st.warning("Dispersed")
        else:
            st.info("Random")

# bar chart comparison
st.markdown("---")
fig_comparison = go.Figure()

periods_list = list(results.keys())
moran_values = [results[p]["moran_I"] for p in periods_list]
colors = [PERIOD_COLORS[p] for p in periods_list]

fig_comparison.add_trace(go.Bar(
    x=periods_list,
    y=moran_values,
    marker_color=colors,
    text=[f"{v:.3f}" for v in moran_values],
    textposition="auto"
))

fig_comparison.add_hline(y=0, line_dash="dot", line_color="gray")
fig_comparison.update_layout(
    title="Moran's I Evolution Across Periods",
    yaxis_title="Moran's I",
    xaxis_title="",
    height=400,
    showlegend=False
)

st.plotly_chart(fig_comparison, width="stretch")

# Interpretation
st.markdown("**Interpretation:**")

if len(results) == 3:
    pre = results.get("Pre-COVID (2014-2019)")
    during = results.get("During COVID (2020-2021)")
    post = results.get("Post-COVID (2022-2023)")

    if pre and during:
        delta_during = during["moran_I"] - pre["moran_I"]
        if abs(delta_during) > 0.05:
            direction = "increased" if delta_during > 0 else "decreased"
            st.write(f" - Spatial clustering **{direction}** during COVID (ΔI = {delta_during:+.3f})")
        else:
            st.write("- Spatial clustering remained **stable** during COVID")
    
    if during and post:
        delta_post = post["moran_I"] - during["moran_I"]
        if abs(delta_post) > 0.05:
            direction = "increased" if delta_post > 0 else "decreased"
            st.write(f" - Post-COVID clustering **{direction}** compared to pandemic period (ΔI = {delta_post:+.3f})")
        

# =========== SECTION 2: Moran Scatter Plot ===========
st.markdown("---")
st.subheader("Moran Scatter Plots by Period")

QUADRANT_COLORS = {
    1: "#d73027",
    2: "#4575b4",
    3: "#fdae61",
    4: "#abd9e9",
    0: "#999999" 
}

QUADRANT_LABELS = {
    1: "High-High",
    2: "Low-Low",
    3: "High-Low",
    4: "Low-High",
    0: "Center"
}

fig_scatter = make_subplots(
    rows=1, cols=len(results),
    subplot_titles=list(results.keys()),
    horizontal_spacing=0.08
)

for col_idx, (period_name, res) in enumerate(results.items(), start=1):
    gdf_period = res["gdf"]
    y_std = res["y_std"]
    y_lag = res["y_lag"]
    quadrant = res["quadrant"]

    for q in [1, 2, 3, 4]:
        mask = quadrant == q
        if mask.sum() > 0:
            fig_scatter.add_trace(
                go.Scatter(
                    x=y_std[mask],
                    y=y_lag[mask],
                    mode="markers",
                    marker=dict(color=QUADRANT_COLORS[q], size=8),
                    name=QUADRANT_LABELS[q],
                    text=gdf_period["AREA_NAME"].values[mask],
                    hovertemplate="%{text}<br>Value: %{x:.2f}<br>Lag: %{y:.2f}<extra></extra>",
                    showlegend=(col_idx == 1),
                    legendgroup=QUADRANT_LABELS[q]
                ),
                row=1, col=col_idx
            )
    
    # regression line
    slope = res["moran_I"]
    fig_scatter.add_trace(
        go.Scatter(
            x=[-3, 3],
            y=[-3 * slope, 3 * slope],
            mode="lines",
            line=dict(color="black", dash="dash", width=1),
            showlegend=False
        ),
        row=1, col=col_idx
    )

    # axis lines for each subplot
    for col_idx in range(1, len(results) + 1):
        # horizontal line at y=0
        fig_scatter.add_shape(
            type="line",
            x0=-3.5, x1=3.5, y0=0, y1=0,
            line=dict(color="gray", dash="dot"),
            row=1, col=col_idx
        )
        # vertical line at x=0
        fig_scatter.add_shape(
            type="line",
            x0=0, x1=0, y0=-3.5, y1=3.5,
            line=dict(color="gray", dash="dot"),
            row=1, col=col_idx
        )

fig_scatter.update_layout(
    height=500,
    margin=dict(b=100),
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="center",
        x=0.5
    )
)
fig_scatter.update_xaxes(title_text="Standardized value", range=[-3.5, 3.5])
fig_scatter.update_yaxes(title_text="Spatial lag", range=[-3.5, 3.5])

st.plotly_chart(fig_scatter, width="stretch")


# =========== SECTION 3: LISA Maps ==============
st.markdown("---")
st.subheader("LISA Cluster Maps by Period")
st.markdown("Hot spots (High-High) and cold spots (Low-Low) with p < 0.05")

LISA_COLORS = {
    "High-High": "#d73027",
    "Low-Low": "#4575b4",
    "High-Low": "#fdae61",
    "Low-High": "#abd9e9",
    "Not significant": "#f0f0f0"
}

selected_period = st.selectbox(
    "Select period to display",
    list(results.keys())
)

res = results[selected_period]
gdf_lisa = res["gdf"]

fig_lisa = px.choropleth_map(
    gdf_lisa,
    geojson=gdf_lisa.geometry.__geo_interface__,
    locations=gdf_lisa.index,
    color="LISA_LABEL",
    color_discrete_map=LISA_COLORS,
    category_orders={"LISA_LABEL": list(LISA_COLORS.keys())},
    map_style="carto-positron",
    center={"lat": 42.0, "lon": 12.5},
    zoom=5,
    hover_name="AREA_NAME",
    hover_data={
        "OBS_VALUE": ":.1f",
        "LISA_P": ":.4f",
        "LISA_LABEL": True,
        "AREA_NAME": False
    },
    labels={
        "OBS_VALUE": "Mean value",
        "LISA_P": "p-value",
        "LISA_LABEL": "Cluster type"
    }
)

fig_lisa.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700)
st.plotly_chart(fig_lisa, width="stretch")

# cluster summary table
st.subheader("Cluster Distribution by Period")

summary_data = []
for period_name, res in results.items():
    counts = res["gdf"]["LISA_LABEL"].value_counts()
    for label in LISA_COLORS.keys():
        summary_data.append({
            "Period": period_name,
            "Cluster": label,
            "Count": counts.get(label, 0)
        })

summary_df = pd.DataFrame(summary_data)
summary_pivot = summary_df.pivot(index="Cluster", columns="Period", values="Count").fillna(0).astype(int)
summary_pivot = summary_pivot[list(results.keys())] # order columns

st.dataframe(summary_pivot, width="stretch")

# stacked bar chart
fig_stacked = px.bar(
    summary_df[summary_df["Cluster"] != "Not significant"],
    x="Period",
    y="Count",
    color="Cluster",
    color_discrete_map=LISA_COLORS,
    title="Significant Cluster by Period"
)

fig_stacked.update_layout(height=400)
st.plotly_chart(fig_stacked, width="stretch")