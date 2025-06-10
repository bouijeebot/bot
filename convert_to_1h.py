# === convert_to_1h.py ===
import pandas as pd
from datetime import datetime

def convert_m1_to_1h(m1_path, out_path):
    df = pd.read_csv(m1_path, sep=';', names=["Date", "Time", "Open", "High", "Low", "Close", "Volume"])
    df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d.%m.%Y %H:%M")
    df.set_index("Datetime", inplace=True)

    ohlc_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    }

    df_1h = df.resample("1H").agg(ohlc_dict).dropna()
    df_1h.to_csv(out_path)
    print(f"✅ 1H-data sparad till {out_path}")


# === macd_ai_to_sheets.py ===
import pandas as pd
import numpy as np
from google_sheets import log_signal_to_sheet, get_credentials
import gspread
from datetime import datetime

def run_macd_strategy(csv_path, symbol):
    df = pd.read_csv(csv_path)

    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    action = None
    if last_row['MACD'] > last_row['Signal'] and prev_row['MACD'] <= prev_row['Signal']:
        action = "BUY"
    elif last_row['MACD'] < last_row['Signal'] and prev_row['MACD'] >= prev_row['Signal']:
        action = "SELL"

    if action:
        creds = get_credentials()
        gc = gspread.authorize(creds)
        user_sheet = gc.open_by_key("SHEET_ID_PLACEHOLDER").worksheet("Users")
        users = user_sheet.get_all_records()

        for user in users:
            chat_id = user.get("Telegram-ID")
            if chat_id:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                mt4_id = user.get("MT4-ID", "Ej angivet")
                values = [
                    timestamp,
                    chat_id,
                    mt4_id,
                    symbol,
                    "",
                    "",
                    action,
                    "Yes",
                    ""
                ]
                log_signal_to_sheet("Signals", values)
                print(f"✅ AI-signal ({action} {symbol}) skickad till {chat_id}")
    else:
        print("ℹ️ Inget tydligt MACD-kors – ingen signal skickad denna timme.")
