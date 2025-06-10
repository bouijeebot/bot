import pandas as pd
import numpy as np
from datetime import datetime
from ai_writer import write_ai_signal

# === Läser CSV med OHLCV-data ===
df = pd.read_csv("your_forex_data.csv")

# === Skapa kolumn 'datetime' om inte finns ===
if "datetime" not in df.columns and "Date" in df.columns:
    df.rename(columns={"Date": "datetime"}, inplace=True)

# === Omvandla tidsformat korrekt ===
df['datetime'] = pd.to_datetime(df['datetime'])
df.sort_values('datetime', inplace=True)

# === MACD-beräkning ===
def calculate_macd(data, fast=12, slow=26, signal=9):
    data['EMA_fast'] = data['Close'].ewm(span=fast, adjust=False).mean()
    data['EMA_slow'] = data['Close'].ewm(span=slow, adjust=False).mean()
    data['MACD'] = data['EMA_fast'] - data['EMA_slow']
    data['MACD_signal'] = data['MACD'].ewm(span=signal, adjust=False).mean()
    return data

df = calculate_macd(df)

# === Avgör senaste signal ===
latest = df.iloc[-1]
macd = latest['MACD']
macd_signal = latest['MACD_signal']

if macd > macd_signal:
    signal = "BUY"
elif macd < macd_signal:
    signal = "SELL"
else:
    signal = None

# === Skriv till Google Sheets ===
if signal:
    write_ai_signal("GBPUSD", signal)
else:
    print("⚠️ Ingen tydlig signal denna gång.")
