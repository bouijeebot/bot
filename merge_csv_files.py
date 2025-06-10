import pandas as pd
import os

# Lista alla år
years = ["2020", "2021", "2022", "2023", "2024"]
dfs = []

for year in years:
    filename = f"DAT_ASCII_GBPUSD_M1_{year}.csv"
    if os.path.exists(filename):
        print(f"Laddar {filename}")
        df = pd.read_csv(filename, header=None)
        dfs.append(df)
    else:
        print(f"⚠️ Fil saknas: {filename}")

# Slå ihop och spara
combined_df = pd.concat(dfs)
combined_df.to_csv("DAT_ASCII_GBPUSD_M1_ALL.csv", index=False, header=False)
print("✅ Alla CSV-filer har kombinerats till DAT_ASCII_GBPUSD_M1_ALL.csv")
