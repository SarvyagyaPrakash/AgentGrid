import json
import httpx

API_URL = "http://localhost:8333/api/events"

def publish_event(event_data: dict):
    # Print the JSON event to the console.
    print("\n--- NEW EVENT PUBLISHED ---")
    print(json.dumps(event_data, indent=2))
    print("---------------------------\n")
    
    # Send event to cloud API
    try:
        response = httpx.post(API_URL, json=event_data, timeout=5.0)
        if response.status_code == 200:
            print("[Publisher] Event successfully posted to Cloud API.")
        else:
            print(f"[Publisher] Error: Cloud API returned status code {response.status_code}. Response: {response.text}")
    except Exception as e:
        print(f"[Publisher] Error: Failed to connect to Cloud API at {API_URL}. Details: {e}")

