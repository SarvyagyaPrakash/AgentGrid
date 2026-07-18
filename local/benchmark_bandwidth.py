import os
import sys
import time
import json
import psutil
import cv2
from datetime import datetime

# Configuration
TEST_DURATION = 300  # seconds
RTSP_URL = "rtsp://localhost:8554/cctv1"
HARDWARE_STRING = "MacBook Air M4, 16GB RAM"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "event_bytes.log")
RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.json")

def get_loopback_recv_bytes():
    """
    Finds loopback interface and returns received bytes.
    On macOS, this is typically 'lo0'. Falls back to global stats if not found.
    """
    stats = psutil.net_io_counters(pernic=True)
    for name in ['lo0', 'lo', 'Loopback Pseudo-Interface 1', 'Loopback']:
        if name in stats:
            return stats[name].bytes_recv
    # Fallback
    return psutil.net_io_counters().bytes_recv

def run_raw_video_benchmark():
    print("\n==================================================")
    print("PHASE 1: Measuring Raw Video Bandwidth")
    print(f"Connecting to RTSP Stream: {RTSP_URL}")
    print("==================================================")
    
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print(f"Error: Could not open RTSP stream at {RTSP_URL}")
        print("Please make sure mediamtx and the ffmpeg publisher are running.")
        sys.exit(1)
        
    print("Stream connected. Starting 300-second measurement loop...")
    
    start_time = time.time()
    last_time = start_time
    last_bytes = get_loopback_recv_bytes()
    
    kbps_samples = []
    total_bytes_transferred = 0
    
    # Read loop
    while time.time() - start_time < TEST_DURATION:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to read frame from stream.")
            time.sleep(0.1)
            continue
            
        current_time = time.time()
        elapsed = current_time - last_time
        
        # Sample bandwidth every 1 second
        if elapsed >= 1.0:
            current_bytes = get_loopback_recv_bytes()
            diff_bytes = current_bytes - last_bytes
            
            # Avoid negative diffs on counter wrap-around/reset
            if diff_bytes < 0:
                diff_bytes = 0
                
            total_bytes_transferred += diff_bytes
            kbps = (diff_bytes / elapsed) / 1024.0
            kbps_samples.append(kbps)
            
            last_bytes = current_bytes
            last_time = current_time
            
            remaining = int(TEST_DURATION - (current_time - start_time))
            print(f"[{remaining:3d}s remaining] Current: {kbps:.2f} KB/s | Cumulative: {total_bytes_transferred / (1024*1024):.2f} MB", end="\r")
            
    cap.release()
    print("\nPhase 1 Complete.")
    
    avg_kbps = sum(kbps_samples) / len(kbps_samples) if kbps_samples else 0.0
    peak_kbps = max(kbps_samples) if kbps_samples else 0.0
    
    print(f"Total Bytes: {total_bytes_transferred}")
    print(f"Avg KBPS: {avg_kbps:.2f} KB/s")
    print(f"Peak KBPS: {peak_kbps:.2f} KB/s")
    
    return {
        "total_bytes": total_bytes_transferred,
        "avg_kbps": avg_kbps,
        "peak_kbps": peak_kbps
    }

def run_event_benchmark():
    print("\n==================================================")
    print("PHASE 2: Measuring Event-Only Bandwidth")
    print("Please start your Cloud API server and ingest.py now.")
    print("Make sure you select the active stream (CCTV1 Counter).")
    print("==================================================")
    
    # Reset log file
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        
    input("Press Enter once cloud_api and ingest.py are running to begin the 300s event window...")
    
    start_time = time.time()
    last_time = start_time
    last_pos = 0
    total_events = 0
    total_event_bytes = 0
    
    # Start tracking loopback bytes specifically during this phase to calculate event network kbps
    last_net_bytes = get_loopback_recv_bytes()
    net_bytes_transferred = 0
    
    while time.time() - start_time < TEST_DURATION:
        # Check the publisher log file
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                f.seek(last_pos)
                lines = f.readlines()
                last_pos = f.tell()
                for line in lines:
                    line = line.strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) == 2:
                            try:
                                total_events += 1
                                total_event_bytes += int(parts[1])
                            except ValueError:
                                pass
                                
        # Calculate raw network bytes over the period too
        current_time = time.time()
        elapsed = current_time - last_time
        if elapsed >= 1.0:
            current_net_bytes = get_loopback_recv_bytes()
            diff_net_bytes = current_net_bytes - last_net_bytes
            if diff_net_bytes < 0:
                diff_net_bytes = 0
            net_bytes_transferred += diff_net_bytes
            last_net_bytes = current_net_bytes
            last_time = current_time
            
            remaining = int(TEST_DURATION - (current_time - start_time))
            print(f"[{remaining:3d}s remaining] Events: {total_events} | Event Payload Bytes: {total_event_bytes} B", end="\r")
            
        time.sleep(0.5)
        
    print("\nPhase 2 Complete.")
    
    # Event average kbps is calculated from the event payload bytes over the test duration
    event_avg_kbps = (total_event_bytes / TEST_DURATION) / 1024.0
    
    print(f"Total Events: {total_events}")
    print(f"Total Event Bytes: {total_event_bytes}")
    print(f"Avg Event KBPS: {event_avg_kbps:.4f} KB/s")
    
    return {
        "total_events": total_events,
        "total_bytes": total_event_bytes,
        "avg_kbps": event_avg_kbps
    }

def main():
    print("AgentGrid Bandwidth Comparison Benchmarking Tool")
    print(f"Duration: {TEST_DURATION}s | Hardware: {HARDWARE_STRING}")
    
    # Run benchmarks
    raw_video_results = run_raw_video_benchmark()
    event_results = run_event_benchmark()
    
    # Extrapolations
    events_per_hour = (event_results["total_events"] / TEST_DURATION) * 3600.0
    estimated_daily_event_kb = (event_results["total_bytes"] / TEST_DURATION) * 86400.0 / 1024.0
    
    # Savings calculation
    if raw_video_results["total_bytes"] > 0:
        savings_percent = ((raw_video_results["total_bytes"] - event_results["total_bytes"]) / raw_video_results["total_bytes"]) * 100.0
    else:
        savings_percent = 0.0
        
    results = {
        "test_date": datetime.utcnow().isoformat() + "Z",
        "test_duration_seconds": TEST_DURATION,
        "hardware": HARDWARE_STRING,
        "raw_video": raw_video_results,
        "event_only": event_results,
        "extrapolated": {
            "events_per_hour": events_per_hour,
            "estimated_daily_event_kb": estimated_daily_event_kb
        },
        "savings_percent": savings_percent
    }
    
    # Save to file
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nResults successfully written to {RESULTS_FILE}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
