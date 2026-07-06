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

        # Draw the results on the frame
        # The plot() method renders the bounding boxes and labels onto the image
        annotated_frame = results[0].plot()

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
