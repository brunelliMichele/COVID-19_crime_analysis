import streamlit as st
import plotly.express as px
from utils import (
    load_criminality_data, load_shapes, calc_rate_variation,
    filter_crime_by_level, CRIME_CATEGORIES
)

GEO_LEVELS = {
    "Provinces": "provinces",
    "Regions": "regions",
    "Macro-areas": "macro-areas",
}

st.set_page_config(
    page_title="Spatial distribution of criminality rate changes",
    layout="wide"
)

st.title("Spatial distribution of criminality rate changes")
st.markdown("Criminality rate variation (%) from pre-COVID baseline (2014-2019) to 2020. Rates are per 100.000 inhabitants.")

criminality = load_criminality_data()

st.sidebar.header("Filters")

# geo filter
selected_geo_label = st.sidebar.radio(
    "Geographical level",
    list(GEO_LEVELS.keys()),
    horizontal=True
)

geo_level = GEO_LEVELS[selected_geo_label]

# category filter
categories = list(CRIME_CATEGORIES.keys())
selected_category = st.sidebar.selectbox("Category", categories)

# crime filter (depending on category)
crimes_in_category = CRIME_CATEGORIES[selected_category]
crime_labels = list(crimes_in_category.values())
crime_codes = list(crimes_in_category.keys())

selected_label = st.sidebar.selectbox("Type of crime:", crime_labels)
selected_crime = crime_codes[crime_labels.index(selected_label)]

shapes = load_shapes(geo_level)
criminality_filtered = filter_crime_by_level(criminality, geo_level)

# var calc
if selected_crime:
    var_df = calc_rate_variation(criminality_filtered, selected_crime)
else:
    st.warning("No crime selected")
    st.stop()

gdf = shapes.merge(var_df, left_on="NUTS_ID", right_on="REF_AREA")

# check valid data
n_valid = gdf["VAR"].notna().sum()

if n_valid == 0:
    st.error("No available data for this type of crime")
else:
    # map
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
            "MEAN_PRE": ":.1f",
            "COVID_2020": ":.1f",
            "AREA_NAME": False,
            "REF_AREA": False
        },
        labels={
            "VAR": "Variation %",
            "MEAN_PRE": "Mean rate 2014-19",
            "COVID_2020": "Rate 2020"
        }
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700)

    st.plotly_chart(fig, width="stretch")

    # stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Variation mean", f"{gdf['VAR'].mean():.1f}%")
    col2.metric("Min", f"{gdf['VAR'].min():.1f}%")
    col3.metric("Max", f"{gdf['VAR'].max():.1f}%")