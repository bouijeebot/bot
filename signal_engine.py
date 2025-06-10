import gspread
from main import send_signal, get_credentials, SHEET_ID
from datetime import datetime
import time

def generate_signals_and_dispatch():
    try:
        creds = get_credentials()
        gc = gspread.authorize(creds)

        # === 1. Läs senaste signal från Google Sheets-bladet "AI_Signals" ===
        signal_sheet = gc.open_by_key(SHEET_ID).worksheet("AI_Signals")
        rows = signal_sheet.get_all_records()

        if not rows:
            print("🚫 Inga signaler hittades i AI_Signals.")
            return

        latest = rows[-1]  # Sista raden = senaste signal

        action = latest.get("Signal", "").strip().upper()
        symbol = latest.get("Symbol", "GBPUSD").strip().upper()
        timestamp = latest.get("Timestamp", "")

        if action not in ["BUY", "SELL"]:
            print(f"⚠️ Ogiltig signal: {action}")
            return

        # === 2. Skicka till alla användare ===
        user_sheet = gc.open_by_key(SHEET_ID).worksheet("Users")
        users = user_sheet.get_all_records()

        for user in users:
            chat_id = user.get("Telegram-ID")
            if chat_id:
                try:
                    send_signal(action, symbol, chat_id)
                    print(f"✅ {action} {symbol} skickad till {chat_id} ({timestamp})")
                except Exception as e:
                    print(f"❌ Kunde inte skicka till {chat_id}: {e}")

    except Exception as err:
        print(f"🚨 Fel i generate_signals_and_dispatch: {err}")
