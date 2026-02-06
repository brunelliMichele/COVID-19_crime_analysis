import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    load_crime_data, load_criminality_data, load_shapes,
    filter_crime_by_level, calc_period_variation,
    CRIME_CATEGORIES, GEO_LEVELS, PERIODS, BASELINE
)

# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false

st.set_page_config(
    page_title="Spatial Distribution of Crime Changes",
    layout="wide"
)

st.title("Spatial Distribution of Crime Changes")
st.markdown("Crime variation (%) from pre-COVID baseline (2014-2019)")


# ---------- Sidebar filters ----------
st.sidebar.header("Filters")

# data type selection
data_type = st.sidebar.radio(
    "Data type",
    ["Absolute crimes", "Criminality rate (per 100k)"],
    horizontal=True
)

# geo level
selected_geo_label = st.sidebar.radio(
    "Geographical level",
    list(GEO_LEVELS.keys()),
    horizontal=True
)
geo_level = GEO_LEVELS[selected_geo_label]

# category filter
categories = list(CRIME_CATEGORIES.keys())
selected_category = st.sidebar.selectbox("Category", categories)

# crime filter
crimes_in_category = CRIME_CATEGORIES[selected_category]
crime_labels = list(crimes_in_category.values())
crime_codes = list(crimes_in_category.keys())

selected_label = st.sidebar.selectbox("Type of crime", crime_labels)
selected_crime = crime_codes[crime_labels.index(selected_label)]

# ---------- Load data ----------
if data_type == "Absolute crimes":
    raw_data = load_crime_data()
    value_format = ":.0f"
else:
    raw_data = load_criminality_data()
    value_format = ":.1f"

raw_data = filter_crime_by_level(raw_data, geo_level)
shapes = load_shapes(geo_level)

# ---------- Calculate variations for all periods ----------
results = {}

for period_name, (start, end) in PERIODS.items():
    var_df = calc_period_variation(raw_data, selected_crime, BASELINE, (start, end))
    gdf = shapes.merge(var_df, left_on="NUTS_ID", right_on="REF_AREA")

    if gdf["VAR"].notna().sum() > 0:
        results[period_name] = gdf

if len(results) == 0:
    st.error("No available data for this type of crime")
    st.stop()


# ---------- Display subtitle ----------
st.caption(f"**{selected_label}** | {data_type} | {selected_geo_label}")

# ---------- Period selection ----------
view_mdoe = st.radio(
    "View mode",
    ["Single period", "Compare all periods"],
    horizontal=True
)

if view_mdoe == "Single period":
    selected_period = st.selectbox("Select period", list(results.keys()))

    gdf = results[selected_period]

    fig = px.choropleth_map(
        gdf,
        geojson=gdf.geometry.__geo_interface__,
        locations=gdf.index,
        color="VAR",
        color_continuous_scale="RdYlGn_r",
        range_color=[-80, 80],
        map_style="carto-positron",
        center={"lat": 42.0, "lon": 12.5},
        zoom=5,
        hover_name="AREA_NAME",
        hover_data={
            "VAR": ":.1f",
            "BASELINE": value_format,
            "TARGET": value_format,
            "AREA_NAME": False,
            "REF_AREA": False
        },
        labels={
            "VAR": "Variation %",
            "BASELINE": "Baseline (2014-19)",
            "TARGET": f"Target {selected_period.split('(')[1].split(')')[0]}"
        }
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=700,
        coloraxis_colorbar=dict(title="Variation %", ticksuffix="%")
    )

    st.plotly_chart(fig, width="stretch")

    # stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Mean variation", f"{gdf['VAR'].mean():.1f}%")
    col2.metric("Min", f"{gdf['VAR'].min():.1f}%")
    col3.metric("Max", f"{gdf['VAR'].max():.1f}%")

else:
    # compare all periods side by side
    st.markdown("### Variation by Period")

    # summary stats
    cols = st.columns(len(results))
    for i, (period_name, gdf) in enumerate(results.items()):
        with cols[i]:
            st.markdown(f"**{period_name}**")
            mean_var = gdf["VAR"].mean()
            delta_color = "normal" if period_name == "Pre-COVID (2014-2019)" else ("inverse" if mean_var < 0 else "normal")
            st.metric(
                "Mean variation",
                f"{mean_var:.1f}%",
                delta=None if period_name == "Pre-COVID (2014-2019)" else f"{mean_var:.1f}%",
                delta_color=delta_color
            )
    
    # maps in tabs
    tabs = st.tabs(list(results.keys()))

    for tab, (period_name, gdf) in zip(tabs, results.items()):
        with tab:
            fig = px.choropleth_map(
                gdf,
                geojson=gdf.geometry.__geo_interface__,
                locations=gdf.index,
                color="VAR",
                color_continuous_scale="RdYlGn_r",
                range_color=[-80, 80],
                map_style="carto-positron",
                center={"lat": 42.0, "lon": 12.5},
                zoom=5,
                hover_name="AREA_NAME",
                hover_data={
                    "VAR": ":.1f",
                    "BASELINE": value_format,
                    "TARGET": value_format,
                    "AREA_NAME": False,
                    "REF_AREA": False
                },
                labels={
                    "VAR": "Variation %",
                    "BASELINE": "Baseline (2014-19)",
                    "TARGET": "Period value"
                }
            )

            fig.update_layout(
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                height=600,
                coloraxis_colorbar=dict(title="Var %", ticksuffix="%")
            )

            st.plotly_chart(fig, width="stretch")

# ---------- Bar chart ----------
st.markdown("---")
st.markdown("### Mean Variation Trend")

period_names = list(results.keys())
mean_vars = [results[p]["VAR"].mean() for p in period_names]

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=period_names,
    y=mean_vars,
    marker_color=["#2166ac", "#b2182b", "#1b7837"],
    text=[f"{v:.1f}%" for v in mean_vars],
    textposition="auto"
))

fig_bar.add_hline(y=0, line_dash="dot", line_color="gray")
fig_bar.update_layout(
    yaxis_title="Mean variation (%)",
    xaxis_title="",
    height=400,
    yaxis=dict(range=[min(min(mean_vars) * 1.3, -10), max(max(mean_vars) * 1.3, 10)]),
    margin=dict(b=80)
)

st.plotly_chart(fig_bar, width="stretch")

# ---------- Top increases/decreases table ----------
with st.expander("Top 10 increases and decreases by period"):
    selected_period_table = st.selectbox(
        "Select period",
        list(results.keys()),
        key="table_period"
    )

    gdf_table = results[selected_period_table]

    col_inc, col_dec = st.columns(2)

    with col_inc:
        st.markdown("**Largest increases**")
        top_inc = gdf_table.nlargest(10, "VAR")[["AREA_NAME", "VAR", "BASELINE", "TARGET"]].copy()
        top_inc.columns = ["Area", "Var %", "Baseline", "Target"]
        st.dataframe(top_inc, hide_index=True)

    with col_dec:
        st.markdown("**Largest decreases**")
        top_dec = gdf_table.nsmallest(10, "VAR")[["AREA_NAME", "VAR", "BASELINE", "TARGET"]].copy()
        top_dec.columns = ["Area", "Var %", "Baseline", "Target"]
        st.dataframe(top_dec, hide_index=True)


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