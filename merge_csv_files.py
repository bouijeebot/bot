import pandas as pd
import os

# Lista på filnamn i rätt ordning
filnamn = [
    "DAT_ASCII_GBPUSD_M1_2020.csv",
    "DAT_ASCII_GBPUSD_M1_2021.csv",
    "DAT_ASCII_GBPUSD_M1_2022.csv",
    "DAT_ASCII_GBPUSD_M1_2023.csv",
    "DAT_ASCII_GBPUSD_M1_2024.csv",
]

# Läs och slå ihop filerna
dataframes = []
for fil in filnamn:
    if os.path.exists(fil):
        df = pd.read_csv(fil, sep=";", names=["datetime", "open", "high", "low", "close", "volume"])
        dataframes.append(df)
    else:
        print(f"⚠️ Fil saknas: {fil}")

# Slå ihop till en enda DataFrame
sammanlagt_df = pd.concat(dataframes)
sammanlagt_df.to_csv("GBPUSD_2019_2024_M1.csv", index=False)

print("✅ Alla filer har slagits ihop till 'GBPUSD_2019_2024_M1.csv'")
