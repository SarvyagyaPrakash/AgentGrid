from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from models import Event, AgentConfig, CameraInput
import db

app = FastAPI(title="AgentGrid Cloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/events")
async def create_event(event: Event):
    try:
        db.save_event(event.model_dump())
        return {"status": "success", "message": "Event logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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

@app.post("/api/cameras")
async def add_camera(camera: CameraInput):
    # If camera_id is not specified, generate one from the name
    camera_id = camera.camera_id or camera.name.lower().replace(" ", "_")
    try:
        db.insert_camera(camera_id, camera.name, camera.rtsp_url)
        return {"status": "success", "camera_id": camera_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
