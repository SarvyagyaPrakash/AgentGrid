import asyncio

class FrameBus:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, agent):
        """Subscribe an agent to the frame bus."""
        self.subscribers.append(agent)

    async def broadcast(self, frame):
        """Broadcast a frame to all subscribed agents concurrently."""
        tasks = []
        for agent in self.subscribers:
            if getattr(agent, 'enabled', True):
                tasks.append(asyncio.create_task(agent.on_frame(frame)))
        if tasks:
            await asyncio.gather(*tasks)
