import pandas as pd
import os

# Lista över CSV-filer i rätt ordning
filnamn = [
    "DAT_ASCII_GBPUSD_M1_2020.csv",
    "DAT_ASCII_GBPUSD_M1_2021.csv",
    "DAT_ASCII_GBPUSD_M1_2022.csv",
    "DAT_ASCII_GBPUSD_M1_2023.csv",
    "DAT_ASCII_GBPUSD_M1_2024.csv",
]

dataframes = []

for fil in filnamn:
    if os.path.exists(fil):
        print(f"✅ Läser in {fil}")
        df = pd.read_csv(fil, header=None, names=["datetime", "open", "high", "low", "close", "volume"])
        dataframes.append(df)
    else:
        print(f"⚠️ Fil saknas: {fil}")

# Slå ihop filerna
sammanlagt_df = pd.concat(dataframes)

# Spara till en enda fil
sammanlagt_df.to_csv("GBPUSD_2019_2024_M1.csv", index=False)
print("🎉 Klar! All data sparad i 'GBPUSD_2019_2024_M1.csv'")
