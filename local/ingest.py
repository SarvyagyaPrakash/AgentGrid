import cv2
import sys
import asyncio
import threading
from frame_bus import FrameBus
from agents import IntrusionAgent

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
    rtsp_url = "rtsp://localhost:8554/cam1"
    camera_id = "cam1"
    
    print(f"Connecting to RTSP stream at {rtsp_url}...")
    cap = VideoCaptureThread(rtsp_url)
    
    if not cap.isOpened():
        print(f"Error: Could not open video stream at {rtsp_url}")
        sys.exit(1)

    print("Stream connected. Initializing FrameBus and Agents...")
    
    bus = FrameBus()
    
    # Instantiate the Intrusion Agent and subscribe it to the bus
    intrusion_agent = IntrusionAgent(camera_id=camera_id)
    bus.subscribe(intrusion_agent)

    print("System running. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from stream. Exiting...")
            break

        # Broadcast the frame to all agents
        await bus.broadcast(frame)

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
