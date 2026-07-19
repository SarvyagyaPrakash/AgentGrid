import json
import httpx

API_URL = "http://localhost:8333/api/events"

def publish_event(event_data: dict):
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

    # Send event to cloud API
    try:
        response = httpx.post(API_URL, json=event_data, timeout=5.0)
        if response.status_code == 200:
            print("[Publisher] Event successfully posted to Cloud API.")
        else:
            print(f"[Publisher] Error: Cloud API returned status code {response.status_code}. Response: {response.text}")
    except Exception as e:
        print(f"[Publisher] Error: Failed to connect to Cloud API at {API_URL}. Details: {e}")

