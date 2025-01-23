from fastapi import UploadFile
from ultralytics import YOLO
from typing import List, Tuple
from PIL import Image
from schemas import BBox, ImagePredict
from config import AWS_S3_BUCKET_NAME, AWS_SETTINGS, MODEL_FILENAME, MODEL_CONFIDENCE
from io import BytesIO
from typing import Union
from uuid import uuid4
import aioboto3
from pydantic import BaseModel
import fitz


def pdf2images(pdf_file: UploadFile) -> List[Tuple[Image.Image, str]]:
    pdf_doc = fitz.open("pdf", pdf_file.file.read())
    zoom = 1
    mat = fitz.Matrix(zoom, zoom)
    results = []
    for i, page in enumerate(pdf_doc, start=1):
        filename = f'{pdf_file.filename[:-4]}-page-{i}.jpg'
        pixmap = page.get_pixmap(matrix=mat)
        yield Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples), filename
    return results


def get_images_and_filenames(files: List[UploadFile]):
    for file in files:
        if file.filename[-4:] == '.pdf':
            yield from pdf2images(file)
        else:
            yield Image.open(file.file), file.filename


async def predict(images_and_filenames: List[Tuple[Image.Image, ImagePredict]]) -> List[ImagePredict]:
    model = YOLO(MODEL_FILENAME)
    predicts = []
    for img, filename in images_and_filenames:
        #resize img into PIL
        img = img.resize([640,640])
        result = model.predict(img, conf=float(MODEL_CONFIDENCE))
        bboxes = []
        for conf, cls, xyxy in zip(result[0].boxes.conf.tolist(), result[0].boxes.cls.tolist(),
                                   result[0].boxes.xyxy.tolist()):
            left_top = (xyxy[0], xyxy[1])
            right_bottom = (xyxy[2], xyxy[3])
            bboxes.append(BBox(left_top=left_top,
                               conf=round(conf, 2),
                               right_bottom=right_bottom,
                               box_class=model.names[cls]))
        predicts.append(ImagePredict(filename=filename,
                                     bboxes=bboxes))
    return predicts


async def upload_object(file_key: str, file: Union[UploadFile, bytes, BytesIO]):
    session = aioboto3.Session()
    if type(file) == bytes:
        file = BytesIO(file)
    async with session.client(**AWS_SETTINGS) as s3:
        await s3.upload_fileobj(file, AWS_S3_BUCKET_NAME, file_key)
        return f'https://storage.yandexcloud.net/{AWS_S3_BUCKET_NAME}/{file_key}'


async def save_or_upload_image(image: Image.Image, img_filename: str, img_format):
    if AWS_S3_BUCKET_NAME is not None:
        img_extension = img_filename.split(".")[-1]
        file_key = f'{uuid4()}.{img_extension}'
        image_as_bytes = BytesIO()
        image.save(image_as_bytes, format=img_format)
        return await upload_object(file_key, image_as_bytes.getvalue())
    else:
        path = f'static/inferences/{img_filename}'
        image.save(path)
        return path


async def save_or_upload_json(content: str):
    filename: str = f'{uuid4()}.json'
    if AWS_S3_BUCKET_NAME is not None:
        return await upload_object(filename, content.encode())
    else:
        path = f'static/inference-jsons/{filename}'
        with open(path, 'w') as w_file:
            w_file.write(content)
        return path


def draw_text(draw, font, text: str, x: int, y: int):
    text_width = draw.textlength(text, font)
    text_height= font.size
    draw.rectangle((x - 5, y, x + text_width + 10, y + text_height), fill='#ff0000')
    draw.text((x, y), text, fill='#ffffff', font=font)


def encode_schema(obj):
    if isinstance(obj, BaseModel):
        return obj.dict()
    else:
        type_name = obj.__class__.__name__
        raise TypeError(f"Object of type '{type_name}' is not JSON serializable")
