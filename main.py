import os
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import threading
from keep_alive import keep_alive

# === Ladda miljövariabler ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDENTIALS_FILE = "credentials.json"

bot = telebot.TeleBot(TOKEN)

# === Google Sheets funktioner ===
def get_credentials():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    return Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)

def log_signal_to_sheet(sheet_name, values):
    creds = get_credentials()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(sheet_name)
    worksheet.append_row(values)

def get_user_balance(telegram_id):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    for row in sheet.get_all_records():
        if str(row.get("Telegram-ID")) == str(telegram_id):
            return row.get("Saldo", "Ej angivet")
    return "Ej hittad"

def get_user_risk(telegram_id):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    for row in sheet.get_all_records():
        if str(row.get("Telegram-ID")) == str(telegram_id):
            return row.get("Risknivå", "Ej angiven")
    return "Ej angiven"

def update_user_risk(telegram_id, risk_level):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    all_values = sheet.get_all_values()
    for i, row in enumerate(all_values):
        if str(row[0]) == str(telegram_id):  # Telegram-ID antas vara i kolumn A
            sheet.update_cell(i + 1, 3, f"{risk_level}%")  # Risknivå antas vara i kolumn C
            return

# === /start ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✨NU KÖR VI!✨", callback_data="demo_signal"))
    bot.send_message(
        message.chat.id,
        "Heeey din katt! 😻✨\n\n"
        "Jag är *Bouijee Bot* – din fab trading-bestie som sniffar pengar snabbare än du hittar dina klackar en lördagkväll. 👠💸\n\n"
        "När jag säger *BUY💚* eller *SELL💔*, så bör signalen accepteras inom rätt tid för bästa resultat. 📉📈\n\n"
        "Så häll upp ett glas bubbel 🥂, luta dig tillbaka, och låt mig servera dig signaler med mer precision än din eyeliner.\n\n"
        "Let’s get rich – men make it fabulous.\n\n"
        "Xoxo NU KÖR VI! 💃🏽\n\n"
        "*Klicka bara på knappen när du är redo att glänsa!*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# === /meny ===
@bot.message_handler(commands=["meny"])
def show_menu(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Mitt konto 💼", callback_data="mitt_konto"),
        InlineKeyboardButton("ℹ️ Info", callback_data="info"),
        InlineKeyboardButton("⚖️ Risknivå", callback_data="risknivå"),
        InlineKeyboardButton("💃🏽 Invänta signal", callback_data="standby")
    )
    bot.send_message(message.chat.id, "✨ *Bouijee Bot Meny* ✨\n\nVad vill du göra nu, babes?🤷🏽‍♀️", reply_markup=markup, parse_mode="Markdown")

def send_standby_button(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💃🏽 Invänta signal", callback_data="standby"))
    bot.send_message(chat_id, "Klicka för att börja ta emot signaler, darling!✨", reply_markup=markup)

# === Menyknappar ===
@bot.callback_query_handler(func=lambda call: call.data == "demo_signal")
def show_main_menu(call):
    show_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "standby")
def handle_standby(call):
    bot.send_message(call.message.chat.id, "Snyggt! Då pingar jag dig så snart nästa signal kommer, babes! 🥂")

# === Info ===
@bot.callback_query_handler(func=lambda call: call.data == "info")
def show_info(call):
    info_text = (
        "*ℹ️ Hur funkar Bouijee Bot?*\n\n"
        "Bouijee Bot skickar fab trading-signaler direkt till dig. Du väljer om du vill godkänna varje trade. 👍🏼\n\n"
        "Vi använder en liten del av ditt konto per trade – vilket skyddar dig från drama på marknaden.\n\n"
        "Bouijee kan inte heller påverka ditt saldo, det är bara du som har åtkomst till ditt konto, just sayin. 💅🏼\n\n"
        "✨ *Rekommenderad första insättning*: $1000 USD\n\n"
        "Men du kan börja med vad du vill – och fylla på när du vill, för att ta ditt konto från *cute* till *cash queen*. 👑\n\n"
        "⚖️ *Risk per signal*:\n"
        "Du väljer mellan 1%, 2% eller 3% av ditt saldo.\n\n"
        "Professionella traders håller sig ofta till:\n"
        "• 1% – (Låg risk) Safe & classy 💁🏽‍♀️\n"
        "• 2% – (Medel risk) Lite spice men fortfarande safe 🌶️\n"
        "• 3% – (Hög risk) Bold babe-mode: mer vinst, mer risk! 🫣\n\n"
        "*Självklart får du välja själv, men Bouijee rekommenderar 1–2% för att hålla det classy och hållbart. Du kan alltid ändra ditt val i menyn.*\n\n",
    )

    bot.send_message(
        call.message.chat.id,
        info_text,
        parse_mode="Markdown"
    )

    # Visa standby-knapp efter infon
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💃🏽 Invänta signal", callback_data="standby"))
    bot.send_message(
        call.message.chat.id,
        "När du är redo att glänsa, klicka här så väntar vi in nästa signal tillsammans!🫶🏼",
        reply_markup=markup
    )

# === Risknivåval ===
@bot.callback_query_handler(func=lambda call: call.data == "risknivå")
def choose_risk_level(call):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("1%", callback_data="risk_1"),
        InlineKeyboardButton("2%", callback_data="risk_2"),
        InlineKeyboardButton("3%", callback_data="risk_3")
    )
    bot.send_message(
        call.message.chat.id,
        "💫 Välj hur mycket av ditt saldo du vill riska per signal:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("risk_"))
def handle_risk_selection(call):
    risk = call.data.split("_")[1]
    update_user_risk(call.from_user.id, risk)
    bot.send_message(
        call.message.chat.id,
        f"Risknivå uppdaterad till {risk}% – classy move!🍹",
        parse_mode="Markdown"
    )

    # Visa standby-knapp efter val
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💃🏽 Invänta signal", callback_data="standby"))
    bot.send_message(
        call.message.chat.id,
        "Redo för att få signaler direkt i din feed? Klicka här, babes!✅",
        reply_markup=markup
    )


# === Konto/Statistik ===
@bot.callback_query_handler(func=lambda call: call.data == "mitt_konto")
def handle_mitt_konto(call):
    telegram_id = call.from_user.id
    saldo = get_user_balance(telegram_id)
    risk = get_user_risk(telegram_id)

    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Signals")
    rows = sheet.get_all_records()

    user_first_name = call.from_user.first_name or "Okänd"
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    vinster = 0
    forluster = 0
    total_pnl = 0

    for row in rows:
        try:
            row_time = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M")
        except:
            continue
        if row["User"] == user_first_name and row_time >= week_ago:
            try:
                pnl = float(row.get("Profit", 0))
            except:
                pnl = 0
            total_pnl += pnl
            if pnl > 0:
                vinster += 1
            elif pnl < 0:
                forluster += 1

    total_signaler = vinster + forluster
    win_rate = round((vinster / total_signaler) * 100, 1) if total_signaler > 0 else 0

    text = (
        f"**Ditt konto**\n"
        f"💰 Saldo: {saldo} USD\n"
        f"⚖️ Risk per trade: {risk}\n\n"
        f"**Senaste 7 dagarna**\n"
        f"💚 Vinster: {vinster}\n"
        f"💔 Förluster: {forluster}\n"
        f"🏆 Win rate: {win_rate}%\n\n"
        f"📊 Total PnL: {round(total_pnl, 2)} USD"
    )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅️ Tillbaka till meny", callback_data="demo_signal"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# === Bekräfta signal ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def handle_confirm_signal(call):
    action = call.data.split("_")[1].upper()
    symbol = "EURUSD"
    user = call.from_user.first_name or "Okänd"
    telegram_id = call.from_user.id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    risk = get_user_risk(telegram_id)
    saldo = get_user_balance(telegram_id)
    try:
        saldo = float(saldo)
        risk_value = round((float(risk.strip('%')) / 100) * saldo, 2)
    except:
        risk_value = "Ej beräknat"

    bot.send_message(call.message.chat.id, f"Signal *{action}* bekräftad för ~{risk}% av ditt saldo ({risk_value} USD). Let's gooo!💃🏽", parse_mode="Markdown")
    log_signal_to_sheet("Signals", [timestamp, user, telegram_id, "SIGNAL", action, "", "", ""])

# === Skicka signal ===
def send_signal(action, symbol="EURUSD", chat_id=None):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👍🏼", callback_data=f"confirm_{action.lower()}"))
    message_text = f"🔥 *SIGNAL* 🔥\n\n{action.upper()} {symbol}\n\nGodkänn om du är redo att glänsa ✨"
    bot.send_message(chat_id=chat_id, text=message_text, reply_markup=markup, parse_mode="Markdown")

# === Automatiskt notifiera resultat ===
def check_signals_result():
    try:
        creds = get_credentials()
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).worksheet("Signals")
        rows = sheet.get_all_records()

        for row in reversed(rows):
            user = row.get("User")
            telegram_id = row.get("Telegram-ID")
            profit = row.get("Profit")
            notified = row.get("Notified", "").lower()

            if not telegram_id or notified == "yes" or profit == "":
                continue

            try:
                profit = float(profit)
                telegram_id = int(telegram_id)
            except:
                continue

            if profit > 0:
                text = f"YESSS! {profit} USD i vinst!🎉"
            elif profit < 0:
                text = f"Jikes… {abs(profit)} USD i förlust💔"
            else:
                continue

            bot.send_message(chat_id=telegram_id, text=text)
            row_index = rows.index(row) + 2
            sheet.update_cell(row_index, 8, "Yes")

        threading.Timer(300, check_signals_result).start()
    except Exception as e:
        print("Fel i check_signals_result:", e)
        threading.Timer(300, check_signals_result).start()

# === Automatiskt påminna om saknat resultat ===
def check_for_missing_results():
    try:
        creds = get_credentials()
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).worksheet("Signals")
        rows = sheet.get_all_records()

        for row in reversed(rows):
            timestamp_str = row.get("Timestamp")
            profit = row.get("Profit", "")
            notified = row.get("Notified", "").lower()
            telegram_id = row.get("Telegram-ID")

            if not timestamp_str or notified == "yes" or profit != "":
                continue

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                telegram_id = int(telegram_id)
            except:
                continue

            if datetime.now() - timestamp > timedelta(minutes=30):
                msg = (
                    "Hmm... inget resultat än på din senaste signal. "
                    "Marknaden spelar svårflörtad just nu – vi håller tummarna!✨"
                )
                bot.send_message(chat_id=telegram_id, text=msg)
                row_index = rows.index(row) + 2
                sheet.update_cell(row_index, 8, "Yes")

        threading.Timer(300, check_for_missing_results).start()
    except Exception as e:
        print("Fel i check_for_missing_results:", e)
        threading.Timer(300, check_for_missing_results).start()

# === Text fallback ===
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_unexpected_messages(message):
    bot.send_message(
        message.chat.id,
        "Babe, tryck på en knapp istället – jag jobbar inte med DMs! ✨",
        parse_mode="Markdown"
    )

# === Starta ===
if __name__ == "__main__":
    print("Bouijee Bot är igång...")

    keep_alive()  # Startar Flask-servern på Render

    bot.remove_webhook()
    bot.set_webhook(url="https://bot-0xdn.onrender.com/")
