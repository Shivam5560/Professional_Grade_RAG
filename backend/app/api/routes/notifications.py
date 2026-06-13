from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.messaging import manager
from app.api.deps import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Note: WebSocket endpoints cannot easily use standard Depends for async auth headers
# In a real scenario, the token could be passed as a query param. For now, we assume user_id is passed
@router.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, wait for disconnect
            data = await websocket.receive_text()
            # Can process incoming messages if needed, currently we just send out
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
