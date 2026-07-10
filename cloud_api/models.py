from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Event(BaseModel):
    camera_id: str
    agent: str = Field(..., description="Must be 'intrusion_detection' or 'productivity_tracker'")
    event_type: str
    confidence: float
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    camera_id: str
    agent_name: str
    enabled: bool
    updated_at: Optional[str] = None

class CameraInput(BaseModel):
    camera_id: Optional[str] = None
    name: str
    rtsp_url: str

class AskRequest(BaseModel):
    question: str
