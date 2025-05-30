from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    return "Bouijee Bot is alive", 200

def keep_alive():
    app.run(host="0.0.0.0", port=8080)
