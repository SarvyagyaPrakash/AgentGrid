"""
This agent measures presence and motion within a zone over time. It does NOT measure work quality, output, or effort.
"""
import cv2
import numpy as np
import asyncio
try:
    import simpleaudio as sa
except ImportError:
    sa = None
from ultralytics import YOLO

from .base_agent import BaseAgent

# Rolling window settings
ROLLING_WINDOW_SECONDS = 30
# Needs empirical tuning based on scale and movement expected
ACTIVE_DISPLACEMENT_THRESHOLD = 500.0

STABLE_ALERT_SECONDS = 300.0

class ProductivityAgent(BaseAgent):
    def __init__(self, camera_id: str):
        super().__init__(camera_id)
        self.agent_name = "productivity_tracker"
        print(f"[{self.agent_name}] Loading YOLOv8s-pose model...")
        self.model = YOLO("yolov8s-pose.pt")
        
        try:
            if sa is not None:
                self.siren_wave = sa.WaveObject.from_wave_file("local/sounds/siren.wav")
            else:
                self.siren_wave = None
        except Exception as e:
            self.siren_wave = None
            
        self.window_start_time = None
        self.id_keypoint_history = {} # track_id -> list of keypoints in current 30s window
        self.id_last_active_time = {} # track_id -> timestamp of last activity
        self.last_alarm_time = 0.0
        self.stable_alert_active = False
        self.hide_labels = False

    async def on_frame(self, frame, results=None):
        current_time = asyncio.get_event_loop().time()
        
        if self.window_start_time is None:
            self.window_start_time = current_time
            self.id_keypoint_history = {}
            self.stable_alert_active = False
            
        if results is None:
            # Use track instead of predict to get unique IDs per person across the entire frame
            results = self.model.track(source=frame, persist=True, classes=[0], conf=0.5, verbose=False)
        
        ids_present = set()

        if len(results) > 0 and results[0].boxes is not None and results[0].boxes.id is not None:
            keypoints = results[0].keypoints.xy.cpu().numpy()
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()

            for i in range(len(boxes)):
                x1, y1, x2, y2 = map(int, boxes[i])
                track_id = track_ids[i]
                ids_present.add(track_id)
                kpts = keypoints[i]
                
                # Track shoulders (5, 6), wrists (9, 10), hips (11, 12)
                target_indices = [5, 6, 9, 10, 11, 12]
                tracked_pts = []
                for idx in target_indices:
                    if idx < len(kpts):
                        pt_x, pt_y = int(kpts[idx][0]), int(kpts[idx][1])
                        if pt_x > 0 and pt_y > 0:  # Valid keypoint
                            tracked_pts.append((pt_x, pt_y))
                            # Draw yellow dots on every tracked keypoint
                            cv2.circle(frame, (pt_x, pt_y), 4, (0, 255, 255), -1)
                
                if track_id not in self.id_keypoint_history:
                    self.id_keypoint_history[track_id] = []
                
                if tracked_pts:
                    self.id_keypoint_history[track_id].append(tracked_pts)
                    
                # Label the person if not hidden
                if not self.hide_labels:
                    label = f"P{track_id}"
                    cv2.putText(frame, label, (x1, max(y1 - 35, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                
                # Ensure they have a last active time initialized
                if track_id not in self.id_last_active_time:
                    self.id_last_active_time[track_id] = current_time
                    
                # Check for 300 seconds stability alert immediately on frame
                if current_time - self.id_last_active_time[track_id] >= STABLE_ALERT_SECONDS:
                    self.stable_alert_active = True
                    if current_time - self.last_alarm_time > 3.0:
                        self.last_alarm_time = current_time
                        if self.siren_wave:
                            self.siren_wave.play()

        # Display alert visual if someone has been stable for > 300s
        if self.stable_alert_active:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], 60), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, f"ALARM: PERSON STABLE > {int(STABLE_ALERT_SECONDS)}s", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Check if rolling window is complete
        if current_time - self.window_start_time >= ROLLING_WINDOW_SECONDS:
            state = "away"
            total_displacement = 0.0
            any_person_active = False

            if ids_present:
                # Calculate displacement per ID
                for track_id, history in self.id_keypoint_history.items():
                    if track_id not in ids_present:
                        continue # Skip if they left before window ended
                        
                    id_disp = 0.0
                    if len(history) > 1:
                        for i in range(1, len(history)):
                            prev_pts = history[i-1]
                            curr_pts = history[i]
                            # match keypoints by index
                            for kp1, kp2 in zip(prev_pts, curr_pts):
                                dist = np.sqrt((kp1[0] - kp2[0])**2 + (kp1[1] - kp2[1])**2)
                                id_disp += dist
                                
                    total_displacement += id_disp
                    
                    if id_disp > ACTIVE_DISPLACEMENT_THRESHOLD:
                        any_person_active = True
                        # Update their last active time because they moved enough
                        self.id_last_active_time[track_id] = current_time

                if any_person_active:
                    state = "active"
                else:
                    state = "idle"

            metadata = {
                "displacement": round(total_displacement, 2),
                "window_seconds": ROLLING_WINDOW_SECONDS
            }
            if len(ids_present) == 1:
                metadata["track_id"] = int(list(ids_present)[0])

            self.emit_event(
                agent_name=self.agent_name,
                event_type=state,
                confidence=1.0,
                metadata=metadata
            )
            
            # Reset window
            self.window_start_time = current_time
            self.id_keypoint_history = {}
            self.stable_alert_active = False # Reset alert visually until triggered again
            
            # Clean up old IDs not seen this window
            active_ids = list(self.id_last_active_time.keys())
            for tid in active_ids:
                if tid not in ids_present:
                    del self.id_last_active_time[tid]

        # Display current status roughly on frame
        elapsed = current_time - self.window_start_time
        current_status = f"Measuring... {int(ROLLING_WINDOW_SECONDS - elapsed)}s left"
        cv2.putText(frame, f"[{self.agent_name}] Status: {current_status}", (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
