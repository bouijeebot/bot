from flask import Flask, request
import threading

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])  # <- Måste ha POST här!
def home():
    if request.method == "POST":
        return "OK", 200
    return "Bouijee Bot is live!", 200

def keep_alive():
    thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080))
    thread.start()
