from flask import Flask, request
import telebot
import os

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

@app.route("/", methods=["GET"])
def home():
    return "Bouijee Bot is running!"

@app.route("/", methods=["POST"])
def receive_update():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

def keep_alive():
    app.run(host="0.0.0.0", port=8080)
