import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    load_criminality_data, load_shapes,
    filter_crime_by_level, compute_moran_for_period, 
    compute_transitions,
    CRIME_CATEGORIES, PERIODS_WITH_BASELINE,
    LISA_COLORS, TRANSITION_COLORS
)

# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false

st.set_page_config(
    page_title="LISA Cluster Transitions",
    layout="wide"
)

st.title("LISA Cluster Transitions")

st.markdown("""
This page shows how spatial clusters changed between periods.
Identify areas where crime patterns shifted due to COVID-19.
""")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")

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

# ---------- Load data ----------
raw_data = load_criminality_data()

raw_data = filter_crime_by_level(raw_data, geo_level)
shapes = load_shapes(geo_level)

# ---------- Compute Moran for all periods ----------
results = {}

for period_name, (start, end) in PERIODS_WITH_BASELINE.items():
    result = compute_moran_for_period(shapes, raw_data, selected_crime, start, end)
    if result:
        results[period_name] = result

if len(results) < 2:
    st.error("Not enough data to compare periods")
    st.stop()

# ---------- Period comparison selection ----------
st.subheader("Select Periods to Compare")

period_names = list(results.keys())

col1, col2 = st.columns(2)
with col1:
    from_period = st.selectbox("From period", period_names, index=0)
with col2:
    to_options = [p for p in period_names if p != from_period]
    to_period = st.selectbox("To period", to_options, index=min(1, len(to_options)-1) if to_options else 0)

# compute transitions
gdf_from = results[from_period]["gdf"]
gdf_to = results[to_period]["gdf"]
gdf_transitions = compute_transitions(gdf_from, gdf_to)

# ========== SECTION 1: Transition Map ==========
st.markdown("---")
st.subheader(f"Cluster Transitions: {from_period} → {to_period}")

fig_map = px.choropleth_map(
    gdf_transitions,
    geojson=gdf_transitions.geometry.__geo_interface__,
    locations=gdf_transitions.index,
    color="TRANSITION",
    color_discrete_map=TRANSITION_COLORS,
    category_orders={"TRANSITION": list(TRANSITION_COLORS.keys())},
    map_style="carto-positron",
    center={"lat": 42.0, "lon": 12.5},
    zoom=5,
    hover_name="AREA_NAME",
    hover_data={
        "LISA_LABEL_from": True,
        "LISA_LABEL_to": True,
        "TRANSITION": True,
        "AREA_NAME": False
    },
    labels={
        "LISA_LABEL_from": f"Cluster ({from_period.split('(')[0].strip()})",
        "LISA_LABEL_to": f"Cluster ({to_period.split('(')[0].strip()})",
        "TRANSITION": "Transition type"
    }
)

fig_map.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    height=700
)

st.plotly_chart(fig_map, width="stretch")


# ========== SECTION 2: Transition Matrix ==========
st.markdown("---")
st.subheader("Transition Matrix")
st.markdown("Rows = origin cluster, Columns = destination cluster")

# create transition matrix
transition_matrix = pd.crosstab(
    gdf_transitions["LISA_LABEL_from"],
    gdf_transitions["LISA_LABEL_to"],
    margins=True,
    margins_name="Total"
)

# reorder rows and columns
cluster_order = ["High-High", "Low-Low", "High-Low", "Low-High", "Not significant", "Total"]
transition_matrix = transition_matrix.reindex(
    index=[c for c in cluster_order if c in transition_matrix.index],
    columns=[c for c in cluster_order if c in transition_matrix.columns]
)

st.dataframe(transition_matrix, width="stretch")


# ========== SECTION 3: Transition Summary ==========
st.markdown("---")
st.subheader("Transition Summary")

transition_counts = gdf_transitions["TRANSITION"].value_counts()

# metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    stable_hot = transition_counts.get("Stable Hot Spot", 0)
    new_hot = transition_counts.get("New Hot Spot", 0)
    st.metric("Hot Spots", f"{stable_hot + new_hot}", delta=f"+{new_hot} new" if new_hot > 0 else None)

with col2:
    stable_cold = transition_counts.get("Stable Cold Spot", 0)
    new_cold = transition_counts.get("New Cold Spot", 0)
    st.metric("Cold Spots", f"{stable_cold + new_cold}", delta=f"+{new_cold} new" if new_cold > 0 else None)

with col3:
    disappeared_hot = transition_counts.get("Disappeared Hot Spot", 0)
    disappeared_cold = transition_counts.get("Disappeared Cold Spots", 0)
    st.metric("Disappeared Clusters", f"{disappeared_hot + disappeared_cold}")

with col4:
    stable_ns = transition_counts.get("Stable Not Significant", 0)
    total = len(gdf_transitions)
    st.metric("Stability Rate", f"{(stable_ns + stable_hot + stable_cold) / total * 100:.1f}%")

# bar chart of transitions
fig_bar = px.bar(
    x=transition_counts.index,
    y=transition_counts.values,
    color=transition_counts.index,
    color_discrete_map=TRANSITION_COLORS,
    labels={"x": "Transition Type", "y": "Count"}
)

fig_bar.update_layout(
    height=400,
    showlegend=False,
    xaxis_tickangle=-45
)

st.plotly_chart(fig_bar, width="stretch")

# ========== SECTION 4: Notable Changes ==========
st.markdown("---")
st.subheader("Notable Changes")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**New Hot Spots** (emerging high-crime clusters)")
    new_hotspots = gdf_transitions[gdf_transitions["TRANSITION"] == "New Hot Spot"][["AREA_NAME", "LISA_LABEL_from", "LISA_LABEL_to"]]
    if len(new_hotspots) > 0:
        new_hotspots.columns = ["Area", "From", "To"]
        st.dataframe(new_hotspots, hide_index=True)
    else:
        st.info("No new hot spots emerged")

with col2:
    st.markdown("**New Cold Spots** (emerging low-crime clusters)")
    new_coldspots = gdf_transitions[gdf_transitions["TRANSITION"] == "New Cold Spot"][["AREA_NAME", "LISA_LABEL_from", "LISA_LABEL_to"]]
    if len(new_coldspots) > 0:
        new_coldspots.columns = ["Area", "From", "To"]
        st.dataframe(new_coldspots, hide_index=True)
    else:
        st.info("No new cold spots emerged")

col3, col4 = st.columns(2)

with col3:
    st.markdown("**Disappeared Hot Spots** (previously high-crime, now changed)")
    disappeared_hot = gdf_transitions[gdf_transitions["TRANSITION"] == "Disappeared Hot Spot"][["AREA_NAME", "LISA_LABEL_from", "LISA_LABEL_to"]]
    if len(disappeared_hot) > 0:
        disappeared_hot.columns = ["Area", "From", "To"]
        st.dataframe(disappeared_hot, hide_index=True)
    else:
        st.info("No hot spots disappeared")
    
with col4:
    st.markdown("**Disappeared Cold Spots** (previously low-crime, now changed)")
    disappeared_cold = gdf_transitions[gdf_transitions["TRANSITION"] == "Disappeared Cold Spot"][["AREA_NAME", "LISA_LABEL_from", "LISA_LABEL_to"]]
    if len(disappeared_cold) > 0:
        disappeared_cold.columns = ["Area", "From", "To"]
        st.dataframe(disappeared_cold, hide_index=True)
    else:
        st.info("No cold spots disappeared")


# ========== SECTION 5: Side-by-side comparison ==========
st.markdown("---")
st.subheader("Side-by-Side LISA Maps")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**{from_period}**")
    fig_from = px.choropleth_map(
        gdf_from,
        geojson=gdf_from.geometry.__geo_interface__,
        locations=gdf_from.index,
        color="LISA_LABEL",
        color_discrete_map=LISA_COLORS,
        category_orders={"LISA_LABEL": list(LISA_COLORS.keys())},
        map_style="carto-positron",
        hover_name="AREA_NAME"
    )
    fig_from.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=500,
        map=dict(
            center=dict(lat=42.0, lon=12.5),
            zoom=4.5
        )
    )
    st.plotly_chart(fig_from, width="stretch")

with col2:
    st.markdown(f"**{to_period}**")
    fig_to = px.choropleth_map(
        gdf_to,
        geojson=gdf_to.geometry.__geo_interface__,
        locations=gdf_to.index,
        color="LISA_LABEL",
        color_discrete_map=LISA_COLORS,
        category_orders={"LISA_LABEL": list(LISA_COLORS.keys())},
        map_style="carto-positron",
        hover_name="AREA_NAME"
    )
    fig_to.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=500,
        map=dict(
            center=dict(lat=42.0, lon=12.5),
            zoom=4.5
        )
    )
    st.plotly_chart(fig_to, width="stretch")


# ---------- Footer ----------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: gray; font-size: 0.85em;">
        Project for the course 'Geospatial Analysis and Representation for Data Science' 
        of the Master's Degree Course in Data Science of the University of Trento.<br><br>
        Developed with 🐍 & ❤️ by Michele Brunelli | 2026
    </div>
    """,
    unsafe_allow_html=True
)