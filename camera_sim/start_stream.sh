#!/bin/bash

# start_stream.sh
# Starts the mediamtx RTSP server and streams a sample video to it in a loop.

# Set strict error handling
set -e

# Define directories
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
SAMPLE_DIR="$PROJECT_ROOT/camera_sim/sample_videos"

if [ -f "$PROJECT_ROOT/mediamtx.exe" ]; then
    MEDIAMTX_BIN="$PROJECT_ROOT/mediamtx.exe"
elif [ -f "$PROJECT_ROOT/mediamtx" ]; then
    MEDIAMTX_BIN="$PROJECT_ROOT/mediamtx"
else
    echo "Error: mediamtx binary not found in project root"
    exit 1
fi

# 1. Start mediamtx in the background
echo "Starting mediamtx server..."

# Run mediamtx in the background and redirect output to a log file
"$MEDIAMTX_BIN" > "$PROJECT_ROOT/mediamtx.log" 2>&1 &
MEDIAMTX_PID=$!
echo "mediamtx running with PID $MEDIAMTX_PID"

# Give the server a second to start up
sleep 1

# 2. Start streaming both videos
echo "Starting streams to cctv1 and office..."

# Note: h264 decode warnings from OpenCV/ffplay at each loop restart are expected and harmless — caused by -stream_loop -1 restarting short demo clips. Not present with continuous real camera input.
ffmpeg -re -stream_loop -1 -i "$SAMPLE_DIR/CCTV1.mp4" -c:v libx264 -preset ultrafast -tune zerolatency -g 30 -f rtsp -rtsp_transport tcp rtsp://localhost:8554/cctv1 > /dev/null 2>&1 &
FFMPEG1_PID=$!

ffmpeg -re -stream_loop -1 -i "$SAMPLE_DIR/OFFICE.mp4" -c:v libx264 -preset ultrafast -tune zerolatency -g 30 -f rtsp -rtsp_transport tcp rtsp://localhost:8554/office > /dev/null 2>&1 &
FFMPEG2_PID=$!

echo "CCTV1 streaming at rtsp://localhost:8554/cctv1 (PID: $FFMPEG1_PID)"
echo "OFFICE streaming at rtsp://localhost:8554/office (PID: $FFMPEG2_PID)"

# Cleanup when script is stopped
cleanup() {
    echo "Stopping streams and mediamtx..."
    kill $FFMPEG1_PID $FFMPEG2_PID $MEDIAMTX_PID 2>/dev/null || true
}

trap cleanup SIGINT SIGTERM EXIT

# Keep script running
wait

