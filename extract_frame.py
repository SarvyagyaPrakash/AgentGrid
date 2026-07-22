import cv2

def main():
    video_path = "camera_sim/sample_videos/CCTV1.mp4"
    cap = cv2.VideoCapture(video_path)
    
    # Skip the first 60 frames to bypass any initial black screens or fade-ins
    for _ in range(60):
        cap.read()
        
    ok, frame = cap.read()
    if ok:
        cv2.imwrite("test_frame.png", frame)
        print("Frame saved as test_frame.png, size:", frame.shape)  # (height, width, channels)
    else:
        print("Failed to read the video file. Ensure the path is correct.")
    cap.release()

if __name__ == "__main__":
    main()
