import cv2
import numpy as np
from datetime import datetime
import simpleaudio as sa
import asyncio
from ultralytics import YOLO

from .base_agent import BaseAgent

# --- CONFIGURABLE CONSTANTS ---
# Replace these with your actual restricted zone polygon coordinates
RESTRICTED_ZONE_POLYGON = np.array([
    [671, 328], 
    [978, 1065], 
    [7, 943]
], np.int32)

ZONE_NAME = "restricted_area_1"

# Active hours window (24-hour format)
ACTIVE_HOURS_START = 0  # 00:00 (Placeholder, change to actual start hour)
ACTIVE_HOURS_END = 24   # 24:00 (Placeholder, change to actual end hour)

class IntrusionAgent(BaseAgent):
    def __init__(self, camera_id: str):
        super().__init__(camera_id)
        self.agent_name = "intrusion_detection"
        print(f"[{self.agent_name}] Loading YOLOv8s model...")
        self.model = YOLO("yolov8s.pt")
        
        # Load the siren sound object
        try:
            self.siren_wave = sa.WaveObject.from_wave_file("local/sounds/siren.wav")
            print(f"[{self.agent_name}] Siren sound loaded.")
        except Exception as e:
            print(f"[{self.agent_name}] Warning: Could not load siren.wav. Error: {e}")
            self.siren_wave = None

        self.last_alarm_time = 0.0

    def is_within_active_hours(self):
        current_hour = datetime.now().hour
        if ACTIVE_HOURS_START <= ACTIVE_HOURS_END:
            return ACTIVE_HOURS_START <= current_hour < ACTIVE_HOURS_END
        else:
            return current_hour >= ACTIVE_HOURS_START or current_hour < ACTIVE_HOURS_END

    async def on_frame(self, frame):
        if not self.is_within_active_hours():
            cv2.putText(frame, f"[{self.agent_name}] OUTSIDE ACTIVE HOURS", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
            # Draw the restricted zone on the frame (orange)
            cv2.polylines(frame, [RESTRICTED_ZONE_POLYGON], isClosed=True, color=(0, 165, 255), thickness=2)
            cv2.putText(frame, ZONE_NAME, (RESTRICTED_ZONE_POLYGON[0][0], RESTRICTED_ZONE_POLYGON[0][1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            return
            
        results = self.model.predict(source=frame, classes=[0], conf=0.5, verbose=False)
        boxes = results[0].boxes
        
        intrusion_detected = False
        highest_conf = 0.0
        intruder_box = None

        # First pass to check if ANY intrusion occurred
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            conf = float(box.conf[0])
            inside = cv2.pointPolygonTest(RESTRICTED_ZONE_POLYGON, (center_x, center_y), measureDist=False)
            
            if inside >= 0:
                intrusion_detected = True
                if conf > highest_conf:
                    highest_conf = conf
                    intruder_box = [x1, y1, x2, y2]

        # Draw the restricted zone (red if intrusion, orange if not)
        zone_color = (0, 0, 255) if intrusion_detected else (0, 165, 255)
        cv2.polylines(frame, [RESTRICTED_ZONE_POLYGON], isClosed=True, color=zone_color, thickness=2)
        cv2.putText(frame, ZONE_NAME, (RESTRICTED_ZONE_POLYGON[0][0], RESTRICTED_ZONE_POLYGON[0][1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, zone_color, 2)

        # Second pass to draw person boxes, P1 labels, and confidences
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            inside = cv2.pointPolygonTest(RESTRICTED_ZONE_POLYGON, (center_x, center_y), measureDist=False)
            
            if inside >= 0:
                # Draw red box for intruder
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
            else:
                # Draw green box for non-intruder
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)

            # Draw label P1, P2, etc and Confidence
            label = f"P{i+1} ({conf:.2f})"
            # Blue color is (255, 0, 0) in BGR
            cv2.putText(frame, label, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        if intrusion_detected:
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_alarm_time > 3.0:
                self.last_alarm_time = current_time
                
                self.emit_event(
                    agent_name=self.agent_name,
                    event_type="intrusion",
                    confidence=round(highest_conf, 2),
                    metadata={
                        "box": intruder_box,
                        "zone": ZONE_NAME
                    }
                )
                
                if self.siren_wave:
                    self.siren_wave.play()
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], 60), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_text = f"ALARM TRIGGERED | Zone: {ZONE_NAME} | {timestamp_str}"
            cv2.putText(frame, alert_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
