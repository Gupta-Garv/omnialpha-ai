import time
import threading

def run_loop():
    print("Loop started")
    time.sleep(2)
    print("Cycle 1 complete")
    
dash_thread = threading.Thread(target=run_loop, daemon=True)
dash_thread.start()
time.sleep(3)
