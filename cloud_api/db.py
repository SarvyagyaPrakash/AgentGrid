import os
import json
import logging
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment")

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        try:
            _pool = ThreadedConnectionPool(1, 10, dsn=DATABASE_URL)
            logging.info("Database connection pool initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing connection pool: {e}")
            raise RuntimeError(f"Database connection pool is not initialized: {e}")
    return _pool

def get_connection():
    return get_pool().getconn()

def put_connection(conn):
    if _pool is not None:
        _pool.putconn(conn)

def save_event(event: dict):
    """Saves an event to the event_log table."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO event_log (camera_id, agent, event_type, confidence, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    event.get("camera_id"),
                    event.get("agent"),
                    event.get("event_type"),
                    event.get("confidence"),
                    json.dumps(event.get("metadata", {}))
                )
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to save event: {e}")
        raise e
    finally:
        put_connection(conn)

def get_agent_configs():
    """Retrieves all agent configurations."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT camera_id, agent_name, enabled, updated_at
                FROM agent_configs
                """
            )
            results = cur.fetchall()
            # Convert datetime to string for JSON serialization
            for row in results:
                if row.get("updated_at"):
                    row["updated_at"] = row["updated_at"].isoformat()
            return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Failed to fetch agent configs: {e}")
        raise e
    finally:
        put_connection(conn)

def set_agent_config(camera_id: str, agent_name: str, enabled: bool):
    """Upserts/sets an agent configuration."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_configs (camera_id, agent_name, enabled, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (camera_id, agent_name)
                DO UPDATE SET enabled = EXCLUDED.enabled, updated_at = now()
                """,
                (camera_id, agent_name, enabled)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to set agent config: {e}")
        raise e
    finally:
        put_connection(conn)

def insert_camera(camera_id: str, name: str, rtsp_url: str):
    """Inserts a new camera into the cameras table."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cameras (camera_id, name, rtsp_url, added_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (camera_id)
                DO UPDATE SET name = EXCLUDED.name, rtsp_url = EXCLUDED.rtsp_url
                """,
                (camera_id, name, rtsp_url)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to insert camera: {e}")
        raise e
    finally:
        put_connection(conn)

def get_cameras():
    """Retrieves all cameras."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT camera_id, name, rtsp_url, added_at
                FROM cameras
                """
            )
            results = cur.fetchall()
            for row in results:
                if row.get("added_at"):
                    row["added_at"] = row["added_at"].isoformat()
            return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Failed to fetch cameras: {e}")
        raise e
    finally:
        put_connection(conn)

def get_recent_events(limit: int = 50):
    """Retrieves recent events."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, camera_id, agent, event_type, confidence, metadata, created_at
                FROM event_log
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            results = cur.fetchall()
            for row in results:
                if row.get("created_at"):
                    row["timestamp"] = row["created_at"].isoformat()
                    del row["created_at"]
            return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Failed to fetch recent events: {e}")
        raise e
    finally:
        put_connection(conn)


