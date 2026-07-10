import os
import json
import logging
from redis.asyncio import from_url
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL is not set in the environment")

# Initialize Redis client using from_url
redis_client = from_url(REDIS_URL, decode_responses=True)

async def publish_to_dashboard(event: dict):
    """Publishes a serialized event to the live events channel."""
    try:
        await redis_client.publish("agentgrid:live_events", json.dumps(event))
        logging.info(f"Published event to Redis: {event.get('event_type')}")
    except Exception as e:
        logging.error(f"Failed to publish event to Redis: {e}")

async def subscribe_dashboard():
    """Async generator yielding events from the live events channel."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("agentgrid:live_events")
    try:
        async for message in pubsub.listen():
            if message and message["type"] == "message":
                try:
                    yield json.loads(message["data"])
                except Exception as ex:
                    logging.error(f"Error parsing redis message data: {ex}")
    finally:
        await pubsub.unsubscribe("agentgrid:live_events")
        await pubsub.close()
