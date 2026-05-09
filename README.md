# 🛡️ Smart Wearable Monitoring Dashboard

Real-time industrial dashboard for biometric + environmental monitoring.

## 📁 Project Structure

```
smart_wearable/
├── app.py                  ← Flask server (run this)
├── sensor_reader.py        ← Arduino COM5 serial reader
├── fatigue_detector.py     ← OpenCV Haar cascade eye/fatigue detection
├── logger.py               ← CSV data logger (every 5 seconds)
├── requirements.txt        ← Python dependencies
├── templates/
│   └── dashboard.html      ← Full dashboard frontend (HTML/CSS/JS)
└── logs/
    └── readings.csv        ← Auto-created log file
```

---

## ⚙️ Setup & Run

### 1. Install dependencies
```bashpython app.py
pip install -r requirements.txt
```

### 2. Connect your Arduino (optional)
- Plug Arduino into **COM5**
- Ensure your Arduino sketch sends: `TEMP:36.5` over Serial at 9600 baud
- If Arduino is not plugged in → app runs in **simulation mode automatically**

### 3. Run the app
```bash
python app.py
```

### 4. Open browser
```
http://localhost:5000
```

---

## 🔌 Arduino Serial Format

Your Arduino sketch should Serial.print in this format:
```
TEMP:36.5
```
Example Arduino code:
```cpp
#include <DHT.h>
DHT dht(2, DHT11);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float t = dht.readTemperature();
  if (!isnan(t)) {
    Serial.print("TEMP:");
    Serial.println(t);
  }
  delay(2000);
}
```

---

## 🚨 Alert Thresholds

| Sensor      | Warning         | Danger          |
|-------------|-----------------|-----------------|
| Temperature | ≥ 36.5°C        | ≥ 38.0°C        |
| Gas (MQ2)   | ≥ 350 ppm       | ≥ 500 ppm       |
| Fatigue     | —               | 20 frames no-eye|

---

## 🔄 Simulation Mode

When Arduino is **not connected**, the dashboard automatically:
- Simulates realistic drifting temperature (30–42°C)
- Simulates humidity (30–95%)
- Simulates gas readings (100–700 ppm)
- Shows **⚡ SIM MODE** badge in the header
- Camera/fatigue detection still works with webcam

---

## 🚀 Future Improvements

### ☁️ IoT Cloud Integration
- **AWS IoT Core**: Send MQTT messages from Flask → CloudWatch dashboards
- **ThingSpeak**: Free IoT cloud, direct Arduino HTTP POST support
- **Firebase Realtime DB**: WebSocket sync, works great with web dashboards
- **Grafana + InfluxDB**: Professional time-series database + visualization

### 📱 Mobile App
- **Flutter**: Cross-platform (iOS + Android), call `/api/data` via HTTP
- **React Native**: JavaScript-based, reuse existing fetch logic
- **Blynk**: No-code IoT mobile dashboard, direct Arduino library support
- **Progressive Web App (PWA)**: Add manifest + service worker to this HTML
  and it installs like a native app on Android!

### 🔧 Wearable Hardware Miniaturization
- **ESP32 (replaces Arduino)**: Built-in WiFi/BT, sends data wirelessly
- **Raspberry Pi Zero 2W**: Runs Flask locally on the wearable device itself
- **Arduino Nano 33 BLE Sense**: Has temp, humidity, accel, BLE built-in
- **Custom PCB**: Design in KiCad, order from JLCPCB for <$10
- **Battery**: 18650 Li-ion cell + TP4056 charging module
- **Enclosure**: 3D print in PLA, or laser-cut acrylic

### 📊 Better Fatigue Detection
- **dlib 68-point landmarks**: Eye Aspect Ratio (EAR) method — much more accurate
- **MediaPipe Face Mesh**: Google's real-time 468-point face mesh, free
- **PERCLOS metric**: Industry standard for fatigue (% eye closure over time)
- **Head pose estimation**: Detect nodding/drooping head as fatigue signal

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| Arduino not detected | Check Device Manager, try COM3/COM4, reinstall CH340 drivers |
| Webcam not opening | Check if another app is using camera, try index 1 in `VideoCapture(1)` |
| ImportError: cv2 | Run `pip install opencv-python` |
| Port already in use | Change port in `app.py`: `app.run(port=5001)` |
| SIM badge always showing | Arduino connected but sending wrong format — check baud rate (9600) |
