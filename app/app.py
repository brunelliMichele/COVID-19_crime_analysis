import streamlit as st

st.set_page_config(
    page_title="COVID-19 and criminality in Italy",
    layout="wide"
)

st.title("COVID-19 and criminality in Italy")
st.markdown("""
Analysis of the impact of the pandemic on the spatial distribution 
and intensity of crimes in the Italian provinces (2014-2023).
""")

st.sidebar.success("Select a page")