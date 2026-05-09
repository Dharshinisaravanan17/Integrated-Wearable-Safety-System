"""
logger.py
---------
Background logger — writes one row to CSV every LOG_INTERVAL seconds.
Keeps the last MAX_ROWS rows so the file doesn't grow forever.
"""

import csv
import os
import threading
import time
from datetime import datetime

LOG_FILE    = os.path.join('logs', 'readings.csv')
LOG_INTERVAL = 5          # seconds between writes
MAX_ROWS     = 500        # keep last N rows in memory / file

HEADERS = ['Timestamp', 'Temperature_C', 'Humidity_pct',
           'Gas_ppm', 'Fatigue_Status', 'Simulated']


def _init_file():
    os.makedirs('logs', exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            csv.writer(f).writerow(HEADERS)


def start_logger(get_sensor_data_fn, get_fatigue_fn):
    """
    Call once at startup.
    get_sensor_data_fn() → dict with temperature, humidity, gas, simulated
    get_fatigue_fn()     → str  ('ACTIVE' | 'FATIGUE' | ...)
    """
    _init_file()

    def _loop():
        while True:
            time.sleep(LOG_INTERVAL)
            try:
                data   = get_sensor_data_fn()
                fatigue = get_fatigue_fn()
                row = [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('temperature', ''),
                    data.get('humidity', ''),
                    data.get('gas', ''),
                    fatigue,
                    data.get('simulated', True)
                ]
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow(row)
            except Exception as e:
                print(f"[Logger] Error: {e}")

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def read_last(n=20):
    """Return last n log rows as list of dicts."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, 'r') as f:
            rows = list(csv.DictReader(f))
        return rows[-n:]
    except Exception:
        return []
