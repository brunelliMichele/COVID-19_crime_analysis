import pandas as pd

df_1 = pd.read_parquet("data/processed/delittips_1_2014_2023.parquet")
df_9 = pd.read_parquet("data/processed/delittips_9_2014_2023.parquet")

df_1["REF_AREA"] = df_1["REF_AREA"].astype(str)

italy = df_1[df_1["REF_AREA"] == "IT"].copy()
macro = df_1[df_1["REF_AREA"].str.len() == 3].copy()
regions = df_1[df_1["REF_AREA"].str.len() == 4].copy()
provinces = df_1[df_1["REF_AREA"].str.len() == 5].copy()

print(df_1["REF_AREA"].nunique(), macro["REF_AREA"].nunique(), regions["REF_AREA"].nunique(), provinces["REF_AREA"].nunique())

# rename = {
#     "REF_AREA": "prov_code",
#     "TIME_PERIOD": "year",
#     "TYPE_CRIME": "crime_code",
#     "OBS_VALUE": "value"
# }