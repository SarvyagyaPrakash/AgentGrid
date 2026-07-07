import json

def publish_event(event_data: dict):
    # For Day 2, we just print the JSON event to the console.
    print("\n--- NEW EVENT PUBLISHED ---")
    print(json.dumps(event_data, indent=2))
    print("---------------------------\n")
