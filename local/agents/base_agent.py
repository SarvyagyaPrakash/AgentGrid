import abc
from datetime import datetime, timezone
import sys
import os

# Add parent dir to path to import publisher
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from publisher import publish_event

class BaseAgent(abc.ABC):
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.enabled = True

    @abc.abstractmethod
    async def on_frame(self, frame):
        """Process a single frame from the video stream."""
        pass

    def emit_event(self, agent_name: str, event_type: str, confidence: float, metadata: dict):
        """Emit an event matching the schema in Part 5.1 of the spec."""
        if not self.enabled:
            return

        event_data = {
            "camera_id": self.camera_id,
            "agent": agent_name,
            "event_type": event_type,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "metadata": metadata
        }
        publish_event(event_data)
