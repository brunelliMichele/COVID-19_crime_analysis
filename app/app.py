import streamlit as st

st.set_page_config(
    page_title="COVID-19 and criminality in Italy",
    layout="wide"
)

pages = {
    "Home": [
        st.Page("pages/home.py", title="Home"),
    ],
    "Analysis": [
        st.Page("pages/01_variation_maps.py", title="Spatial Distribution of Crime Changes"),
        st.Page("pages/02_moran.py", title="Spatial Autocorrelation Analysis"),
    ]
}

pg = st.navigation(pages)
pg.run()