import time
import threading
from signal_engine import generate_signals_and_dispatch
from bouijee_core import check_signals_result, reminder_loop

def start_ai_signal_loop():
    while True:
        try:
            print("🔮 SugarMama kör AI-signal-loop...")
            generate_signals_and_dispatch()
        except Exception as e:
            print(f"⚠️ Fel i AI-signal-loop: {e}")
        time.sleep(1800)  # Vänta 30 minuter innan nästa signal

if __name__ == "__main__":
    print("🚀 Bouijee Worker startar...")

    # Starta resultat-uppföljning i egen tråd
    result_thread = threading.Thread(target=check_signals_result)
    result_thread.daemon = True
    result_thread.start()

    # Starta påminnelse-loop i egen tråd
    reminder_thread = threading.Thread(target=reminder_loop)
    reminder_thread.daemon = True
    reminder_thread.start()

    # Kör AI-signal-loop (i main-tråden)
    start_ai_signal_loop()
