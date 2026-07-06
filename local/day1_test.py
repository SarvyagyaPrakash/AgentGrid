import cv2
import sys
from ultralytics import YOLO

def main():
    print("Loading YOLOv8s model (this may download weights on the first run)...")
    # Load the YOLOv8 small model
    model = YOLO("yolov8s.pt")

    rtsp_url = "rtsp://localhost:8554/cam1"
    print(f"Connecting to RTSP stream at {rtsp_url}...")
    
    # Open the video stream
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print(f"Error: Could not open video stream at {rtsp_url}")
        print("\nMost likely causes:")
        print("1. start_stream.sh is not running or mediamtx crashed.")
        print("2. OpenCV was installed without FFmpeg support. Fix by running:")
        print("   pip uninstall opencv-python && pip install opencv-python")
        sys.exit(1)

    print("Stream connected. Press 'q' to quit.")

    while True:
        # Read a frame from the stream
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from stream. Exiting...")
            break

        # Run inference on the frame
        # We only want to detect the 'person' class (class 0 in COCO dataset)
        results = model.predict(source=frame, classes=[0], conf=0.5, verbose=False)

        # Draw custom bounding boxes and labels
        annotated_frame = frame.copy()
        
        # results[0].boxes contains all the detections
        boxes = results[0].boxes
        for i, box in enumerate(boxes):
            # Get bounding box coordinates (x1, y1, x2, y2)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Get confidence score
            conf = float(box.conf[0])
            
            # Determine box color: BGR format (OpenCV uses BGR, not RGB)
            # Red if < 0.6, Green if >= 0.6
            if conf < 0.6:
                color = (0, 0, 255) # Red
            else:
                color = (0, 255, 0) # Green
                
            # Draw the bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label text (P1, P2, P3, etc.)
            label = f"P{i+1}"
            
            # Draw the label text in Blue (255, 0, 0)
            text_color = (255, 0, 0) # Blue
            font = cv2.FONT_HERSHEY_SIMPLEX
            # Draw text with a slight offset above the box
            cv2.putText(annotated_frame, label, (x1, max(y1 - 10, 20)), font, 0.9, text_color, 2)

        # Display the annotated frame
        cv2.imshow("Day 1 Baseline Detection (Person Only)", annotated_frame)

        # Check for user input to exit
        # Wait for 1 ms, and if the user presses 'q', break the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("User pressed 'q', exiting...")
            break

    # Clean up resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
