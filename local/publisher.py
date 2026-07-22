import json
import httpx
import threading
from agents.vlm_captioner import generate_caption

API_URL = "http://localhost:8333/api/events"

def generate_and_update_caption(event_id: int, frame, metadata: dict):
    """Worker function to generate the caption in a background thread and update the cloud API."""
    print(f"[Publisher] Asynchronously generating scene caption for event ID {event_id}...")
    caption = generate_caption(frame)
    print(f"[Publisher] Generated Caption: {caption}")
    metadata["scene_caption"] = caption
    try:
        url = f"http://localhost:8333/api/events/{event_id}/metadata"
        response = httpx.put(url, json=metadata, timeout=10.0)
        if response.status_code == 200:
            print(f"[Publisher] Successfully updated event {event_id} with scene_caption.")
        else:
            print(f"[Publisher] Error: Cloud API returned status code {response.status_code} for metadata update. Response: {response.text}")
    except Exception as e:
        print(f"[Publisher] Error updating event metadata: {e}")

def publish_event(event_data: dict, frame=None):
    # Print the JSON event to the console.
    print("\n--- NEW EVENT PUBLISHED ---")
    print(json.dumps(event_data, indent=2))
    print("---------------------------\n")
    
    # Track byte size for the benchmark
    try:
        import os
        import time
        payload_bytes = len(json.dumps(event_data).encode('utf-8'))
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "event_bytes.log")
        with open(log_path, "a") as f:
            f.write(f"{time.time()},{payload_bytes}\n")
    except Exception:
        pass

    event_id = None
    # Send event to cloud API
    try:
        response = httpx.post(API_URL, json=event_data, timeout=5.0)
        if response.status_code == 200:
            res_json = response.json()
            event_id = res_json.get("id")
            print(f"[Publisher] Event successfully posted to Cloud API (ID: {event_id}).")
        else:
            print(f"[Publisher] Error: Cloud API returned status code {response.status_code}. Response: {response.text}")
    except Exception as e:
        print(f"[Publisher] Error: Failed to connect to Cloud API at {API_URL}. Details: {e}")

    # If a frame was passed and we successfully posted the event, start async captioning
    if frame is not None and event_id is not None:
        metadata = event_data.get("metadata", {}).copy()
        t = threading.Thread(target=generate_and_update_caption, args=(event_id, frame, metadata))
        t.daemon = True
        t.start()

