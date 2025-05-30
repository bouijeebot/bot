from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "I'm alive", 200

@app.route("/", methods=["POST"])
def webhook():
    return "Webhook received", 200

def keep_alive():
    app.run(host="0.0.0.0", port=8080)
