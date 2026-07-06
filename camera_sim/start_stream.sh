#!/bin/bash

# start_stream.sh
# Starts the mediamtx RTSP server and streams a sample video to it in a loop.

# Set strict error handling
set -e

# Define directories
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
MEDIAMTX_BIN="$PROJECT_ROOT/mediamtx"
SAMPLE_DIR="$PROJECT_ROOT/camera_sim/sample_videos"

# 1. Start mediamtx in the background
echo "Starting mediamtx server..."
if [ ! -f "$MEDIAMTX_BIN" ]; then
    echo "Error: mediamtx binary not found at $MEDIAMTX_BIN"
    exit 1
fi

# Run mediamtx in the background and redirect output to a log file
"$MEDIAMTX_BIN" > "$PROJECT_ROOT/mediamtx.log" 2>&1 &
MEDIAMTX_PID=$!
echo "mediamtx running with PID $MEDIAMTX_PID"

# Give the server a second to start up
sleep 1

# 2. Find the video file
# If an argument is provided, use that. Otherwise, look for the first file in sample_videos/
if [ -n "$1" ]; then
    VIDEO_PATH="$1"
    if [ ! -f "$VIDEO_PATH" ]; then
        echo "Error: File $VIDEO_PATH not found."
        kill $MEDIAMTX_PID
        exit 1
    fi
else
    VIDEO_FILE=$(ls "$SAMPLE_DIR" | grep -v '^\.' | head -n 1 || true)
    if [ -z "$VIDEO_FILE" ]; then
        echo "Error: No video file found in $SAMPLE_DIR"
        kill $MEDIAMTX_PID
        exit 1
    fi
    VIDEO_PATH="$SAMPLE_DIR/$VIDEO_FILE"
fi

echo "Found video file: $VIDEO_PATH"
echo "Starting stream to rtsp://localhost:8554/cam1..."

# 3. Use ffmpeg to stream the video
# EXPLANATION OF FFMPEG FLAGS:
# -re : Read input at native frame rate (essential for simulating a live stream).
# -stream_loop -1 : Loop the input video infinitely.
# -i "$VIDEO_PATH" : Specify the input video file.
# -c:v libx264 : Re-encode video to H.264 (helps fix OpenCV decoding errors on some MP4s).
# -preset ultrafast -tune zerolatency : Optimize for live streaming.
# -g 30 : Force a keyframe every 30 frames (fixes "Missing reference picture" in OpenCV).
# -f rtsp : Specify the output format as RTSP.

ffmpeg -re -stream_loop -1 -i "$VIDEO_PATH" -c:v libx264 -preset ultrafast -tune zerolatency -g 30 -f rtsp rtsp://localhost:8554/cam1


# Cleanup when ffmpeg is stopped (e.g. by Ctrl+C)
echo "Stopping mediamtx server..."
kill $MEDIAMTX_PID
