import streamlit as st
import pandas as pd
from utils import (
    load_criminality_data, filter_crime_by_level, 
    calc_period_variation,get_all_variations,
    BASELINE, PERIODS
)

CRIME_TYPES = {
    "PICKTHEF": "Pickpocketing",
    "BAGTHEF": "Snatch theft",
    "BURGTHEF": "Residential burglary",
    "STREETROB": "Street robbery",
    "RAPE": "Sexual assault",
    "CYBERCRIM": "Cybercrime",
    "SWINCYB": "Online fraud and cyber scams",
    "PORNO": "Child sexual abuse material (CSAM) offences"
}

st.title("COVID-19 and criminality in Italy")
st.markdown("""
This interactive dashboard explores how the COVID-19 pandemic
reshaped the spatial distribution and intensity of crimes across
Italian provinces, regions and macro-areas from 2014 to 2023.
""")

# ---------- Calculate all variations ----------
variations_national = get_all_variations()

# get specific values
def get_national_var(code: str) -> float:
    row = variations_national[variations_national["code"] == code]
    return row["variation_pct"].values[0] if len(row) > 0 else 0.0


# ---------- Key Findings with Geographic Level Selection ----------
st.header("Key Findings")

# geographic level selector
geo_level = st.radio(
    "Select geographic level:",
    ["provinces", "regions", "macro-areas"],
    format_func=lambda x: x.capitalize().replace("-", " "),
    horizontal=True
)

# load and filter data
crime_data = load_criminality_data()
crime_data = filter_crime_by_level(crime_data, geo_level)

# calculate variations for each crime type
variations_list = []

for code, name in CRIME_TYPES.items():
    for period_name, (start, end) in PERIODS.items():
        var_df = calc_period_variation(crime_data, code, BASELINE, (start, end))

        if len(var_df) > 0:
            mean_var = var_df["VAR"].mean()
            variations_list.append({
                "Crime Type": name,
                "Period": period_name,
                "Average Variation (%)": mean_var
            })

# create and pivot dataframe
if variations_list:
    variations_df = pd.DataFrame(variations_list)

    # pivot to have periods as columns
    pivot_df = variations_df.pivot(
        index="Crime Type",
        columns="Period",
        values="Average Variation (%)"
    ).reset_index()

    # round values
    for col in pivot_df.columns:
        if col != "Crime Type":
            pivot_df[col] = pivot_df[col].round(1)
        
    # display as styled dataframe
    st.dataframe(
        pivot_df,
        hide_index=True,
        column_config={
            "Crime Type": st.column_config.TextColumn("Crime Type", width="medium"),
            "During COVID (2020-2021)": st.column_config.NumberColumn(
                "During COVID (%)",
                format="%.1f%%"
            ),
            "Post-COVID (2022-2023)": st.column_config.NumberColumn(
                "Post-COVID (%)",
                format="%.1f%%"
            ),
        },
        width="stretch"
    )

    # add color-coded interpretation
    st.info("""
    **Legend:**
    - **Negative values**: Crime rate decreased compare to pre-COVID baseline (2014-19)
    - **Positive values**: Crime rate increased compare to pre-COVID baseline (2014-19)
    """)
else:
    st.warning("No data available for the selected crimes")

total_var = get_national_var("TOT")
st.markdown(f"""
**Compositional Shift Hypothesis:** 

While total reported crimes changed by {total_var:+.1f}% during COVID-19, the data reveals 
a potential **displacement effect** from physical to digital crime. This pattern is consistent 
with reduced opportunities for contact-based offenses (due to lockdowns and reduced mobility) 
and increased opportunities for cyber-enabled crimes (increased online activity during 
remote work/education).

⚠️ **Note:** Correlation does not imply causation. Multiple factors beyond pandemic restrictions 
may have contributed to these patterns.
""")

# ---------- Data & Methods ----------
st.markdown("---")
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
st.header("Limitations")

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