import pandas as pd

def convert_m1_to_1h(input_csv, output_csv):
    rows = []

    with open(input_csv, "r") as f:
        for line in f:
            # Hoppa över raden om den innehåller "datetime" (rubrikrad)
            if "datetime" in line.lower():
                continue

            parts = line.strip().split(",")
            if len(parts) == 6:
                rows.append(parts)

    df = pd.DataFrame(rows, columns=["datetime", "open", "high", "low", "close", "volume"])

    # Konvertera till rätt typer
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])

    df.set_index("datetime", inplace=True)

    df_1h = df.resample("1H").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()

    df_1h.reset_index(inplace=True)
    df_1h.to_csv(output_csv, index=False)
    print(f"✅ Klar! Sparade som {output_csv}")
