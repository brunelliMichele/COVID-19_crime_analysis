import streamlit as st
import pandas as pd
from utils import load_crime_data, get_all_variations


st.title("COVID-19 and criminality in Italy")
st.markdown("""
This interactive dashboard explores how the COVID-19 pandemic
reshaped the spatial distribution and intensity of crimes across
Italian provinces, regions and macro-areas from 2014 to 2023.
""")

# ---------- Calculate all variations ----------
variations_df = get_all_variations()

# get specific values
def get_var(code: str) -> float:
    row = variations_df[variations_df["code"] == code]
    return row["variation_pct"].values[0] if len(row) > 0 else 0.0

bankrob = get_var("BANKROB")
pickthef = get_var("PICKTHEF")
cybercrim = get_var("CYBERCRIM")
swincyb = get_var("SWINCYB")


# ---------- Key Findings ----------
st.header("Key Findings")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Bank Robbery",
        value=f"{bankrob:+.0f}%",
        delta="During COVID",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="Pickpocketing",
        value=f"{pickthef:+.0f}%",
        delta="During COVID",
        delta_color="normal"
    )

with col3:
    st.metric(
        label="Cybercrime",
        value=f"{cybercrim:+.0f}%",
        delta="During COVID",
        delta_color="inverse"
    )

with col4:
    st.metric(
        label="Online Fraud",
        value=f"{swincyb:+.0f}%",
        delta="During COVID",
        delta_color="inverse"
    )


# ---------- The Pattern ----------
st.markdown("---")
st.header("The Pattern")

col1, col2 = st.columns(2)

# split into decreases and increases
decreases = variations_df[variations_df["variation_pct"] < 0].sort_values("variation_pct")
increases = variations_df[variations_df["variation_pct"] > 0].sort_values("variation_pct", ascending=False)

with col1:
    st.markdown("### Contact Crimes Dropped")
    st.markdown("Crimes requiring physical presence decreased significantly during lockdowns:")

    for _, row in decreases.iterrows():
        st.markdown(f"- **{row['name']}:** {row['variation_pct']:+.1f}%")

with col2:
    st.markdown("### Remote Crimes Increased")
    st.markdown("Crimes that can be commited remotly saw substantial increases:")

    for _, row in increases.iterrows():
        st.markdown(f"- **{row['name']}:** {row['variation_pct']:+.1f}%")

total_var = get_var("TOT")
st.markdown(f"""
---
**Overall:** Total crimes changed by {total_var:+.1f}%,
but the nature of crime shifted significantly from physical to digital.
""")

# ---------- Data & Methods ----------
st.header("Data & Methods")

st.markdown("""
**Data Source:** [ISTAT](https://www.istat.it/dati/banche-dati/) - Italian National Institute of Statistics

**Time Period:** 2014-2023 (10 years)
- Pre-COVID baseline: 2014-2019
- During COVID: 2020-2021
- Post-COVID recovery: 2022-2023
            
**Geographic Coverage:**
- 107 Italian provinces (NUTS-3)
- 20 Italian regions (NUTS-2)
- 5 Italian macro-areas (NUTS-1)
    1. Nort-West
    2. Nort-East
    3. Center
    4. South
    5. Islands
""")

# ---------- Navigation Guide ----------
st.markdown("---")
st.header("Explore the Dashboard")

st.markdown("""
| Page | Description |
|------|-------------|
| **Spatial Distribution** | Interactive maps showing crime variation (%) compared to pre-COVID baseline |
| **Spatial Autocorrelation** | Moran's I analysis to detect spatial clustering patterns |
| **LISA Transitions** | Track how hot spots and cold spots shifted between periods |
""")

# ---------- Limitations ----------
st.markdown("---")
st.markdown("""
- **Annual data only:** ISTAT provides yearly aggregates, so we cannot isolate the effect of specific lockdown periods (e.g., March-May 2020).
- **Reporting bias:** Some crimes (e.g., domestic violence) may be underreported during lockdowns when victims were confined with perpetrators.
- **Correlation ≠ Causation:** Changes in crime patterns may be influenced by factors beyond COVID-19 restrictions.            
""")

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