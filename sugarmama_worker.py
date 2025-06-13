import time
import threading
from sugarmama_worker import (
    start_ai_signal_loop,
    check_signals_result,
    reminder_loop
)

if __name__ == "__main__":
    print("🚀 Bouijee Worker startar...")

    # Starta AI-signal-loop
    start_ai_signal_loop()

    # Starta resultat-uppföljning
    check_signals_result()

    # Starta påminnelse-loop
    reminder_thread = threading.Thread(target=reminder_loop)
    reminder_thread.daemon = True
    reminder_thread.start()

    # Håll processen vid liv
    while True:
        time.sleep(60)
