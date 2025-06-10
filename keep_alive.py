from flask import Flask, request
import telebot
import os

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

@app.route("/", methods=["GET"])
def home():
    return "Bouijee Bot is live! 💅", 200

@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

def keep_alive():
    app.run(host="0.0.0.0", port=8080)
