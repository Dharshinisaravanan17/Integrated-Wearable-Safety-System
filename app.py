"""
app.py
------
Smart Wearable Monitoring System — Flask Backend
Run:  python app.py
Open: http://localhost:5000
"""

import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, Response

from sensor_reader    import SensorReader
from fatigue_detector import FatigueDetector
import logger as Logger

# ── Flask app ─────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Component init ────────────────────────────────────────────────────
sensor  = SensorReader(port='COM5', baud=9600)
fatigue = FatigueDetector()

# ── Shared state (thread-safe) ────────────────────────────────────────
_sensor_data = {
    'temperature': 36.5,
    'humidity':    60.0,
    'gas':         200,
    'simulated':   True
}
_lock = threading.Lock()


def _get_sensor():
    with _lock:
        return dict(_sensor_data)

def _get_fatigue():
    return fatigue.status


# ── Background sensor thread ─────────────────────────────────────────
def _sensor_loop():
    while True:
        data = sensor.read()
        with _lock:
            _sensor_data.update(data)
        time.sleep(2)

threading.Thread(target=_sensor_loop, daemon=True, name='SensorThread').start()

# ── Start logger ──────────────────────────────────────────────────────
Logger.start_logger(_get_sensor, _get_fatigue)


# ── Alert builder ─────────────────────────────────────────────────────
def _build_alerts(data, fatigue_status):
    alerts = []

    # Temperature
    if data['temperature'] >= 38.0:
        alerts.append({'level': 'danger',
                       'msg': f"High Temperature: {data['temperature']}°C — Check immediately!"})
    elif data['temperature'] >= 36.5:
        alerts.append({'level': 'warning',
                       'msg': f"Elevated Temperature: {data['temperature']}°C"})

    # Fatigue
    if fatigue_status == 'FATIGUE':
        alerts.append({'level': 'danger',
                       'msg': 'Fatigue Detected — Please take a break now!'})

    # Gas
    if data['gas'] >= 500:
        alerts.append({'level': 'danger',
                       'msg': f"Dangerous Gas Level: {data['gas']} ppm — Ventilate area!"})
    elif data['gas'] >= 350:
        alerts.append({'level': 'warning',
                       'msg': f"Elevated Gas Level: {data['gas']} ppm"})

    return alerts


# ══════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/data')
def api_data():
    data           = _get_sensor()
    fatigue_status = _get_fatigue()
    alerts         = _build_alerts(data, fatigue_status)

    return jsonify({
        'temperature':    data['temperature'],
        'humidity':       data['humidity'],
        'gas':            data['gas'],
        'fatigue':        fatigue_status,
        'simulated':      data['simulated'],
        'alerts':         alerts,
        'alert_count':    len(alerts),
        'timestamp':      datetime.now().strftime('%H:%M:%S'),
        'date':           datetime.now().strftime('%d %b %Y')
    })


@app.route('/api/logs')
def api_logs():
    rows = Logger.read_last(20)
    return jsonify(rows)


@app.route('/video_feed')
def video_feed():
    return Response(
        fatigue.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# ── Entry point ───────────────────────────────────────────────────────
if __name__ == '__main__':
    print('\n' + '═' * 55)
    print('  🛡️  Smart Wearable Dashboard')
    print('═' * 55)
    print('  Arduino : COM5  (simulation if not connected)')
    print('  Camera  : webcam index 0')
    print('  URL     : http://localhost:5000')
    print('═' * 55 + '\n')
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
