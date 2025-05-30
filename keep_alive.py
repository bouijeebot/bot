from flask import Flask, request
import telebot

app = Flask(__name__)
bot = os.getenv(7692679752:AAH8QUrMAjnUBrnoy4pe0mMuTcosCRxfV2Q)  # valfritt om du behöver

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return "Webhook received!", 200
    return "Bouijee Bot är vaken!", 200

def keep_alive():
    app.run(host="0.0.0.0", port=8080)
