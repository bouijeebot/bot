from flask import Flask, request
import threading

app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "Bouijee Bot is alive!", 200

@app.route("/", methods=["POST"])
def webhook():
    return "Webhook received!", 200

def keep_alive():
    def run():
        app.run(host="0.0.0.0", port=8080)

    t = threading.Thread(target=run)
    t.start()
