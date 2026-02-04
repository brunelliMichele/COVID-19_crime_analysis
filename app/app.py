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
        st.Page("pages/01_map_1.py", title="Crime Variation Map"),
        st.Page("pages/02_map_2.py", title="Criminality Rate Variation"),
    ]
}

pg = st.navigation(pages)
pg.run()