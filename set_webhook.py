import os
import telebot

TOKEN = os.getenv("TELEGRAM_TOKEN") or "DIN_TOKEN_HÄR"
bot = telebot.TeleBot(TOKEN)

WEBHOOK_URL = "https://din-app.onrender.com/"  # <-- din Render-URL med /
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)
print("✅ Webhook satt:", WEBHOOK_URL)
