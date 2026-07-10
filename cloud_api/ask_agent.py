import datetime
import json
import urllib.request
import logging
from psycopg2.extras import RealDictCursor
from db import get_connection, put_connection

def filter_events(question: str):
    """Step 1: Plain SQL/Python keyword/date filtering against the event_log table."""
    q = question.lower()
    
    conn = get_connection()
    try:
        # Fetch camera names and ids to match against question
        cameras = []
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT camera_id, name FROM cameras")
            cameras = cur.fetchall()
            
        where_clauses = []
        params = []
        
        # Camera filter
        matched_camera_ids = []
        for cam in cameras:
            cam_id = cam["camera_id"].lower()
            cam_name = cam["name"].lower()
            if cam_id in q or cam_name in q:
                matched_camera_ids.append(cam["camera_id"])
        
        if matched_camera_ids:
            where_clauses.append("camera_id = ANY(%s)")
            params.append(matched_camera_ids)
            
        # Agent / Event Type filter
        if "intrusion" in q:
            where_clauses.append("agent = %s")
            params.append("intrusion_detection")
        elif "productivity" in q or "idle" in q or "active" in q or "away" in q:
            where_clauses.append("agent = %s")
            params.append("productivity_tracker")
            
        # Date / Time filter
        now = datetime.datetime.now(datetime.timezone.utc)
        if "last night" in q:
            # From 10 PM yesterday to 6 AM today
            today = now.date()
            yesterday = today - datetime.timedelta(days=1)
            start_time = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 22, 0, 0, tzinfo=datetime.timezone.utc)
            end_time = datetime.datetime(today.year, today.month, today.day, 6, 0, 0, tzinfo=datetime.timezone.utc)
            where_clauses.append("created_at BETWEEN %s AND %s")
            params.extend([start_time, end_time])
        elif "today" in q:
            start_time = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=datetime.timezone.utc)
            where_clauses.append("created_at >= %s")
            params.append(start_time)
        elif "yesterday" in q:
            yesterday = now.date() - datetime.timedelta(days=1)
            start_time = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=datetime.timezone.utc)
            end_time = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=datetime.timezone.utc)
            where_clauses.append("created_at BETWEEN %s AND %s")
            params.extend([start_time, end_time])
            
        # Construct raw SQL query
        sql = "SELECT id, camera_id, agent, event_type, confidence, metadata, created_at FROM event_log"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY created_at DESC LIMIT 100"
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            
            # Format results, converting datetimes to ISO strings
            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()
            return rows
    except Exception as e:
        logging.error(f"Error filtering events: {e}")
        return []
    finally:
        put_connection(conn)

def ask_ollama(question: str, events: list) -> str:
    """Step 2: Send filtered rows to local Ollama instance and ask it to summarize/answer."""
    if not events:
        return "no matching events found"
        
    # Serialize events to compact JSON, retaining full metadata (and track_id)
    events_json = json.dumps(events, separators=(',', ':'))
    
    prompt = (
        "You are 'AgentGrid Ask Your Cameras' reasoning assistant.\n"
        "Analyze the following event logs from Postgres and answer the user's question.\n"
        "CRITICAL RULES:\n"
        "1. You must answer the question ONLY using the provided events.\n"
        "2. Do not assume or invent events. Do not mention events not listed in the JSON.\n"
        "3. If the list is empty or does not contain events answering the question, say exactly 'no matching events found'.\n"
        "4. Pay close attention to 'metadata.track_id' if present, to see if the same person or entity triggered different events.\n\n"
        f"Event Logs (JSON):\n{events_json}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )
    
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("response", "").strip()
    except Exception as e:
        logging.error(f"Failed to communicate with local Ollama: {e}")
        return f"Error: Local Ollama model failed to respond. (Is Ollama running locally with llama3.2:1b? Details: {e})"

def ask_agent_query(question: str):
    """Executes the complete 2-step pipeline."""
    events = filter_events(question)
    answer = ask_ollama(question, events)
    return {
        "answer": answer,
        "matched_events": len(events),
        "source": "event_log"
    }
