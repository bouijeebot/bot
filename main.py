from flask import Flask, request
import os
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import threading
import random
import time
from pytz import timezone
import json

# === Pending signals för påminnelser ===
pending_signals = []
awaiting_balance_input = {}

# === Ladda miljövariabler ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDENTIALS_FILE = "credentials.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bouijee Bot är igång!", 200

@app.route("/", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

def get_credentials():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\n", "
")
    return Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

# === Starta AI-loop innan den anropas ===
def start_ai_signal_loop():
    import os
    import time
    from convert_to_1h import convert_m1_to_1h
    from macd_ai_to_sheets import run_macd_strategy

    def loop():
        while True:
            try:
                convert_m1_to_1h("DAT_ASCII_GBPUSD_M1_ALL.csv", "GBPUSD_1h.csv")
                run_macd_strategy("GBPUSD_1h.csv", "GBPUSD")
                print("✅ AI-signal genererad och sparad till Google Sheets")
            except Exception as e:
                print("❌ AI-signal loop error:", e)
            time.sleep(3600)

    threading.Thread(target=loop, daemon=True).start()

# === Resultatnotifiering + saldouppdatering ===
def check_signals_result():
    try:
        creds = get_credentials()
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).worksheet("Signals")
        rows = sheet.get_all_records()
        already_notified = set()

        for row in reversed(rows):
            telegram_id = row.get("Telegram-ID")
            profit = row.get("Profit")
            accepted = row.get("Accepted", "").strip().lower()
            signal_text = row.get("Signal", "").strip()

            if not telegram_id or profit == "":
                continue
            try:
                profit = float(profit)
                telegram_id = int(telegram_id)
            except:
                continue

            if (telegram_id, signal_text) in already_notified:
                continue

            try:
                entry_time = row.get("Timestamp", "").split(" ")[1]
            except:
                entry_time = "okänt"

            if accepted == "yes":
                msg = f"✅ {signal_text} kl {entry_time} = {'+' if profit > 0 else ''}{profit} USD 🎉" if profit != 0 else f"✅ {signal_text} kl {entry_time} = ±0 USD 😐"
            else:
                result = "WIN🏆" if profit > 0 else "LOSS💀"
                msg = f"❌ Missad signal: {signal_text} kl {entry_time} = {result}"
            bot.send_message(chat_id=telegram_id, text=msg)
            already_notified.add((telegram_id, signal_text))

        update_all_user_balances()

    except Exception as e:
        print("⚠️ check_signals_result error:", e)

    threading.Timer(300, check_signals_result).start()

def update_all_user_balances():
    creds = get_credentials()
    gc = gspread.authorize(creds)
    user_sheet = gc.open_by_key(SHEET_ID).worksheet("Users")
    signal_sheet = gc.open_by_key(SHEET_ID).worksheet("Signals")
    user_data = user_sheet.get_all_records()
    signal_data = signal_sheet.get_all_records()

    for i, user in enumerate(user_data):
        telegram_id = str(user.get("Telegram-ID"))
        if not telegram_id:
            continue
        try:
            saldo = float(user.get("Balance", user.get("Saldo", 0)))
        except:
            saldo = 0
        total_profit = sum(
            float(row.get("Profit", 0)) for row in signal_data
            if str(row.get("Telegram-ID")) == telegram_id and str(row.get("Accepted", "")).strip().lower() == "yes"
        )
        nytt_saldo = round(saldo + total_profit, 2)
        saldo_col = None
        headers = user_sheet.row_values(1)
        for idx, header in enumerate(headers):
            if header.strip().lower() in ["balance", "saldo"]:
                saldo_col = idx + 1
                break
        if saldo_col:
            user_sheet.update_cell(i + 2, saldo_col, nytt_saldo)
    print("✅ Alla användarsaldon har uppdaterats!")
