from flask import Flask
import os
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bouijee Bot is live 💅"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()
