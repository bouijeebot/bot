import os
import telebot

TOKEN = os.getenv("TELEGRAM_TOKEN") or "7692679752:AAH8QUrMAjnUBrnoy4pe0mMuTcosCRxfV2Q"
bot = telebot.TeleBot(TOKEN)

WEBHOOK_URL = "https://bot-ihfu.onrender.com"  # <-- din Render-URL med /
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)
print("✅ Webhook satt:", WEBHOOK_URL)
