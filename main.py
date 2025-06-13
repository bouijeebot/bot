import os
from dotenv import load_dotenv
from flask import Flask, request
import telebot

# === Ladda miljövariabler ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === Koppla alla knappar och kommandon ===
from bouijee_handlers import register_all_handlers
register_all_handlers(bot)

# === Telegram webhook route ===
@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# === Render health check ===
@app.route("/", methods=["GET"])
def home():
    return "Bouijee webhook är igång 💅", 200

# === Lokal körning (valfritt) ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

