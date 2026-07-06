# AgentGrid

**Multi-Agent Video Intelligence Platform** — A scaled-down but architecturally faithful replica of enterprise video-AI systems. Built solo, on free-tier infrastructure, in 7 days.

AgentGrid simulates the edge/cloud split used by real-world video-AI platforms: video processing runs on your local machine ("edge"), while only structured JSON events are sent to a public cloud dashboard. Full video stays local; the dashboard shows text-only alerts — mirroring real cost and privacy constraints.

---

## Architecture

```
LOCAL MACHINE ("edge")
  Camera/Video File ──► MediaMTX (RTSP) ──► FrameBus ──► AI Detection Agents
                                                          ├── Intrusion Agent (YOLOv8s)
                                                          └── Productivity Agent (YOLOv8s-pose)
                                                          │
                                    Local Viewer :5000 ◄──┘
                                    Publisher ──► HTTPS POST (JSON events)

CLOUD (all free tiers)
  FastAPI Orchestrator (Hugging Face Spaces)
    ├── Supabase PostgreSQL (event_log, agent_configs)
    ├── Upstash Redis (pub/sub live feed)
    └── Ollama LLM (reasoning layer — runs locally)
  Next.js Dashboard (Vercel) ◄── WebSocket / REST
```

---

## Features

### Implemented (Day 1)
- **Camera Simulation** — Loops MP4 files as real RTSP streams via MediaMTX + ffmpeg
- **YOLOv8s Object Detection** — Real-time person detection on live RTSP streams with OpenCV display

### Planned (Days 2–7)
- **Intrusion Detection Agent** — Zone-based person detection with configurable hours, siren alarm, red banner overlay
- **Productivity Tracker Agent** — Pose-based skeleton tracking; classifies workers as active / idle / away
- **FrameBus** — Asyncio-based frame broadcaster for multi-agent support
- **Local Viewer** — Full video with overlays at `localhost:5000`
- **Cloud API** — FastAPI orchestrator with REST endpoints for events, agents, cameras
- **Supabase Database** — `event_log`, `agent_configs`, `cameras` tables
- **Redis Pub/Sub** — Real-time event broadcasting via Upstash
- **WebSocket Live Feed** — `/ws/live` endpoint for dashboard updates
- **Ollama Reasoning Layer** — "Ask Your Cameras": natural-language Q&A over event data
- **Next.js Dashboard** — Agent toggles, live event feed, camera onboarding form, Q&A interface
- **Public Deployment** — API on Hugging Face Spaces, dashboard on Vercel

---

## Tech Stack

| Category | Tool | License |
|---|---|---|
| Detection | YOLOv8s (Ultralytics) | AGPL-3.0 |
| Pose Estimation | YOLOv8s-pose (Ultralytics) | AGPL-3.0 |
| RTSP Server | MediaMTX | MIT |
| Stream Looping | ffmpeg | LGPL/GPL |
| Computer Vision | opencv-python | Apache 2.0 |
| Backend | FastAPI + Uvicorn | MIT |
| Database | PostgreSQL (Supabase) | Free tier |
| Pub/Sub | Redis (Upstash) | Free tier |
| LLM | Ollama + llama3.2:1b | Free / open-source |
| Frontend | Next.js 14 + React + Tailwind CSS | MIT |
| Deployment | Hugging Face Spaces + Vercel | Free tier |

---

## Getting Started

### Prerequisites
- Python 3.11
- ffmpeg
- VLC (for stream verification)

### Setup

```bash
# 1. Activate the virtual environment
source env/bin/activate

# 2. Install dependencies
pip install -r local/requirements.txt
```

### Run the Demo

```bash
# 1. Start the camera simulation (MediaMTX + ffmpeg loop)
bash camera_sim/start_stream.sh

# 2. Verify the stream (optional)
#    Open rtsp://localhost:8554/cam1 in VLC

# 3. Run object detection
python local/day1_test.py
```

Press `q` in the OpenCV window to quit.

---

## Project Status

This is a work-in-progress portfolio project built over 7 days. Currently at **Day 1** of 7:
- [x] Camera simulation (MediaMTX + ffmpeg)
- [x] Baseline YOLOv8s detection
- [ ] Intrusion agent
- [ ] Productivity agent
- [ ] Local viewer
- [ ] Cloud API
- [ ] Database & event pipeline
- [ ] Reasoning layer (Ollama)
- [ ] Dashboard
- [ ] Deployment

---

## License

The AgentGrid project code is available for use under the MIT License. Note that the `LICENSE` file in this repository currently covers the [MediaMTX](https://github.com/bluenviron/mediamtx) binary (MIT, copyright aler9). Third-party components (YOLOv8s, MediaMTX, ffmpeg, etc.) are governed by their respective licenses.
