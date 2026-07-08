import cv2
import sys
import asyncio
import threading
from frame_bus import FrameBus
from agents import IntrusionAgent, ProductivityAgent

class VideoCaptureThread:
    """
    Runs cv2.VideoCapture in a dedicated background thread.
    This constantly consumes the RTSP stream, preventing the buffer from 
    overflowing and corrupting frames (macroblock glitches) when YOLO inference is slow.
    """
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.ret, self.frame = ret, frame

    def read(self):
        if self.ret and self.frame is not None:
            return self.ret, self.frame.copy()
        return False, None

    def release(self):
        self.running = False
        self.thread.join()
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()

async def main():
    # Prompt the user for video stream choice
    print("Which video do you want to open?")
    print("1. CCTV1 Counter (cctv1)")
    print("2. Office Desk (office)")
    video_choice = input("Enter choice (1/2): ").strip()

    # Prompt the user for agent selection
    print("\nWhich agents do you want to run for this video?")
    print("1. Restriction (Intrusion Detection)")
    print("2. Productivity (Pose-based Tracking)")
    print("3. Both")
    choice = input("Enter choice (1/2/3): ").strip()
    
    import numpy as np
    if video_choice == '2':
        # Office Desk (OFFICE.mp4)
        rtsp_url = "rtsp://localhost:8554/office"
        camera_id = "office_cam"
        custom_zone = np.array([
            [3, 577], 
            [731, 638], 
            [618, 1056], 
            [5, 1072]
        ], np.int32)
    else:
        # CCTV1 Counter (CCTV1.mp4)
        rtsp_url = "rtsp://localhost:8554/cctv1"
        camera_id = "cctv1_cam"
        custom_zone = np.array([
            [671, 328], 
            [978, 1065], 
            [7, 943]
        ], np.int32)
    
    print(f"Connecting to RTSP stream at {rtsp_url}...")
    cap = VideoCaptureThread(rtsp_url)
    
    if not cap.isOpened():
        print(f"Error: Could not open video stream at {rtsp_url}")
        sys.exit(1)

    print("Stream connected. Initializing FrameBus and Agents...")
    
    bus = FrameBus()
    
    # Initialize shared model for unified tracking IDs
    from ultralytics import YOLO
    print("Loading shared YOLOv8s-pose model for tracking...")
    shared_model = YOLO("yolov8s-pose.pt")
    
    # Instantiate chosen agents and subscribe them to the bus
    if choice in ['1', '3']:
        intrusion_agent = IntrusionAgent(camera_id=camera_id, zone_polygon=custom_zone)
        bus.subscribe(intrusion_agent)
    
    if choice in ['2', '3']:
        productivity_agent = ProductivityAgent(camera_id=camera_id)
        if choice == '3':
            productivity_agent.hide_labels = True
        bus.subscribe(productivity_agent)

    print("System running. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from stream. Exiting...")
            break

        # Run tracking ONCE per frame to share IDs and detections
        results = shared_model.track(source=frame, persist=True, classes=[0], conf=0.5, verbose=False)

        # Broadcast the frame and tracking results to all agents
        await bus.broadcast(frame, results)

        # Display the annotated frame
        cv2.imshow("AgentGrid Local Viewer", frame)

        # Check for user input to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("User pressed 'q', exiting...")
            break
            
        # Small sleep to yield to event loop
        await asyncio.sleep(0.001)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())
