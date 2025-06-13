# Alla Telegrambotens faktiska funktioner samlade här

# Här måste du inkludera dessa imports igen eftersom detta är en fristående fil
import os
import json
import time
import threading
import gspread
import telebot
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone
from google.oauth2.service_account import Credentials
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === Globala variabler ===
pending_signals = []
awaiting_balance_input = {}

# === Miljövariabler ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDENTIALS_FILE = "credentials.json"

bot = telebot.TeleBot(TOKEN)

def home():
    return "Bouijee Bot är igång!", 200

def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

def run_signal_engine():
    from signal_engine import generate_signals_and_dispatch  
    return generate_signals_and_dispatch()

def register_user_if_not_exists(telegram_id):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    all_data = sheet.get_all_records()

    for row in all_data:
        if str(row.get("Telegram-ID")) == str(telegram_id):
            return  # Redan registrerad

    # Lägg till ny användare med alla standardvärden
    today = datetime.now().strftime("%Y-%m-%d")  # Registrerad
    sheet.append_row([telegram_id, "", "1%", today, 0, 0, "Standard"])

# === Credential-setup ===
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

    expected_header = [
        "Timestamp", "Telegram-ID", "MT4-ID", "Signal",
        "Result", "Profit", "Action", "Accepted", "Executed"
    ]
    actual_header = worksheet.row_values(1)
    if actual_header != expected_header:
        raise ValueError(
            f"Felaktiga kolumnrubriker i bladet '{sheet_name}'.\n"
            f"Förväntat: {expected_header}\n"
            f"Hittat:    {actual_header}"
        )

    worksheet.append_row(values)

# === Alla funktioner nedan: ===

def get_mt4_id_by_telegram(telegram_id):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    for row in sheet.get_all_records():
        if str(row.get("Telegram-ID")) == str(telegram_id):
            return row.get("MT4-ID", "Ej angivet")
    return "Ej angivet"

def log_trade_signal(telegram_id, user_name, symbol, action):
    mt4_id = get_mt4_id_by_telegram(telegram_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    values = [
        timestamp,
        telegram_id,   # 👈 Viktigt: loggar Telegram-ID här
        mt4_id,
        symbol,
        "",      # Result
        "",      # Profit
        action,
        "Yes",   # Accepted
        ""       # Executed
    ]
    log_signal_to_sheet("Signals", values)

def get_user_balance(telegram_id):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    for row in sheet.get_all_records():
        if str(row.get("Telegram-ID")) == str(telegram_id):
            for key in row:
                if key.strip().lower() in ["balance", "saldo"]:
                    value = row[key]
                    return value if value else "Ej angivet"
    return "Ej hittad"

def get_user_risk(telegram_id):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    for row in sheet.get_all_records():
        if str(row.get("Telegram-ID")) == str(telegram_id):
            risk = row.get("Risknivå", "").strip()
            return risk if risk else "1%"
    return "1%"

def update_user_risk(telegram_id, risk_level):
    creds = get_credentials()
    sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
    all_values = sheet.get_all_values()
    for i, row in enumerate(all_values):
        if str(row[0]) == str(telegram_id):  # Telegram-ID finns i kolumn A (index 0)
            sheet.update_cell(i + 1, 7, f"{risk_level}%")  # Kolumn G = Risknivå (index 7)
            return

def save_mt4_id(message):
    telegram_id = str(message.from_user.id)
    mt4_id = message.text.strip()

    try:
        creds = get_credentials()
        sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
        all_values = sheet.get_all_values()

        row_index = None
        for i, row in enumerate(all_values):
            if row[0] == telegram_id:
                row_index = i + 1  # eftersom get_all_values() börjar på rad 1
                sheet.update_cell(row_index, 3, mt4_id)  # Kolumn C = MT4-ID
                break

        bot.send_message(message.chat.id, f"MT4-ID *{mt4_id}* är nu kopplat – nice babes! ✨", parse_mode="Markdown")

        # Kolla om användaren har angett startsaldo
        balance_cell = f"B{row_index}"  # Kolumn B = Balance
        current_balance = sheet.acell(balance_cell).value
        if not current_balance:
            awaiting_balance_input[telegram_id] = balance_cell
            bot.send_message(
                message.chat.id,
                "Nu när du är kopplad – hur mycket kapital vill du starta med? 💰 Skriv bara summan (t.ex. 2000)"
            )
            return  # Vänta på att användaren anger saldo innan meny visas

        show_menu(message)

    except Exception as e:
        bot.send_message(message.chat.id, "Något gick snett när vi skulle spara ditt MT4-ID 😢 Testa igen om en stund.")

# Exempel: för /start-kommandot
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📲 App Store", url="https://apps.apple.com/app/metatrader-4/id496212596"),
        InlineKeyboardButton("📲 Google Play", url="https://play.google.com/store/apps/details?id=net.metaquotes.metatrader4")
    )
    markup.add(InlineKeyboardButton("✨NU KÖR VI✨", callback_data="demo_signal"))

    bot.send_message(
        message.chat.id,
        "Heeey din katt! 😻✨\n\n"
        "Jag är *Bouijee Bot* – din fab trading-bestie som sniffar pengar snabbare än du hittar dina klackar en lördagkväll. 👠💸\n\n"
        "När jag säger *BUY💚* eller *SELL💔*, så bör signalen accepteras inom rätt tid för bästa resultat. 📉📈\n\n"
        "Så häll upp ett glas bubbel 🥂, luta dig tillbaka, och låt mig servera dig signaler med mer precision än din eyeliner.\n\n"
        "💼 Du kommer att behöva *MetaTrader 4* – finns att ladda ner här 👇\n\n"
        "*Let’s get rich – men make it fabulous.*\n\n"
        "Xoxo NU KÖR VI! 💃🏽\n\n"
        "👉 Du kan skriva /meny när som helst för att återgå till menyn.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ... Fyll på med:
# - show_menu(message)
def show_menu(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Mitt konto 💼", callback_data="mitt_konto"),
        InlineKeyboardButton("ℹ️ Info", callback_data="info"),
        InlineKeyboardButton("📊 Valutapar info", callback_data="valutapar_info"),
    )
    markup.add(
        InlineKeyboardButton("⚖️ Risknivå", callback_data="risknivå"),
        InlineKeyboardButton("💃🏽 Aktivera signaler", callback_data="standby")
    )
    markup.add(
        InlineKeyboardButton("🔁 Byt MT4-ID", callback_data="koppla_mt4")
    )
    
    bot.send_message(
        message.chat.id,
        "✨ *Bouijee Bot Meny* ✨\n\n"
        "Vad vill du göra nu, babes? 🤷🏽‍♀️\n\n"
        "💼 *Psst!* Du kan när som helst uppdatera ditt MT4-ID om du byter konto – klicka bara på *🔁 Byt MT4-ID*. Bouijee fixar. 💅",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def send_standby_button(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💃🏽 Aktivera signaler", callback_data="standby"))
    bot.send_message(chat_id, "Klicka för att börja ta emot signaler, darling!✨", reply_markup=markup)
  
# - show_info(call)
def show_info(call):
    info_text = (
        "*ℹ️ Hur funkar Bouijee Bot?*\n\n"
        "Bouijee Bot skickar fab trading-signaler direkt till dig. Du väljer om du vill godkänna varje trade. 👍🏼\n\n"
        "Vi använder en liten del av ditt konto per trade – vilket skyddar dig från drama på marknaden.\n\n"
        "Bouijee kan inte heller påverka ditt saldo, det är bara du som har åtkomst till ditt konto, just sayin. 💅🏼\n\n"
        "✨ *Rekommenderad första insättning*: $1000 USD\n\n"
        "Men du kan börja med vad du vill – och fylla på när du vill, för att ta ditt konto från *cute* till *cash queen*. 👑\n\n"
        "⚖️ *Risk per signal*:\n"
        "Du väljer mellan 1%, 2% eller 3% av ditt saldo.\n"
        "Om du inte väljer något själv, så sätter Bouijee det automatiskt till *1%* – classy & safe. 💼\n\n"
        "Professionella traders håller sig ofta till:\n"
        "• 1% – (Låg risk) Safe & classy 💁🏽‍♀️\n"
        "• 2% – (Medel risk) Lite spice men fortfarande safe 🌶️\n"
        "• 3% – (Hög risk) Bold babe-mode: mer vinst, mer risk! 🫣\n\n"
        "*Självklart får du välja själv, men Bouijee rekommenderar 1–2% för att hålla det classy och hållbart. Du kan alltid ändra ditt val i menyn.*"
    )

    bot.send_message(
        call.message.chat.id,
        info_text,
        parse_mode="Markdown"
    )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💃🏽 Aktivera signaler", callback_data="standby"))
    bot.send_message(
        call.message.chat.id,
        "När du är redo att glänsa, klicka här så väntar vi in nästa signal tillsammans!🫶🏼",
        reply_markup=markup
    )

def prompt_mt4_id(call):
    try:
        msg = bot.send_message(
            call.message.chat.id,
            "*Skriv in ditt MT4-ID här, babe 💼*\n\n"
            "🔎 Öppna MT4-appen, klicka på ’Inställningar’ ⚙️ och sedan ’Konto’.\n"
            "Kopiera numret som står högst upp – det är ditt ID 💋",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, save_mt4_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, "Oops! Något gick fel när jag försökte be om ditt MT4-ID 😿")

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
    markup.add(InlineKeyboardButton("💃🏽 Aktivera signaler", callback_data="standby"))
    bot.send_message(
        call.message.chat.id,
        "Redo för att få signaler direkt i din feed? Klicka här, babes!✅",
        reply_markup=markup
    )
  
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
  
def show_main_menu(call):
    show_menu(call.message)

def handle_standby(call):
    bot.send_message(call.message.chat.id, "Snyggt! Då pingar jag dig så snart nästa signal kommer, babes! 🥂")

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

def handle_callback(call):
    telegram_id = call.from_user.id
    user = call.from_user.first_name or "Okänd"
    data = call.data

    try:
        if data == "mitt_konto":
            handle_mitt_konto(call)

        elif data == "koppla_mt4":
            prompt_mt4_id(call)

        elif data == "risknivå":
            choose_risk_level(call)

        elif data.startswith("risk_"):
            handle_risk_selection(call)

        elif data == "info":
            show_info(call)

        elif data == "valutapar_info":
            show_valutapar_info(call)

        elif data == "standby":
            handle_standby(call)

        elif data == "demo_signal":
            show_main_menu(call)

        elif data == "accept":
            for s in pending_signals:
                if s['user_id'] == telegram_id and not s['confirmed']:
                    s['confirmed'] = True
                    symbol = s.get("symbol", "EURUSD")
                    action = s.get("action", "BUY")
                    bot.send_message(call.message.chat.id, "Yaaas Let’s go!🥂")
                    log_trade_signal(telegram_id, user, symbol, action)
                    break

        elif data == "decline":
            bot.send_message(call.message.chat.id, "Got it babes🤫 vi tar nästa istället!")

        else:
            # Okänd knapp – visa meny
            show_menu(call.message)

    except Exception as e:
        bot.send_message(call.message.chat.id, "Oops! Något gick fel med knappen 😿 Testa igen eller skriv /meny")
      
def handle_balance_input(message):
    telegram_id = str(message.from_user.id)
    text = message.text.strip()

    try:
        balance = float(text.replace(",", ".").replace(" ", ""))
        balance_cell = awaiting_balance_input.pop(telegram_id)
        creds = get_credentials()
        sheet = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet("Users")
        sheet.update_acell(balance_cell, str(balance))
        bot.send_message(message.chat.id, f"Toppen, vi har sparat ditt startsaldo som {balance} kr. Let’s slay these markets babe 💸")
        show_menu(message)

    except ValueError:
        bot.send_message(message.chat.id, "Oops! Det där såg inte ut som en siffra. Försök igen 💵")
      
def handle_unexpected_messages(message):
    bot.send_message(
        message.chat.id,
        "Babe, tryck på en knapp istället – jag jobbar inte med DMs! ✨",
        parse_mode="Markdown"
    )
  
def send_signal(action, symbol="EURUSD", chat_id=None):
    # Använd svensk lokal tid
    se_tz = timezone("Europe/Stockholm")
    entry_time = datetime.now(se_tz) + timedelta(minutes=20)
    entry_str = entry_time.strftime("%H:%M")

    # Lägg till signalen med korrekt entry_time för interna påminnelser (i UTC)
    pending_signals.append({
        'user_id': chat_id,
        'entry_time': entry_time.astimezone(timezone("UTC")),  # för jämförelse i reminder-loop
        'symbol': symbol,
        'action': action,
        'confirmed': False,
        'reminder_10': False,
        'reminder_5': False,
        'reminder_1': False
    })

    # Behåll nuvarande meddelandestil
    message_text = (
        f"🔥 *MONEY RAIN* 🔥\n\n"
        f"{'💚' if action.upper() == 'BUY' else '💔'} *{action.upper()} {symbol}*\n"
        f"⏰ Entry: *{entry_str}*\n\n"
        "Take it or leave it 💅🏼"
    )

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅✅✅", callback_data="accept"),
        InlineKeyboardButton("❌❌❌", callback_data="decline")
    )

    bot.send_message(chat_id=chat_id, text=message_text, reply_markup=markup, parse_mode="Markdown")

def check_signals_result():
    try:
        creds = get_credentials()
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).worksheet("Signals")
        rows = sheet.get_all_records()

        notified_col_index = 10  # Kolumn J = Notified
        notified_cells = sheet.range(f"J2:J{len(rows)+1}")  # Rad 2 till slutet

        for idx, row in enumerate(reversed(rows)):
            row_index = len(rows) - idx - 1  # För att matcha originalindex

            telegram_id = row.get("Telegram-ID")
            profit = row.get("Profit")
            accepted = row.get("Accepted", "").strip().lower()
            signal_text = row.get("Signal", "").strip()
            already_notified = row.get("Notified", "").strip().lower()

            if already_notified == "yes":
                continue  # Hoppa över redan notifierade

            if not telegram_id or profit == "":
                continue

            try:
                profit = float(profit)
                telegram_id = int(telegram_id)
            except:
                continue

            try:
                entry_time = row.get("Timestamp", "").split(" ")[1]
            except:
                entry_time = "okänt"

            # === Skicka meddelande beroende på accepted/result ===
            if accepted == "yes":
                if profit > 0:
                    msg = f"💸 {signal_text} kl {entry_time} = +{profit} USD 🎉 Money wagon incoming!"
                elif profit < 0:
                    msg = f"💔 {signal_text} kl {entry_time} = {profit} USD 😵 Jikes... Nästa tar vi!"
                else:
                    msg = f"😐 {signal_text} kl {entry_time} = ±0 USD – Phew, det var nära ögat!"
                bot.send_message(chat_id=telegram_id, text=msg)
            else:
                result = "🏆 WIN" if profit > 0 else "💀 LOSS"
                msg = f"❌ Du missade {signal_text} kl {entry_time} = {result}. Vi tar nästa babes 💅"
                bot.send_message(chat_id=telegram_id, text=msg)

            # ✅ Markera raden som notifierad
            notified_cells[row_index].value = "Yes"

        # Uppdatera hela kolumnen på en gång (effektivare)
        sheet.update_cells(notified_cells)

        # 🧮 Uppdatera saldon
        try:
            update_all_user_balances()
        except Exception as e:
            print("⚠️ Kunde inte uppdatera saldon:", e)

    except Exception as e:
        print("Fel i check_signals_result:", e)

    # 🔁 Kör igen om 5 minuter
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

        total_profit = 0
        for row in signal_data:
            if (
                str(row.get("Telegram-ID")) == telegram_id and
                str(row.get("Accepted", "")).strip().lower() == "yes"
            ):
                try:
                    total_profit += float(row.get("Profit", 0))
                except:
                    continue

        nytt_saldo = round(saldo + total_profit, 2)

        headers = user_sheet.row_values(1)
        saldo_col = None
        for idx, header in enumerate(headers):
            if header.strip().lower() in ["balance", "saldo"]:
                saldo_col = idx + 1
                break

        if saldo_col:
            user_sheet.update_cell(i + 2, saldo_col, nytt_saldo)

    print("✅ Alla användarsaldon har uppdaterats!")

def reminder_loop():
    while True:
        now = datetime.now(timezone.utc)

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
