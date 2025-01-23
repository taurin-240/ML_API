from dotenv import load_dotenv
import os

load_dotenv()

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME")
MODEL_FILENAME = os.environ.get("MODEL_FILENAME")
MODEL_CONFIDENCE = os.environ.get('MODEL_CONFIDENCE')

AWS_SETTINGS = {
    "service_name": 's3',
    "endpoint_url": "https://storage.yandexcloud.net",
    "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
    "aws_access_key_id": AWS_ACCESS_KEY_ID
}
