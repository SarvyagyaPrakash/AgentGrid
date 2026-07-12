# AgentGrid

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/AgentGrid-Multi--Agent%20Video%20Intelligence-7c3aed?style=for-the-badge&logo=python&logoColor=white">
    <img src="https://img.shields.io/badge/AgentGrid-Multi--Agent%20Video%20Intelligence-7c3aed?style=for-the-badge&logo=python&logoColor=white" alt="AgentGrid">
  </picture>
</p>

<p align="center">
  <b>Edge-native video intelligence.</b> Two AI agents watch the same feed. Raw video stays local — only structured JSON meets the cloud.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/YOLOv8s-Detection-2563eb?style=flat-square&logo=openai&logoColor=white" alt="YOLOv8s">
  <img src="https://img.shields.io/badge/YOLOv8s--pose-Pose%20Estimation-16a34a?style=flat-square&logo=openai&logoColor=white" alt="YOLOv8s-pose">
  <img src="https://img.shields.io/badge/MediaMTX-RTSP-dc2626?style=flat-square" alt="MediaMTX">
  <img src="https://img.shields.io/badge/FastAPI-Cloud%20API-059669?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-Dashboard-000000?style=flat-square&logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-3b82f6?style=flat-square&logo=supabase&logoColor=white" alt="Supabase">
  <img src="https://img.shields.io/badge/Redis-Upstash-dc2626?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Ollama-LLM-7c3aed?style=flat-square&logo=ollama&logoColor=white" alt="Ollama">
</p>

---

## Why AgentGrid

Most video-AI demos stream the entire feed to the cloud — expensive, slow, and privacy-hostile.

AgentGrid flips the model. Everything happens on-device using local YOLOv8 models. The cloud receives only lightweight JSON event payloads (~0.4 Kbps per camera), not raw video (~2000 Kbps). This is how real production systems work.

Two independent AI agents watch the same video simultaneously, each focused on a single job:

| Agent | Model | Purpose |
|-------|-------|---------|
| **Intrusion Detection** | `yolov8s.pt` | Flags people entering a configurable polygon zone during active hours. Plays a siren, draws a red alarm banner, emits a structured event. |
| **Productivity Tracker** | `yolov8s-pose.pt` | Tracks skeletal keypoints over a 30-second rolling window and classifies each person as **active**, **idle**, or **away** based on motion displacement. |

---

## How It Connects

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL EDGE                                      │
│                                                                              │
│  Camera or MP4 ──► MediaMTX ──► FrameBus (async broadcaster)                 │
│  (RTSP stream)                  ┌──────────┴──────────┐                      │
│                                 ▼                      ▼                     │
│                     Intrusion Agent           Productivity Agent             │
│                     (YOLOv8s)                 (YOLOv8s-pose)                 │
│                                 │                      │                     │
│                                 └──────────┬───────────┘                     │
│                                            ▼                                 │
│                                  OpenCV Window (overlays, alarms)            │
│                                            │                                 │
│                                            ▼                                 │
│                                      Publisher: HTTPS POST                   │
│                                     (JSON events only, no video)             │
└────────────────────────────────────┬─────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                                CLOUD                                         │
│                                                                              │
│  FastAPI ──── Supabase (event_log, agent_configs, cameras)                   │
│     │                                                                        │
│     ├── Redis pub/sub ──── WebSocket ──── Dashboard (live feed)              │
│     │                                                                        │
│     └── Ask Agent: Ollama LLM (deepseek-r1:1.5b)                             │
│         Filters database by keyword/date, then answers from real events only │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Anatomy

### `camera_sim/` — Camera Simulation

Loops MP4 files as live RTSP streams using MediaMTX + ffmpeg. Two pre-configured feeds:

| Feed | URL | Content |
|------|-----|---------|
| CCTV1 | `rtsp://localhost:8554/cctv1` | Counter / entrance view |
| OFFICE | `rtsp://localhost:8554/office` | Desk view |

No real cameras needed — the entire pipeline works against simulated streams. Point `ingest.py` at a real RTSP camera URL and it works identically, zero code changes.

### `local/` — Edge Processing

| File | Role |
|------|------|
| `ingest.py` | Entry point — selects video source and launches agents |
| `frame_bus.py` | Async pub/sub broadcaster — decodes stream once, serves all agents |
| `publisher.py` | HTTP client — ships JSON events to the cloud API |
| `agents/base_agent.py` | Abstract base — defines `emit_event()` contract |
| `agents/intrusion_agent.py` | Polygon zone + active hours + siren alarm |
| `agents/productivity_agent.py` | Pose keypoint displacement over rolling window |
| `sounds/siren.wav` | Alarm audio played on intrusion trigger |

**FrameBus** is the linchpin. It decodes the RTSP stream once, then broadcasts every frame to all subscribed agents asynchronously. This means you can add more agents without touching the decoding pipeline — each agent gets every frame independently.

Both agents share a single YOLOv8s-pose inference per frame for person tracking, so `track_id` values are consistent across agents.

### `cloud_api/` — Backend API

FastAPI service with 9 REST endpoints + WebSocket pub/sub:

| Method | Route | Purpose |
|--------|-------|---------|
| `POST` | `/api/events` | Log a detection or productivity event |
| `GET` | `/api/events` | Query events (filterable by camera, agent, date, keyword) |
| `GET` | `/api/events/recent` | Latest events for live dashboard |
| `GET` | `/api/agents` | List all agent configurations |
| `POST` | `/api/agents/{camera_id}/{agent_name}/toggle` | Enable / disable an agent |
| `POST` | `/api/cameras` | Register a new camera |
| `GET` | `/api/cameras` | List registered cameras |
| `POST` | `/api/ask` | Natural-language query against the event database |
| `WS` | `/ws/events` | WebSocket — live event stream via Redis pub/sub |

**Event flow:** Publisher -> FastAPI -> Supabase (persist) + Redis (broadcast) -> WebSocket -> Dashboard.

**Ask Agent** — a grounded 2-step reasoning pipeline:
1. Parse the natural-language question, extract keywords and date ranges, query the database
2. Pass the real matching events to a local Ollama `deepseek-r1:1.5b` model for summarization

The LLM never invents data — it only sees what the database actually returned.

### `dashboard/` — Web Dashboard (Next.js)

A public-facing control panel deployable on Vercel:

| Component | What it does |
|-----------|-------------|
| **Agent Toggle** | Table of cameras with on/off switches per agent |
| **Live Event Feed** | Real-time event stream over WebSocket |
| **Add Camera Form** | Register new RTSP camera sources |
| **Ask Cameras Box** | Typed natural-language queries against the event log |

Built with React 18, Tailwind CSS 3, and Geist fonts.

### Utility Tools

| Tool | Purpose |
|------|---------|
| `extract_frame.py` | Pull a single frame from any video for zone calibration reference |
| `pick_zone_points.py` | Click-to-define polygon coordinates for intrusion zones |

---

## Quick Start

```bash
# Prerequisites
# Python 3.11, ffmpeg

# 1. Install local dependencies
pip install -r local/requirements.txt

# 2. Start camera simulation
bash camera_sim/start_stream.sh
# Feeds: rtsp://localhost:8554/cctv1, rtsp://localhost:8554/office

# 3. Run the agents
python local/ingest.py
# Press 'q' in the OpenCV window to quit
```

### Cloud API (Optional)

```bash
pip install -r cloud_api/requirements.txt
# Set DATABASE_URL and REDIS_URL in .env
uvicorn cloud_api.main:app --reload --port 8333
```

### Dashboard (Optional)

```bash
cd dashboard
npm install
npm run dev
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Object Detection | Ultralytics **YOLOv8s** |
| Pose Estimation | Ultralytics **YOLOv8s-pose** |
| RTSP Server | **MediaMTX** |
| Stream Looping | **ffmpeg** |
| Computer Vision | **OpenCV** |
| Concurrency | Python **asyncio** |
| Audio Alarm | **simpleaudio** |
| Cloud API | **FastAPI** + **Uvicorn** |
| Database | **PostgreSQL** (Supabase) |
| Event Bus | **Redis** (Upstash) |
| Reasoning | **Ollama** — `deepseek-r1:1.5b` |
| Dashboard | **Next.js 14** + **React 18** + **Tailwind CSS 3** |
| Deployment | **Docker** + **Docker Compose** |

---

## Project Map

```
AgentGrid/
├── docker-compose.yml           # Orchestrates cloud_api + dashboard
├── .env.example                 # Required environment variables
│
├── camera_sim/                  # Camera simulation layer
│   ├── start_stream.sh          # Launches MediaMTX + 2 ffmpeg loops
│   └── sample_videos/
│       ├── CCTV1.mp4
│       └── OFFICE.mp4
│
├── local/                       # Edge processing layer
│   ├── ingest.py                # Main entry point
│   ├── frame_bus.py             # Async frame broadcaster
│   ├── publisher.py             # Cloud API client
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── intrusion_agent.py
│   │   └── productivity_agent.py
│   └── sounds/
│       └── siren.wav
│
├── cloud_api/                   # Cloud backend
│   ├── main.py                  # FastAPI app (9 endpoints + WebSocket)
│   ├── models.py                # Pydantic schemas
│   ├── db.py                    # PostgreSQL CRUD
│   ├── redis_bus.py             # Redis pub/sub
│   ├── ask_agent.py             # LLM reasoning pipeline
│   └── Dockerfile
│
├── dashboard/                   # Web dashboard
│   ├── app/
│   │   ├── page.tsx             # Main dashboard grid
│   │   └── components/
│   │       ├── AgentToggle.tsx
│   │       ├── LiveEventFeed.tsx
│   │       ├── AddCameraForm.tsx
│   │       └── AskCamerasBox.tsx
│   └── Dockerfile
│
├── extract_frame.py             # Frame extraction tool
└── pick_zone_points.py          # Zone polygon tool
```

---

## Design Decisions

- **Video stays local.** Only structured JSON events (avg. ~0.4 Kbps) leave the edge. No raw video is ever transmitted to any external service.
- **Decode once, consume everywhere.** FrameBus decodes the RTSP stream once and broadcasts frames to all agents concurrently, avoiding redundant decode work.
- **Consistent track IDs.** A single YOLOv8s-pose inference per frame provides unified person tracking across all agents.
- **Grounded LLM reasoning.** The Ask Agent never passes questions directly to the LLM. It first filters the database by keyword/date, then passes only real events to Ollama for summarization. No hallucination, no bluff.
- **Video source agnostic.** Swap a simulated RTSP URL for a real camera URL — the pipeline works without changes.

---

## License

MIT — see [LICENSE](./LICENSE).

Third-party components (Ultralytics YOLOv8, MediaMTX, ffmpeg, OpenCV, Ollama, etc.) are governed by their respective licenses.
