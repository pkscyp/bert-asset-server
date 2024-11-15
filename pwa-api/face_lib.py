
from deepface import DeepFace
from fastapi import  HTTPException
from PIL import Image
import io
import numpy as np
import os
from datetime import  datetime,timezone 

logger=None 

backends = [
  'opencv', 
  'ssd', 
  'dlib', 
  'mtcnn', 
  'fastmtcnn',
  'retinaface', 
  'mediapipe',
  'yolov8',
  'yunet',
  'centerface',
]

def handle_checkin(req) -> bool:
    logger.info("exceuting checkin")
    try:
        byte_data = bytes(req['image'])
        image = Image.open(io.BytesIO(byte_data))
        user_id = req['user_id']
        file_dt=int(datetime.now(timezone.utc).timestamp())
        checkin_filename = f"{user_id}_check_in_org_{file_dt}.jpg"
        checkin_face_filename = f"{user_id}_check_in_face_{file_dt}.jpg"
        logger.info("detecing faces in checkin image")
        face_sts, checkin_face_img = detect_single_face(image,user_id)
        if face_sts == False:
            logger.info(" Picture has not Face")
            return False
        user_face_filename = f"{user_id}_face.jpg"
        user_face_image = f"{os.getcwd()}/images/{user_face_filename}"
        if not os.path.exists(user_face_image):
            logger.info("User face file does not exists")
            return False
        image.save( f"{os.getcwd()}/images/{checkin_filename}")
        checkin_face_img.save( f"{os.getcwd()}/images/{checkin_face_filename}")
        original_image =  Image.open(user_face_image)
        logger.info(f" size {original_image.size} {checkin_face_img.size} {user_face_image}")
        match_sts = verify_check_in(original_image,checkin_face_img,user_id)
        if not match_sts:
            return False
        
        return True
    except Exception as ex:
        logger.error(ex)
        return False

def handle_register(req) -> bool:
    try:
        byte_data = bytes(req['image'])
        image = Image.open(io.BytesIO(byte_data))
        user_id = req['user_id']
        image_filename = f"{user_id}_original.jpg"
        file_name = f"{os.getcwd()}/images/{image_filename}"
        face_sts, face_img = detect_single_face(image,user_id)
        if face_sts:
            logger.info(f" Disk file is {file_name}")
            image.save(file_name)
            face_img_name = f"{os.getcwd()}/images/{user_id}_face.jpg"
            face_img.save(face_img_name)
        
        return face_sts

    except Exception as ex:
        logger.error(ex)
        return False


def detect_single_face(image:Image,user_id:str):
    try:
        
        face_objs_list = DeepFace.extract_faces(
            img_path=np.array(image),
            detector_backend = backends[0],
            anti_spoofing = True
            )
        
        logger.info(f" Number of faces detected {len(face_objs_list)}")
        if len(face_objs_list) > 1:
            return False, None 
        logger.info(f"Detail confidence={face_objs_list[0]['confidence']} isreal={face_objs_list[0]['is_real']} score={face_objs_list[0]['antispoof_score']}")
        fo=face_objs_list[0]['facial_area']
        croped_img = image.crop((fo['x'],fo['y'],fo['x']+fo['w'],fo['y']+fo['h']))
        return face_objs_list[0]['is_real'], croped_img
    except Exception as e:
        logger.error(e)
        return False, None

def analyze_face(image:Image):
    objs = DeepFace.analyze(
            img_path = np.array(image), 
            actions = ['age', 'gender', 'race', 'emotion'],
            )
    logger.info(objs)


def verify_check_in(oimg:Image,simg:Image,user_id:str) -> bool:
    try:
       result = DeepFace.verify(img1_path=np.array(oimg),img2_path=np.array(simg),model_name ="Facenet512",anti_spoofing=True)
       logger.info(f"Verification result ={result}")
       if result['verified']:
           return True
       else:
           return False
    except Exception as ex:
        logger.error(ex)
        return False