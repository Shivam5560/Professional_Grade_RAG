import json
import asyncio
import aio_pika
from fastapi import WebSocket
from typing import Dict, List, Any

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected to WebSocket.")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket.")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")

manager = ConnectionManager()

async def get_rabbitmq_connection() -> aio_pika.RobustConnection:
    return await aio_pika.connect_robust(settings.rabbitmq_url)

async def publish_message(queue_name: str, message: dict):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name,
        )

async def consume_notifications():
    """Background task to consume from the notifications queue and push to websockets."""
    while True:
        try:
            connection = await get_rabbitmq_connection()
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue("notifications", durable=True)
                
                logger.info("Started consuming notifications from RabbitMQ")
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            data = json.loads(message.body.decode())
                            user_id = data.get("user_id")
                            if user_id:
                                await manager.send_personal_message(json.dumps(data), str(user_id))
        except Exception as e:
            logger.error(f"Error in consume_notifications: {e}")
            await asyncio.sleep(5)  # Retry after 5 seconds
