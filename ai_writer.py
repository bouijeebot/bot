import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# === Ladda miljövariabler ===
load_dotenv()
SHEET_ID = os.getenv("SHEET_ID")
service_account_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))

# === Autentisering ===
def get_credentials():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

# === Lägg till signal ===
def write_ai_signal(symbol: str, signal: str):
    try:
        creds = get_credentials()
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).worksheet("AI_Signals")

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [now, symbol.upper(), signal.upper()]

        # Lägg till raden längst ner
        sheet.append_row(row)
        print(f"✅ AI-signal loggad: {row}")

    except Exception as e:
        print(f"❌ Kunde inte skriva AI-signal: {e}")

# === EXEMPEL: anropa funktionen ===
if __name__ == "__main__":
    # Exempel – AI säger BUY på GBPUSD
    write_ai_signal("GBPUSD", "BUY")
