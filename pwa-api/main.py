
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
import socket 
from datetime import datetime, timezone, timedelta,time
from typing import List, Any
import uvicorn
import  pathlib
import logging
import sys,os
import atexit
import json
import platform
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, APIRouter, Request, Response, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi import File, UploadFile
import uuid
import face_lib as facelib
import numpy as np
from PIL import Image
import io
import ws_lib as wsf


API_BOOT_TIME= datetime.now(timezone.utc).isoformat()[0:22]

router = APIRouter(prefix="")

logger = logging.getLogger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global logger 
    logger.info("Application Starting .. attempting to connect to database")
    wsf.init(logger)
    yield
    logger.info("Application Shutdown .. attempting to disconnect from database")
    

def init_filelogging():
    format = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
    logger.setLevel(logging.INFO)
    # logdir = os.environ.get("LOG_DIR","logs")
    # logFileName="{}/geofence_backend_api_{}_pid_{}.log".format(logdir,socket.gethostname(),os.getpid())
    # fileHandler = logging.handlers.RotatingFileHandler(logFileName,mode='a',maxBytes=500000000,backupCount=10)
    # fileHandler.setFormatter(format)
    # logger.addHandler(fileHandler)
    stdout=logging.StreamHandler(sys.stdout)
    stdout.setFormatter(format)
    stdout.setLevel(logging.INFO)
    logger.addHandler(stdout)
    facelib.logger = logger
    for _log in ["uvicorn", "uvicorn.error","uvicorn.access"]:
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

def CreateApp():
    init_filelogging()
    app = FastAPI(title="Synergy Bert APIs",
            version="1.0.0",
            summary="This system provide Apis for Bert",
            contact={
                "name": "Pankaj Srivastava",
                "email": "psrivastava@sentineladvantage.com",
                },
            license_info={
                    "name": "Sentinel Offender Service LLC"
                },
                lifespan=lifespan
            )
    Instrumentator().instrument(app).expose(app)
    app.include_router(router)
    logger.info("Running Api Server Now...")
    logger.info('API is starting up')  
    app.mount("/ui", StaticFiles(directory="ui"), name="ui") 
    os.makedirs(os.path.dirname(f"{os.getcwd()}/images/"), exist_ok=True)
    return app

def onExiting():
    logger.error("Existing System")
    wsf.close()

atexit.register(onExiting)

@router.get("/health")
async def health():
    return {"message": "Geofence Backend Api Running fine since {} Server Name={}".format(API_BOOT_TIME,socket.gethostname())}


@router.post("/bert/v1/register/{user_id}")
async def register(user_id:str, user_image: UploadFile = File(...)) -> JSONResponse: 
    try:
        logger.info(f" received file name={user_image.filename}")
        filename, file_extension = os.path.splitext(user_image.filename)
        contents = user_image.file.read()
        image = Image.open(io.BytesIO(contents))
        face_sts, face_img = facelib.detect_single_face(image,user_id)
        logger.info(f" Face image is acceptable status {face_sts}")
        
        os.makedirs(os.path.dirname(f"{os.getcwd()}/images/"), exist_ok=True)
        file_dt=int(datetime.now(timezone.utc).timestamp())
        image_filename = f"{user_id}_original.{file_extension}"
        file_name = f"{os.getcwd()}/images/{image_filename}"
        logger.info(f" Disk file is {file_name}")
        image.save(file_name)       
        if face_sts:
            face_img_name = f"{os.getcwd()}/images/{user_id}_face.{file_extension}"
            face_img.save(face_img_name)
            facelib.analyze_face(face_img)

        resp = jsonable_encoder({'status':0,'request_id': uuid.uuid4(),'user_id':user_id})
        return JSONResponse(content=resp)
    except Exception as er:
        logger.error('error',er)
        return JSONResponse(status_code=500, content=jsonable_encoder({'status':-1,'user_id':user_id,'error': er}))
    finally:
        user_image.file.close()

@router.post("/bert/v1/check_in/{user_id}")
async def check_in(user_id:str, user_image: UploadFile = File(...)) -> JSONResponse: 
    try:
        logger.info(f" received file name={user_image.filename}")

        filename, file_extension = os.path.splitext(user_image.filename)
        os.makedirs(os.path.dirname(f"{os.getcwd()}/images/"), exist_ok=True)
        file_dt=int(datetime.now(timezone.utc).timestamp())
        image_filename = f"{user_id}_face.{file_extension}"
        file_name = f"{os.getcwd()}/images/{image_filename}"
        if not os.path.exists(file_name):
            return HTTPException(status_code=404, detail=f"registration not found for {user_id}")
        
        
        contents = user_image.file.read()
        image = Image.open(io.BytesIO(contents))
        face_sts, face_img = facelib.detect_single_face(image,user_id)
        logger.info(f" Face image is acceptable status {face_sts}")
        if face_sts:
            original_image =  Image.open(file_name)
            match_sts = facelib.verify_check_in(original_image,image,user_id)
            if match_sts:
                resp = jsonable_encoder({'status':0,'request_id': uuid.uuid4(),'user_id':user_id})
                return JSONResponse(content=resp)
        resp = jsonable_encoder({'status':-2,'error': 'check-in failed','user_id':user_id})
        return JSONResponse(content=resp)
    except Exception as er:
        logger.error('error',er)
        return JSONResponse(status_code=500, content=jsonable_encoder({'status':-1,'user_id':user_id,'error': er}))
    finally:
        user_image.file.close()


@router.websocket("/bertws/{user_name}")
async def pulsar_integration(user_name:str,websocket: WebSocket):
     wsf.init(logger)
     await wsf.manager.connect(user_name,websocket)
     try:
          while True:
               data = await websocket.receive_text()
               await wsf.handle_webrecv(websocket,data)
     except WebSocketDisconnect:
        wsf.manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app=CreateApp(), host="0.0.0.0", port=9000,log_config=None)

