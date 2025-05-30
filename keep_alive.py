from flask import Flask, request
import threading

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])  # ← Lägg till POST här
def index():
    return "Bouijee Bot is running!", 200

def keep_alive():
    thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080))
    thread.start()
