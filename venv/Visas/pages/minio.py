from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('test', image_name, file_object, file_object.size)
        return f"http://localhost:9000/test/{image_name}"
    except Exception as e:
        return {"error": str(e)}

def add_pic(new_visa, pic):
    client = Minio(
            endpoint=settings.AWS_S3_ENDPOINT_URL,
           access_key=settings.AWS_ACCESS_KEY_ID,
           secret_key=settings.AWS_SECRET_ACCESS_KEY,
           secure=settings.MINIO_USE_SSL
    )
    i = new_visa.id
    img_obj_name = f"{i}.jpg"

    if not pic:
        return Response({"error": "Нет файла для изображения логотипа."})
    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        return Response(result)

    new_visa.url = result
    new_visa.save()

    return Response({"message": "success"})
def delete_pic(pk):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{pk}.jpg"
    try:
        client.remove_object('test', img_obj_name)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}