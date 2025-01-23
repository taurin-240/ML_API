from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from PIL import ImageDraw, ImageFont, UnidentifiedImageError
from services import predict, save_or_upload_image, save_or_upload_json, draw_text, encode_schema, \
    get_images_and_filenames
from schemas import ImagePredict
import uvicorn
import json

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'))

templates = Jinja2Templates("templates")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


async def inference(files: List[UploadFile] = File()):
    images_and_filenames = [x for x in get_images_and_filenames(files)]
    img_predicts = await predict(images_and_filenames)
    annotations = []
    font = ImageFont.truetype('arial.ttf', size=27)
    for image_and_filename, img_predict in zip(images_and_filenames, img_predicts):
        image, filename = image_and_filename
        img_format = image.format if image.format is not None else 'JPEG'
        image = image.convert('RGB')
        image = image.resize([640,640])
        draw = ImageDraw.Draw(image)
        for box in img_predict.bboxes:
            draw.rectangle((*box.left_top, *box.right_bottom), outline='red', width=4)
            text = f"{box.box_class} {box.conf}"
            x, y = box.left_top[0], box.right_bottom[1]
            draw_text(draw, font, text, x, y)
        img_predict.link_to_processed_image = await save_or_upload_image(image, filename, img_format)
        annotations.append(img_predict)
    return annotations


@app.post("/inference-template")
async def inference_to_template(request: Request, files: List[UploadFile] = File(...)):
    try:
        annotations = await inference(files)
        annotations_json = json.dumps(annotations, default=encode_schema, indent=4)
        link_to_file = await save_or_upload_json(annotations_json)
    except UnidentifiedImageError:
        return templates.TemplateResponse("index.html", {"request": request,
                                                         "error": "Вы загрузили не изображение!"})
    return templates.TemplateResponse("index.html", {"request": request,
                                                     "annotations_file": link_to_file,
                                                     "annotations": annotations})


@app.post("/inference-json")
async def inference_to_json(files: List[UploadFile] = File(...)) -> List[ImagePredict] | dict:
    try:
        annotations = await inference(files)
    except UnidentifiedImageError:
        return {"error": "Вы загрузили не изображения!"}
    return annotations


if __name__ == '__main__':
    uvicorn.run('main:app')
