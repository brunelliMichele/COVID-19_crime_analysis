import streamlit as st
import plotly.express as px
from utils import load_crime_data, load_shapes, calc_variation

st.title("Choropleth Maps")

crimes = load_crime_data()
shapes = load_shapes()

# filter's sidebar
crime_types = sorted(crimes["TYPE_CRIME"].unique())
selected_crimes = st.sidebar.selectbox(
    "Type of crime", 
    crime_types, 
    index=crime_types.index("PICKTHEF") if "PICKTHEF" in crime_types else 0
)

# var calc
if selected_crimes:
    var_df = calc_variation(crimes, selected_crimes)
else:
    st.warning("No crime selected")
    
gdf = shapes.merge(var_df, left_on="NUTS_ID", right_on="REF_AREA")

# map
fig = px.choropleth_mapbox(
    gdf,
    geojson=gdf.geometry.__geo_interface__,
    locations=gdf.index,
    color="VAR",
    color_continuous_scale="RdYlGn_r",
    range_color=[-80, 80],
    mapbox_style="carto-positron",
    center={"lat": 42.0, "lon": 12.5},
    zoom=5,
    hover_data={"AREA_NAME": True, "VAR": ":.1f"},
    labels={"VAR": "Variation %"}
)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700)

st.plotly_chart(fig, use_container_width=True)

# stats
col1, col2, col3 = st.columns(3)
col1.metric("Variation's mean", f"{gdf["VAR"].mean():.1f}%")
col2.metric("Min", f"{gdf['VAR'].min():.1f}%")
col3.metric("Max", f"{gdf['VAR'].max():.1f}%")