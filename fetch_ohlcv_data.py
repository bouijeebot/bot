import os
import struct
import requests
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import lzma
import io

def download_bi5(pair, dt):
    url = f"https://datafeed.dukascopy.com/datafeed/{pair}/{dt.year}/{dt.month - 1:02d}/{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return lzma.decompress(response.content)
        except lzma.LZMAError:
            print(f"⚠️  Trasig fil på {dt} – hoppar över.")
            return None
    return None

def decode_bi5(data):
    ticks = []
    stream = io.BytesIO(data)
    while True:
        record = stream.read(20)
        if len(record) < 20:
            break
        ms, ask, bid, ask_vol, bid_vol = struct.unpack('>IIIff', record)
        time = ms / 1000.0
        ticks.append((time, ask / 1e5, bid / 1e5, ask_vol, bid_vol))
    return ticks

def to_ohlcv(ticks, base_dt):
    df = pd.DataFrame(ticks, columns=["time", "ask", "bid", "ask_vol", "bid_vol"])
    df["datetime"] = [base_dt + timedelta(seconds=t) for t in df["time"]]
    df.set_index("datetime", inplace=True)

    df["price"] = (df["ask"] + df["bid"]) / 2
    ohlc = df["price"].resample("1T").ohlc()
    ohlc["volume"] = df["ask_vol"].resample("1T").sum()
    return ohlc.dropna()

def download_ohlcv(pair, start_date, end_date, save_as="output.csv"):
    pair = pair.upper().replace("_", "")
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    current = start_dt

    all_data = []

    print(f"Hämtar och konverterar data för {pair} från {start_date} till {end_date}...")

    while current <= end_dt:
        for hour in range(24):
            dt = current.replace(hour=hour)
            raw = download_bi5(pair, dt)
            if raw:
                ticks = decode_bi5(raw)
                ohlc = to_ohlcv(ticks, dt)
                all_data.append(ohlc)

        current += timedelta(days=1)

    if all_data:
        df_all = pd.concat(all_data)
        df_all.reset_index(inplace=True)
        df_all.columns = ["Timestamp", "Open", "High", "Low", "Close", "Volume"]
        df_all.to_csv(save_as, index=False)
        print(f"✅ Klar! Sparat till {save_as} ({len(df_all)} rader)")
    else:
        print("❌ Ingen data kunde hämtas.")

# EXEMPEL
if __name__ == "__main__":
    download_ohlcv("EURUSD", "2020-01-03", "2020-01-03", save_as="eurusd_ohlcv_20200103.csv")

