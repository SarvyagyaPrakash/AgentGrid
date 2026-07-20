from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models import Event, AgentConfig, CameraInput, AskRequest
from psycopg2.extras import RealDictCursor
import db
from redis_bus import publish_to_dashboard, subscribe_dashboard
import logging
from ask_agent import ask_agent_query

app = FastAPI(title="AgentGrid Cloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3333",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3333",
    ],
    allow_origin_regex="https://.*\\.vercel\\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        db.put_connection(conn)
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database healthcheck failed: {str(e)}")

@app.post("/api/events")
async def create_event(event: Event):
    try:
        event_dict = event.model_dump()
        db.save_event(event_dict)
        await publish_to_dashboard(event_dict)
        return {"status": "success", "message": "Event logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/events")
async def get_events(limit: int = 50):
    try:
        events = db.get_recent_events(limit)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        async for event in subscribe_dashboard():
            await websocket.send_json(event)
    except WebSocketDisconnect:
        logging.info("WebSocket client disconnected")
    except Exception as e:
        logging.error(f"WebSocket connection error: {e}")

@app.get("/api/agents")
async def get_agents():
    try:
        configs = db.get_agent_configs()
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/agents/{camera_id}/{agent_name}/toggle")
async def toggle_agent(camera_id: str, agent_name: str, enabled: bool = Body(..., embed=True)):
    try:
        db.set_agent_config(camera_id, agent_name, enabled)
        return {"status": "success", "message": f"Agent {agent_name} set to {enabled} for camera {camera_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/cameras")
async def get_cameras():
    try:
        cameras = db.get_cameras()
        return cameras
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/cameras")
async def add_camera(camera: CameraInput):
    # If camera_id is not specified, generate one from the name
    camera_id = camera.camera_id or camera.name.lower().replace(" ", "_")
    try:
        db.insert_camera(camera_id, camera.name, camera.rtsp_url)
        return {"status": "success", "camera_id": camera_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/ask")
async def ask_cameras(request: AskRequest):
    try:
        res = ask_agent_query(request.question)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in reasoning layer: {str(e)}")

@app.post("/api/benchmarks")
async def post_benchmark(payload: dict = Body(...)):
    try:
        db.save_benchmark_results(payload)
        return {"status": "success", "message": "Benchmark results saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/benchmarks")
async def get_benchmark():
    try:
        results = db.get_latest_benchmark_results()
        if results is None:
            # Fallback to empty/default structure if none exists yet so it doesn't hard-crash the dashboard
            return {}
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
