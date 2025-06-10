import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm

def download_dukascopy(pair, from_date, to_date, timeframe="m1", output_file=None):
    base_url = "https://datafeed.dukascopy.com/datafeed"
    tf_map = {"m1": "60"}
    pair = pair.upper()

    if "_" in pair:
        pair = pair.replace("_", "")

    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")
    delta = timedelta(minutes=1)

    rows = []
    now = from_dt

    print(f"Hämtar {pair} från {from_date} till {to_date}...")

    while now <= to_dt:
        y, m, d, h = now.year, now.month, now.day, now.hour
        url = f"{base_url}/{pair}/{y}/{m - 1:02d}/{d:02d}/{h:02d}h_ticks.bi5"

        r = requests.get(url, stream=True)
        if r.status_code == 200:
            # Spara och läs binärfil – eller markera som tillgänglig datapunkt
            rows.append({
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "source": url
            })

        now += delta

    df = pd.DataFrame(rows)
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"✅ Klar! {len(df)} datapunkter sparade till: {output_file}")
    else:
        print(df.head())

# EXEMPEL
if __name__ == "__main__":
    download_dukascopy("EURUSD", "2020-01-01", "2020-01-01", output_file="eurusd_2020_01_01.csv")
