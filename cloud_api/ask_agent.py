import datetime
import json
import urllib.request
import logging
import os
import re
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
    # Limit to top 10 most recent events to prevent LLM context overflow/confusion
    relevant_events = events[:10] if events else []
    
    # Construct a clean, structured representation of the events for the LLM
    events_str = ""
    if relevant_events:
        for idx, e in enumerate(relevant_events, 1):
            metadata = e.get("metadata") or {}
            caption = metadata.get("scene_caption", "N/A")
            events_str += (
                f"Event {idx}:\n"
                f"- Camera: {e.get('camera_id')}\n"
                f"- Agent: {e.get('agent')}\n"
                f"- Type: {e.get('event_type')}\n"
                f"- Confidence: {e.get('confidence')}\n"
                f"- Timestamp: {e.get('created_at') or e.get('timestamp')}\n"
                f"- Scene Caption (what the VLM saw): {caption}\n"
                f"- Extra Metadata: {json.dumps({k: v for k, v in metadata.items() if k != 'scene_caption'})}\n\n"
            )
    else:
        events_str = "No events matching the criteria found."

    prompt = (
        "You are 'AgentGrid Ask Your Cameras' reasoning assistant.\n"
        "Analyze the following event logs from Postgres and answer the user's question.\n"
        "NOTE: The events below are listed in descending order (newest/most recent first). Event 1 is the most recent event.\n\n"
        "CRITICAL RULES:\n"
        "1. If the user is greeting you (e.g. 'hi', 'hello', 'hey'), respond warmly, introduce yourself as AgentGrid assistant, and explain how you can help.\n"
        "2. Answer the question using the provided events where possible. Note that each event contains a 'Scene Caption (what the VLM saw)' field describing the actual visual detail recorded by a Vision-Language Model. Draw heavily from these scene captions for your answer to provide a rich description of what happened. Do not invent events.\n"
        "3. If the user asks general questions about yourself or the system, explain that you are AgentGrid's edge video analytics assistant.\n"
        "4. If no events are relevant and it is not a general/greeting query, explain that no matching events were found.\n"
        "5. Respond using a strict format detailing the Activity, Time, and Camera (e.g. Activity: [description], Time: [time], Camera: [camera_id]), and keep the response under 100 words by default.\n\n"
        f"Event Logs:\n{events_str}\n"
        f"Question: {question}\n"
        "Answer:"
    )
    
    base_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    
    # We want to try the primary URL first, and if localhost fails, try host.docker.internal
    urls_to_try = [base_url]
    if "localhost" in base_url:
        urls_to_try.append(base_url.replace("localhost", "host.docker.internal"))
    elif "127.0.0.1" in base_url:
        urls_to_try.append(base_url.replace("127.0.0.1", "host.docker.internal"))
        
    last_error = None
    res_text = ""
    
    model_name = os.environ.get("OLLAMA_MODEL", "llama3")
    
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    
    for url in urls_to_try:
        api_url = f"{url.rstrip('/')}/api/generate"
        try:
            req = urllib.request.Request(
                api_url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                res_text = res_data.get("response", "").strip()
                break
        except Exception as e:
            last_error = e
            logging.warning(f"Ollama connection failed at {api_url}: {e}")
            continue
            
    if not res_text and last_error:
        logging.error(f"Failed to communicate with local Ollama after trying all URLs: {last_error}")
        return f"Error: Local Ollama model failed to respond. (Is Ollama running locally with {model_name}? Details: {last_error})"

    # Strip thinking block for deepseek-r1
    clean_res = re.sub(r'<think>.*?</think>', '', res_text, flags=re.DOTALL).strip()
    return clean_res if clean_res else "no matching events found"

def ask_agent_query(question: str):
    """Executes the complete 2-step pipeline."""
    events = filter_events(question)
    
    # Fallback to recent events if no specific filter matches
    if not events:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, camera_id, agent, event_type, confidence, metadata, created_at FROM event_log ORDER BY created_at DESC LIMIT 20")
                events = cur.fetchall()
                for r in events:
                    if r.get("created_at"):
                        r["created_at"] = r["created_at"].isoformat()
        except Exception as e:
            logging.error(f"Error fetching fallback events: {e}")
        finally:
            put_connection(conn)
            
    answer = ask_ollama(question, events)
    return {
        "answer": answer,
        "matched_events": len(events) if events else 0,
        "source": "event_log"
    }
