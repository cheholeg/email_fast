import logging

from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect

from services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("New WebSocket connection attempt")
    await manager.connect(websocket)
    logger.info("WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket data: {data}")
            await manager.broadcast(data)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        manager.disconnect(websocket)
        logger.info("WebSocket connection closed and removed from manager")
