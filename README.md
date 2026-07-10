# AgentGrid

<p align="center">
  <img src="https://img.shields.io/badge/Video%20AI-Platform-blue?style=for-the-badge" alt="Video AI Platform" />
  <img src="https://img.shields.io/badge/Multi--Agent-System-green?style=for-the-badge" alt="Multi-Agent System" />
  <img src="https://img.shields.io/badge/Edge%20%2F%20Cloud-Split-orange?style=for-the-badge" alt="Edge Cloud Split" />
  <img src="https://img.shields.io/badge/YOLOv8s-Detection-red?style=for-the-badge" alt="YOLOv8s" />
</p>

<p align="center">
  <b>A multi-agent video intelligence platform that mirrors how real-world video-AI systems split work between the edge and the cloud.</b>
</p>

---

## What It Does

AgentGrid processes video on your local machine ("the edge") and ships only structured JSON events to a cloud API — full video never leaves your machine. This mirrors the real cost and privacy constraints of production video-AI deployments.

The pipeline is driven by independent AI agents that watch the same video feed and each do one job well: detect intrusions, or track how active a person is.

## Architecture

```
LOCAL MACHINE ("edge")
  Camera / Video File
        │
        ▼
   MediaMTX (RTSP)  ──►  FrameBus
                              │
            ┌─────────────────┼─────────────────┐
            ▼                                   ▼
   Intrusion Agent                     Productivity Agent
   (YOLOv8s)                           (YOLOv8s-pose)
            │                                   │
            └──────────────┬────────────────────┘
                           ▼
                 cv2.imshow (local overlay)
                           │
                           ▼
                 Publisher  ──►  HTTPS POST (JSON events)

CLOUD (optional)
   FastAPI API
        │
        ▼
   Supabase PostgreSQL
   (event_log · agent_configs · cameras)
```

## How It Works

### 1. Camera Simulation
Loops MP4 files as live RTSP streams using MediaMTX + ffmpeg. Two sample feeds are served:
- `rtsp://localhost:8554/cctv1` — a counter / entrance view
- `rtsp://localhost:8554/office` — a desk view

### 2. FrameBus
An asyncio-based frame broadcaster. The RTSP stream is decoded once, then every frame is broadcast to all subscribed agents so multiple agents run concurrently against the same video.

### 3. AI Agents

| Agent | Model | What it does |
|-------|-------|--------------|
| **Intrusion Detection** | YOLOv8s (`yolov8s.pt`) | Detects people inside a configurable polygon zone during active hours. On trigger it plays a siren and draws a red alarm banner, then emits a structured JSON event. |
| **Productivity Tracker** | YOLOv8s-pose (`yolov8s-pose.pt`) | Tracks pose keypoints over a 30-second rolling window and classifies each person as **active**, **idle**, or **away** based on motion. Emits one event per window. |

### 4. Local Viewer
An OpenCV window renders bounding boxes, zone outlines, pose skeletons, and alarm overlays in real time. Press `q` to quit.

### 5. Cloud API
A FastAPI service receives the JSON events and stores them in Supabase PostgreSQL.

**Endpoints**
| Method | Route | Purpose |
|--------|-------|---------|
| `POST` | `/api/events` | Log a detection event |
| `GET`  | `/api/agents` | List agent configurations |
| `POST` | `/api/agents/{camera_id}/{agent_name}/toggle` | Enable / disable an agent |
| `POST` | `/api/cameras` | Register a new camera |

### 6. Supabase Database
Structured persistence with three tables:
- `event_log` — every detection / productivity event
- `agent_configs` — per-camera agent settings
- `cameras` — registered camera metadata

### 7. Zone Calibration Tools
- `extract_frame.py` — pull a single frame from a video for reference
- `pick_zone_points.py` — click to define the polygon intrusion zone

## Tech Stack

<table>
  <tr><th>Category</th><th>Tool</th></tr>
  <tr><td>Object Detection</td><td>YOLOv8s (Ultralytics)</td></tr>
  <tr><td>Pose Estimation</td><td>YOLOv8s-pose (Ultralytics)</td></tr>
  <tr><td>RTSP Server</td><td>MediaMTX</td></tr>
  <tr><td>Stream Looping</td><td>ffmpeg</td></tr>
  <tr><td>Computer Vision</td><td>OpenCV</td></tr>
  <tr><td>Concurrency</td><td>asyncio</td></tr>
  <tr><td>Backend API</td><td>FastAPI + Uvicorn</td></tr>
  <tr><td>Database</td><td>PostgreSQL (Supabase)</td></tr>
  <tr><td>Alarm Audio</td><td>simpleaudio</td></tr>
</table>

## Getting Started

### Prerequisites
- Python 3.11
- ffmpeg
- VLC (optional, for stream verification)

### Local Setup
```bash
source env/bin/activate
pip install -r local/requirements.txt
```

### Run the Demo
```bash
# 1. Start camera simulation (MediaMTX + ffmpeg loop)
bash camera_sim/start_stream.sh

# 2. Verify the stream (optional) — open the URL in VLC
#    rtsp://localhost:8554/cctv1
#    rtsp://localhost:8554/office

# 3. Run the agents
python local/ingest.py
```
Press `q` in the OpenCV window to quit.

### Run the Cloud API (Optional)
```bash
pip install -r cloud_api/requirements.txt
# Set DATABASE_URL in .env
uvicorn cloud_api.main:app --reload --port 8333
```

## Notes

- The Productivity Agent measures **presence and motion** within a zone over time. It does not measure work quality, output, or effort.
- Only royalty-free stock footage (Pexels, Pixabay) or self-recorded footage is used.

## License

AgentGrid code is available under the MIT License. Third-party components (YOLOv8s, MediaMTX, ffmpeg, etc.) are governed by their respective licenses.
