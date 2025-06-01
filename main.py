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

# === Pending signals för påminnelser ===
pending_signals = []

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

# === Google Sheets funktioner ===
def register_user_if_not_exists(telegram_id):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    all_data = sheet.get_all_records()

    for row in all_data:
        if str(row.get("Telegram-ID")) == str(telegram_id):
            return  # Redan registrerad

    # Lägg till ny användare med alla standardvärden
    today = datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([telegram_id, 1000, "Ej angiven", today, 0, 0])  # TotalVinst och WinRate
    
import json

def get_credentials():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    
    # FIXA PRIVATE KEY MED RIKTIGA RADBRYTNINGAR
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    return Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

def log_signal_to_sheet(sheet_name, values):
    creds = get_credentials()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(sheet_name)

    # Validera rubriker
    expected_header = ["Timestamp", "User", "Telegram-ID", "Signal", "Result", "Profit", "Action", "Accepted", "Executed"]
    actual_header = worksheet.row_values(1)
    if actual_header != expected_header:
        raise ValueError(
            f"Felaktiga kolumnrubriker i bladet '{sheet_name}'.\n"
            f"Förväntat: {expected_header}\n"
            f"Hittat:    {actual_header}"
        )

    worksheet.append_row(values)

def log_trade_signal(telegram_id, user_name, symbol, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    values = [
    timestamp,
    user_name,
    telegram_id,
    symbol,
    "",      # Result
    "",      # Profit
    action,
    "Yes",   # Accepted
    ""       # Executed – fylls i senare av MT4
]
    log_signal_to_sheet("Signals", values)

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
        if str(row[0]) == str(telegram_id):  # Telegram-ID finns i kolumn A (index 0)
            sheet.update_cell(i + 1, 3, f"{risk_level}%")  # Risknivå finns i kolumn C (index 2, men +1 = 3)
            return

# === /start ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    telegram_id = str(message.from_user.id)
    register_user_if_not_exists(telegram_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✨NU KÖR VI!✨", callback_data="demo_signal"))

    bot.send_message(
        message.chat.id,
        "Heeey din katt! 😻✨\n\n"
        "Jag är *Bouijee Bot* – din fab trading-bestie som sniffar pengar snabbare än du hittar dina klackar en lördagkväll. 👠💸\n\n"
        "När jag säger *BUY💚* eller *SELL💔*, så bör signalen accepteras inom rätt tid för bästa resultat. 📉📈\n\n"
        "Så häll upp ett glas bubbel 🥂, luta dig tillbaka, och låt mig servera dig signaler med mer precision än din eyeliner.\n\n"
        "*Let’s get rich – men make it fabulous.*\n\n"
        "_Xoxo NU KÖR VI! 💃🏽_\n\n"
        "👉 Du kan skriva /meny när som helst för att återgå till menyn.",
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
        InlineKeyboardButton("📊 Valutapar info", callback_data="valutapar_info"),
    )
    markup.add(
        InlineKeyboardButton("⚖️ Risknivå", callback_data="risknivå"),
        InlineKeyboardButton("💃🏽 Invänta signal", callback_data="standby")
    )
    bot.send_message(
        message.chat.id,
        "✨ *Bouijee Bot Meny* ✨\n\nVad vill du göra nu, babes?🤷🏽‍♀️",
        reply_markup=markup,
        parse_mode="Markdown"
    )

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

@bot.callback_query_handler(func=lambda call: call.data in ["risk_1", "risk_2", "risk_3"])
def handle_risk_choice(call):
    telegram_id = str(call.from_user.id)
    risk_value = {
        "risk_1": "1%",
        "risk_2": "2%",
        "risk_3": "3%"
    }.get(call.data, "Ej angiven")

    try:
        creds = get_credentials()
        sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
        all_data = sheet.get_all_records()
        cell = None

        for idx, row in enumerate(all_data, start=2):  # Startar från rad 2 (efter header)
            if str(row.get("Telegram-ID")) == telegram_id:
                cell = f"C{idx}"  # Kolumn C = Risknivå
                break

        if cell:
            sheet.update_acell(cell, risk_value)
            bot.answer_callback_query(call.id, f"Risknivå satt till {risk_value} ⚖️")
        else:
            bot.answer_callback_query(call.id, "Kunde inte hitta din användare. 😢")

    except Exception as e:
        import traceback
        traceback.print_exc()
        bot.answer_callback_query(call.id, "Fel uppstod när risk skulle uppdateras. 😓")
        
# === Konto/Statistik ===
@bot.callback_query_handler(func=lambda call: call.data == "mitt_konto")
def handle_mitt_konto(call):
    print("==> mitt_konto tryck registrerad")
    try:
        import traceback

        telegram_id = call.from_user.id
        saldo = get_user_balance(telegram_id)
        risk = get_user_risk(telegram_id)

        if saldo is None or saldo == "":
            saldo = "Ej angivet"
        if risk is None or risk == "":
            risk = "Ej angiven"

        creds = get_credentials()
        sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Signals")
        rows = sheet.get_all_records()

        user_first_name = call.from_user.first_name or "Okänd"
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        vinster = 0
        forluster = 0
        total_pnl = 0
        missade = 0

        for row in rows:
            try:
                row_time = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M")
            except:
                continue

            if str(row.get("Telegram-ID")) == str(telegram_id):
                # Räkna missade trades
                if row.get("Accepted", "").strip().lower() != "yes":
                    missade += 1

                # Endast senaste veckan påverkar PnL-statistik
                if row_time >= week_ago:
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
            f"🏆 Win rate: {win_rate}%\n"
            f"📊 Total PnL: {round(total_pnl, 2)} USD\n"
            f"🚫 Missade trades: {missade}"
        )

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅️ Tillbaka till meny", callback_data="demo_signal"))
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        traceback.print_exc()
        bot.send_message(call.message.chat.id, "Oops! Kunde inte hämta kontoinformation just nu. Försök igen om en liten stund. 💔")

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
    log_trade_signal(telegram_id, user, symbol, action)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    telegram_id = call.from_user.id
    user = call.from_user.first_name or "Okänd"

    if call.data == "accept":
        for s in pending_signals:
            if s['user_id'] == telegram_id and not s['confirmed']:
                s['confirmed'] = True
                symbol = s.get("symbol", "EURUSD")
                action = s.get("action", "BUY")
                bot.send_message(call.message.chat.id, "Yaaas Let’s go!🥂")
                log_trade_signal(telegram_id, user, symbol, action)
                break

    elif call.data == "decline":
        bot.send_message(call.message.chat.id, "Got it babes🤫 vi tar nästa istället!")

# === Skicka signal ===
def send_signal(action, symbol="EURUSD", chat_id=None):
    from datetime import datetime, timedelta

    # 20 minuter framåt från nu
    entry_time_utc = datetime.utcnow() + timedelta(minutes=20)
    entry_time_local = datetime.now() + timedelta(minutes=20)
    entry_str = entry_time_local.strftime("%H:%M")

    # Lägg till signal i väntelistan för påminnelse
    pending_signals.append({
        'user_id': chat_id,
        'entry_time': entry_time_utc,
        'symbol': symbol,
        'action': action,
        'confirmed': False,
        'reminder_10': False,
        'reminder_5': False,
        'reminder_1': False
    })

    # Knappar
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅✅✅", callback_data="accept"),
        InlineKeyboardButton("❌❌❌", callback_data="decline")
    )

    # Bouijee-style meddelande
    message_text = (
        f"🔥 *MONEY RAIN* 🔥\n\n"
        f"{'💚' if action.upper() == 'BUY' else '💔'} *{action.upper()} {symbol}*\n"
        f"⏰ Entry: *{entry_str}*\n\n"
        "Take it or leave it 💅🏼"
    )

    bot.send_message(chat_id=chat_id, text=message_text, reply_markup=markup, parse_mode="Markdown")

def auto_generate_signal():
    pairs = ["USDCHF", "EURCHF", "EURUSD", "USDJPY", "EURJPY", "GBPUSD", "XAUUSD", "GBPJPY"]
    actions = ["BUY", "SELL"]
    
    chosen_pair = random.choice(pairs)
    chosen_action = random.choice(actions)

    creds = get_credentials()
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet("Users")
    users = sheet.get_all_records()

    for user in users:
        chat_id = user.get("Telegram-ID")
        if chat_id:
            try:
                send_signal(chosen_action, chosen_pair, chat_id)
            except Exception as e:
                print(f"Misslyckades att skicka signal till {chat_id}: {e}")
                
# === Automatiskt notifiera resultat ===
def check_signals_result():
    try:
        creds = get_credentials()
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).worksheet("Signals")
        rows = sheet.get_all_records()

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

            # Hämta klockslag från timestamp
            entry_time = ""
            try:
                entry_time = row.get("Timestamp", "").split(" ")[1]
            except:
                entry_time = "okänt"

            # === Meddelande till den som bekräftade ===
            if accepted == "yes":
                if profit > 0:
                    msg = f"✅ {signal_text} kl {entry_time} = +{profit} USD 🎉💰"
                elif profit < 0:
                    msg = f"✅ {signal_text} kl {entry_time} = {profit} USD 😵💔"
                else:
                    msg = f"✅ {signal_text} kl {entry_time} = ±0 USD 😐"
                bot.send_message(chat_id=telegram_id, text=msg)

            # === Meddelande till den som missade signalen ===
            else:
                result = "WIN🏆" if profit > 0 else "LOST💀"
                msg = f"❌ Missad signal: {signal_text} kl {entry_time} = {result}"
                bot.send_message(chat_id=telegram_id, text=msg)

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
    
# === Valutapar info-knapp ===
@bot.callback_query_handler(func=lambda call: call.data == "valutapar_info")
def show_valutapar_info(call):
    valutapar_info_text = """
<b>Info om valutaparen</b>
(Sorterade från låg till hög risk)

1. <b>USDCHF</b> – 💚 Väldigt stabilt, låg volatilitet. Går ofta motsatt EURUSD.  
2. <b>EURCHF</b> – 💚 Två säkra valutor. Rör sig långsamt – används ofta i försiktiga strategier.  
3. <b>EURUSD</b> – 💚 Mest handlade paret. Stabilt, låg spread. Bra för nybörjare.  
4. <b>USDJPY</b> – 💛 Ofta stabilt, men kan reagera starkt på nyheter från centralbanker.  
5. <b>EURJPY</b> – 💛 Lite mer rörelse än EURUSD. Bra balans mellan stabilitet och potential.  
6. <b>GBPUSD</b> – 💛 Mer volatil än EURUSD. Kräver lite mer koll, men ger också större möjligheter.  
7. <b>XAUUSD (Guld)</b> – ❤️‍🔥 Volatilt och känsligt för geopolitik. För dig som gillar tempo.  
8. <b>GBPJPY</b> – ❤️‍🔥 Kallas <i>"The Beast"</i>. Väldigt volatilt. Hög risk men hög potential.
"""
    bot.send_message(call.message.chat.id, valutapar_info_text, parse_mode="HTML")

if __name__ == '__main__':
    app.run()
    
def reminder_loop():
    while True:
        now = datetime.utcnow()

        for signal in pending_signals:
            if signal['confirmed']:
                continue

            time_diff = (signal['entry_time'] - now).total_seconds() / 60

            # 10 min kvar
            if 9 < time_diff <= 10 and not signal.get('reminder_10'):
                bot.send_message(
                    signal['user_id'],
                    "🔔 Psst… Din signal väntar fortfarande på dig! Du har 10 minuter kvar innan signalen går live. Missa den inte!😱"
                )
                signal['reminder_10'] = True

            # 5 min kvar
            elif 4 < time_diff <= 5 and not signal.get('reminder_5'):
                bot.send_message(
                    signal['user_id'],
                    "🔔🔔 Tick-tock babes!! 5 minuter kvar innan din trade går live. Go get that bag💸"
                )
                signal['reminder_5'] = True

            # 1 min kvar
            elif 0 < time_diff <= 1 and not signal.get('reminder_1'):
                bot.send_message(
                    signal['user_id'],
                    "❗️SISTA CHANSEN❗️Nu har du bara 1 minut på dig att acceptera signalen. Don’t miss out..🔥"
                )
                signal['reminder_1'] = True

        time.sleep(30)

# Starta påminnelsetråd
reminder_thread = threading.Thread(target=reminder_loop)
reminder_thread.daemon = True
reminder_thread.start()

def start_signal_loop():
    def loop():
        while True:
            auto_generate_signal()
            time.sleep(3600)  # 60 minuter

    thread = threading.Thread(target=loop)
    thread.daemon = True
    thread.start()

# Starta signalgeneratorn
start_signal_loop()

# === Starta på Render ===
if __name__ == "__main__":
    print("Bouijee Bot är igång...")

    # Ta bort eventuell gammal webhook och sätt ny
    bot.remove_webhook()
    bot.set_webhook(url="https://bot-0xdn.onrender.com/")  # 🔁 Ändra till din faktiska Render-URL om den byts

    # Starta Flask med rätt port och IP för Render
    port = int(os.environ.get("PORT", 5000))  # Render sätter PORT som env-variabel
    app.run(host="0.0.0.0", port=port)