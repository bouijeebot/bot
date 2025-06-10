import pandas as pd
from main import send_signal, get_credentials, SHEET_ID
import gspread

def generate_signals_and_dispatch():
    try:
        # === Läs signal-DataFrame från .csv, AI eller Sheets ===
        df = pd.read_csv("gbpusd_signals.csv")  # <-- byt till din faktiska datakälla
        latest = df[df["signal"].isin(["BUY", "SELL"])].tail(1)

        # === Hämta alla Telegram-användare från Sheets ===
        creds = get_credentials()
        gc = gspread.authorize(creds)
        users = gc.open_by_key(SHEET_ID).worksheet("Users").get_all_records()

        for _, row in latest.iterrows():
            action = row["signal"]
            symbol = "GBPUSD"  # Ändra om du vill inkludera fler par

            for user in users:
                chat_id = user.get("Telegram-ID")
                if chat_id:
                    try:
                        send_signal(action, symbol, chat_id)
                        print(f"✅ Signal skickad till {chat_id}: {action} {symbol}")
                    except Exception as e:
                        print(f"❌ Misslyckades att skicka till {chat_id}: {e}")

    except Exception as err:
        print(f"🚨 Fel i generate_signals_and_dispatch: {err}")
