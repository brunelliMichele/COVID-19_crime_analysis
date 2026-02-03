import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from app.utils import fix_sardinia_codes

DF_CRIME = pd.read_parquet("data/processed/crime_clean.parquet")
SHAPE = gpd.read_parquet("data/shapes/nuts3_it.geoparquet")
CRIME = "PICKTHEF"
THRESHOLD = 1000

FILTERED_SHAPE = fix_sardinia_codes(SHAPE)

DF_CRIME = DF_CRIME[DF_CRIME["REF_AREA"].isin(FILTERED_SHAPE["NUTS_ID"])]

pre_covid = DF_CRIME[(DF_CRIME["TIME_PERIOD"].between(2014, 2019)) & (DF_CRIME["TYPE_CRIME"] == CRIME)]
pre_covid_mean = pre_covid.groupby("REF_AREA")["OBS_VALUE"].mean()

covid = DF_CRIME[(DF_CRIME["TIME_PERIOD"] == 2020) & (DF_CRIME["TYPE_CRIME"] == CRIME)]
covid_sum = covid.groupby("REF_AREA")["OBS_VALUE"].sum()

var_prov = ((covid_sum - pre_covid_mean) / pre_covid_mean * 100)

var_df = var_prov.reset_index()
var_df.columns = ["REF_AREA", "VAR"]

gdf = FILTERED_SHAPE.merge(var_df, left_on="NUTS_ID", right_on="REF_AREA")

# plot
fig, ax = plt.subplots(1, 1, figsize=(12, 14))
gdf.plot(
    column="VAR",
    cmap="RdYlGn_r",
    legend=True,
    legend_kwds={"label": "Varation % (mean 2014-19 vs 2020)"},
    edgecolor="black",
    linewidth=0.3,
    ax=ax
)
ax.set_title(f"Variation {CRIME} - COVID 2020", fontsize=14)
ax.axis("off")
plt.tight_layout()
plt.savefig("outputs/map_pickthef.png", dpi=150)
plt.show()