# AgentGrid

**Multi-Agent Video Intelligence Platform** — A scaled-down but architecturally faithful replica of enterprise video-AI systems.

AgentGrid simulates the edge/cloud split used by real-world video-AI platforms: video processing runs on your local machine ("edge"), while structured JSON events are sent to a cloud API. Full video stays local; the dashboard shows text-only alerts — mirroring real cost and privacy constraints.

## Architecture

```
LOCAL MACHINE ("edge")
  Camera/Video File → MediaMTX (RTSP) → FrameBus
                                            │
                        ┌────────────────────┼──────────┐
                        │  AI Agents          │          │
                        │  ┌──────────────────┘          │
                        │  ▼                             │
                        │  Intrusion Agent (YOLOv8s)     │
                        │  Productivity Agent (YOLOv8s-pose)│
                        └──────────┬─────────────────────┘
                                   │
                     cv2.imshow (local window)
                                   │
                        Publisher → HTTPS POST (JSON events)

                                   ▼
CLOUD (optional)
  FastAPI API (runs locally or via Hugging Face Spaces)
    └── Supabase PostgreSQL (event_log, agent_configs, cameras)
```

## Implemented

- **Camera Simulation** — loops MP4 files as RTSP streams via MediaMTX + ffmpeg (`camera_sim/start_stream.sh`); streams `CCTV1.mp4` (counter view) and `OFFICE.mp4` (desk view) to `rtsp://localhost:8554/cctv1` and `rtsp://localhost:8554/office`
- **Intrusion Detection Agent** — zone-based person detection using YOLOv8s (`yolov8s.pt`); configurable polygon zone + active hours; plays siren `.wav` and shows red banner on trigger; emits structured JSON events
- **Productivity Tracker Agent** — pose-based skeleton tracking using YOLOv8s-pose (`yolov8s-pose.pt`); classifies persons as **active** / **idle** / **away** based on 30-second rolling keypoint displacement window; emits one event per window
- **FrameBus** — asyncio-based frame broadcaster for multi-agent support; agents subscribe and process frames concurrently
- **Local Viewer** — OpenCV `imshow` window with bounding boxes, zone outlines, pose keypoints, alarm overlays
- **Cloud API** — FastAPI app (`cloud_api/main.py`) with REST endpoints:
  - `POST /api/events` — log detection events
  - `GET /api/agents` — list agent configurations
  - `POST /api/agents/{camera_id}/{agent_name}/toggle` — enable/disable agents
  - `POST /api/cameras` — register new cameras
- **Supabase Database** — PostgreSQL with `event_log`, `agent_configs`, `cameras` tables (connection pooling via `psycopg2`)
- **Zone Calibration Tools** — `extract_frame.py` (extract frame from video) + `pick_zone_points.py` (click-to-define polygon zones)

## Not Yet Implemented

- Redis pub/sub and WebSocket live feed (`/ws/live`)
- "Ask Your Cameras" reasoning layer (Ollama + `/api/ask`)
- Next.js public dashboard
- Docker deployment
- Public hosting (Hugging Face Spaces / Vercel)

## Tech Stack

| Category          | Tool                    |
|-------------------|-------------------------|
| Detection         | YOLOv8s (Ultralytics)   |
| Pose Estimation   | YOLOv8s-pose (Ultralytics) |
| RTSP Server       | MediaMTX                |
| Stream Looping    | ffmpeg                  |
| Computer Vision   | opencv-python           |
| Backend           | FastAPI + Uvicorn       |
| Database          | PostgreSQL (Supabase)   |
| Alarm Sound       | simpleaudio             |

## Getting Started

### Prerequisites
- Python 3.11
- ffmpeg
- VLC (for stream verification)

### Setup

```bash
source env/bin/activate
pip install -r local/requirements.txt
```

### Run the Demo

```bash
# 1. Start camera simulation (MediaMTX + ffmpeg loop)
bash camera_sim/start_stream.sh

# 2. Verify stream (optional)
#    Open rtsp://localhost:8554/cctv1 or rtsp://localhost:8554/office in VLC

# 3. Run agents
python local/ingest.py
```

Press `q` in the OpenCV window to quit.

### Run Cloud API (Optional)

```bash
pip install -r cloud_api/requirements.txt
# Set DATABASE_URL in .env
uvicorn cloud_api.main:app --reload --port 8333
```

## Productivity Tracker Scope

The Productivity Agent measures presence and motion within a zone over time. It does **not** measure work quality, output, or effort.

## Video Sourcing

Only royalty-free stock footage (Pexels, Pixabay) or self-recorded footage is used.

## License

The AgentGrid project code is available under the MIT License. Third-party components (YOLOv8s, MediaMTX, ffmpeg, etc.) are governed by their respective licenses.
