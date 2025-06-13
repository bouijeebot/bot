from sugarmama_worker import start_ai_signal_loop, check_signals_result, reminder_loop
import threading
import time

if __name__ == "__main__":
    print("🚀 Startar background worker...")

    # Starta AI-signalmodul
    start_ai_signal_loop()

    # Starta resultatövervakning
    check_signals_result()

    # Starta påminnelse-loop
    reminder_thread = threading.Thread(target=reminder_loop)
    reminder_thread.daemon = True
    reminder_thread.start()

    # Håll igång processen
    while True:
        time.sleep(60)
