"""
fatigue_detector.py
-------------------
Uses OpenCV Haar cascades to detect face + eyes in real time.
If eyes are absent for FATIGUE_THRESHOLD consecutive frames → FATIGUE.
generate_frames() yields MJPEG bytes for Flask's /video_feed route.
"""

import cv2
import time
import numpy as np
import threading


class FatigueDetector:

    FATIGUE_THRESHOLD = 20   # consecutive no-eye frames before alert

    def __init__(self):
        # Load cascades from OpenCV's built-in data directory
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade  = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')

        self.cap              = None
        self.status           = 'INITIALIZING'
        self._no_eye_frames   = 0
        self._frame_lock      = threading.Lock()
        self._latest_frame    = None   # encoded JPEG bytes

        self._camera_ok       = False
        self._init_camera()

    # ── Camera init ───────────────────────────────────────────────────
    def _init_camera(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW faster on Windows
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap        = cap
            self._camera_ok = True
            self.status     = 'ACTIVE'
            print("[Camera] ✅ Webcam opened successfully.")
        else:
            self.status     = 'NO CAMERA'
            print("[Camera] ⚠️  Could not open webcam — video feed will show placeholder.")

    # ── Core detection (called inside generate_frames loop) ───────────
    def _process_frame(self, frame):
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        eyes_detected = False

        for (fx, fy, fw, fh) in faces:
            # Draw face rectangle
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 200, 100), 2)

            roi_gray  = gray[fy:fy + fh, fx:fx + fw]
            roi_color = frame[fy:fy + fh, fx:fx + fw]

            eyes = self.eye_cascade.detectMultiScale(
                roi_gray, scaleFactor=1.1, minNeighbors=10)

            if len(eyes) > 0:
                eyes_detected = True
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey),
                                  (ex + ew, ey + eh), (0, 100, 255), 2)

        # Update consecutive no-eye counter
        if eyes_detected:
            self._no_eye_frames = 0
            self.status = 'ACTIVE'
        else:
            self._no_eye_frames += 1
            if self._no_eye_frames >= self.FATIGUE_THRESHOLD:
                self.status = 'FATIGUE'

        # ── Overlay ──────────────────────────────────────────────────
        if self.status == 'FATIGUE':
            overlay_color = (0, 0, 220)
            label         = '⚠ FATIGUE DETECTED'
        else:
            overlay_color = (0, 200, 80)
            label         = '✓  ACTIVE'

        # Semi-transparent top bar
        bar = frame.copy()
        cv2.rectangle(bar, (0, 0), (frame.shape[1], 50), (20, 20, 20), -1)
        cv2.addWeighted(bar, 0.6, frame, 0.4, 0, frame)

        cv2.putText(frame, label,
                    (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.9, overlay_color, 2, cv2.LINE_AA)

        counter_text = f'Frames: {self._no_eye_frames}/{self.FATIGUE_THRESHOLD}'
        cv2.putText(frame, counter_text,
                    (frame.shape[1] - 220, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1, cv2.LINE_AA)

        return frame

    # ── Placeholder when camera unavailable ───────────────────────────
    def _placeholder_frame(self):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (20, 20, 30)
        cv2.putText(img, 'CAMERA UNAVAILABLE',
                    (120, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (60, 60, 80), 2)
        cv2.putText(img, 'Check webcam connection',
                    (155, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (60, 60, 80), 1)
        return img

    # ── MJPEG generator (Flask uses this) ────────────────────────────
    def generate_frames(self):
        """Yields MJPEG-encoded frames continuously."""
        while True:
            if not self._camera_ok or self.cap is None:
                frame = self._placeholder_frame()
                self.status = 'NO CAMERA'
            else:
                ret, frame = self.cap.read()
                if not ret:
                    frame = self._placeholder_frame()
                    self.status = 'NO CAMERA'
                else:
                    frame = self._process_frame(frame)

            # Encode to JPEG
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok:
                time.sleep(0.05)
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes()
                   + b'\r\n')

            time.sleep(0.04)   # ~25 fps
