import pandas as pd
import geopandas as gpd
from scripts.utils import fix_sardinia_codes

crime = pd.read_parquet("data/processed/crime_clean.parquet")
criminality = pd.read_parquet("data/processed/criminality_clean.parquet")

prov_shape = gpd.read_parquet("data/shapes/nuts3_it.geoparquet")


prov_shape_filterd = fix_sardinia_codes(prov_shape)

crime = crime[crime["REF_AREA"].isin(prov_shape_filterd["NUTS_ID"])]

# gdf = prov_shape.merge(crime, left_on="NUTS_ID", right_on="REF_AREA")

threshold = 1000

pre_covid_crime = crime[crime["TIME_PERIOD"].between(2014, 2019)]

sum_per_year = (
    pre_covid_crime
    .groupby(["TIME_PERIOD", "TYPE_CRIME"])["OBS_VALUE"]
    .sum()
)

mean_pre_covid = sum_per_year.groupby("TYPE_CRIME").mean()

valid_crimes = mean_pre_covid[mean_pre_covid >= threshold].index

covid_crime = (
    crime[crime["TIME_PERIOD"] == 2020]
    .groupby("TYPE_CRIME")["OBS_VALUE"]
    .sum()
)

common_crime = valid_crimes.intersection(covid_crime.index)

variation = (
    (covid_crime.loc[common_crime] - mean_pre_covid.loc[common_crime])
    / mean_pre_covid.loc[common_crime]
    * 100
).sort_values()

print(variation)



