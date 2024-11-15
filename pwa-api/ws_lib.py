import uuid
from datetime import datetime
import json 
from fastapi import WebSocket
import asyncio
import face_lib as flib

logger = None 
init_done=False

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, user_name,websocket: WebSocket):
        try:
            await websocket.accept()
            websocket.user_id=user_name
            self.active_connections.append(websocket)
        except Exception as ex:
            logger.error("Error ",ex)
    

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except Exception as ex:
            logger.error(ex)
            pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as ex:
            logger.error(ex)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as ex:
                logger.error(ex)

manager = ConnectionManager()

def init(_logger):
    global logger 
    global init_done
    if not init_done:
        logger = _logger
        init_done=True
        flib.logger = _logger

def close():
    global logger 
    global init_done
    if init_done:
        init_done=False

async def handle_webrecv(websocket:WebSocket,data:str):
    id = str(uuid.uuid4())
    jstr = json.loads(data)
    jstr['id'] = id 
    jstr['user_id'] = websocket.user_id 
    rqtype = jstr['type'] or 'register'
    logger.info(f"Received message from {websocket.user_id}")
    handle_sts=False 
    if rqtype == "register":
        handle_sts = flib.handle_register(jstr)
    if rqtype == "checkin":
        logger.info("running chekin commands")
        handle_sts = flib.handle_checkin(jstr)

    status = "Accepted" if handle_sts else "Rejected"
    resp = f"Received Request Type={rqtype} id={id} {status} "
    await manager.send_personal_message(resp,websocket)
    logger.info(resp)
    