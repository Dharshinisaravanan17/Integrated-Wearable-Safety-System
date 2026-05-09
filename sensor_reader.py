"""
sensor_reader.py
----------------
Reads temperature from Arduino on COM5 (format: TEMP:36.5)
Simulates humidity and gas since only TEMP is sent over serial.
Falls back to full simulation if Arduino is not connected.
"""

import serial
import random
import time
import threading


class SensorReader:
    def __init__(self, port='COM5', baud=9600):
        self.port   = port
        self.baud   = baud
        self.ser    = None
        self.simulated = False
        self._lock  = threading.Lock()

        # Simulation drift values (shared between real + sim modes)
        self._temp     = 36.5
        self._humidity = 60.0
        self._gas      = 200

        self._connect()

    # ── Connection ────────────────────────────────────────────────────
    def _connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=2)
            time.sleep(2)          # wait for Arduino reset
            self.simulated = False
            print(f"[Sensor] ✅ Connected to Arduino on {self.port}")
        except Exception as e:
            print(f"[Sensor] ⚠️  Cannot open {self.port}: {e}")
            print("[Sensor] 🔄 Running in SIMULATION mode — plug in Arduino anytime and restart.")
            self.simulated = True

    # ── Public read ───────────────────────────────────────────────────
    def read(self):
        """Return dict with temperature, humidity, gas, simulated flag."""
        with self._lock:
            if self.simulated:
                return self._simulate_all()
            return self._read_serial()

    # ── Serial read ───────────────────────────────────────────────────
    def _read_serial(self):
        try:
            if self.ser.in_waiting > 0:
                raw = self.ser.readline().decode('utf-8', errors='ignore').strip()
                self._parse_line(raw)
        except Exception as e:
            print(f"[Sensor] Read error: {e} — switching to simulation.")
            self.simulated = True

        # Humidity & gas are always simulated (Arduino only sends TEMP)
        self._humidity += random.uniform(-0.5, 0.5)
        self._humidity  = round(max(30, min(95, self._humidity)), 1)

        self._gas += random.randint(-15, 15)
        self._gas  = max(100, min(700, self._gas))

        return {
            'temperature': round(self._temp, 1),
            'humidity':    self._humidity,
            'gas':         self._gas,
            'simulated':   False       # Arduino IS connected for temp
        }

    def _parse_line(self, line):
        """Parse 'TEMP:36.5' format."""
        if line.upper().startswith('TEMP:'):
            try:
                val = float(line.split(':')[1])
                if 10 < val < 60:    # sanity check
                    self._temp = val
            except (IndexError, ValueError):
                pass                  # ignore malformed lines

    # ── Full simulation ───────────────────────────────────────────────
    def _simulate_all(self):
        """Smoothly drift all values for a realistic demo."""
        self._temp     += random.uniform(-0.3, 0.4)
        self._temp      = round(max(30.0, min(42.0, self._temp)), 1)

        self._humidity += random.uniform(-1.0, 1.0)
        self._humidity  = round(max(30.0, min(95.0, self._humidity)), 1)

        self._gas      += random.randint(-20, 25)
        self._gas       = max(100, min(700, self._gas))

        return {
            'temperature': self._temp,
            'humidity':    self._humidity,
            'gas':         self._gas,
            'simulated':   True
        }
