import io
import os
import logging
from minio import Minio
from fastapi import UploadFile
from minio.error import S3Error
from datetime import datetime, timedelta

from src.config import (
    MINIO_URL,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    MINIO_BUCKET,
)


minio_client = Minio(
    MINIO_URL,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def is_image(filename: str, content_type: str) -> bool:
    valid_extensions = [".jpg", ".jpeg", ".png"]
    _, ext = os.path.splitext(filename)
    valid_ext = ext.lower() in valid_extensions
    valid_content_type = content_type.startswith("image/")

    return valid_ext and valid_content_type


def generate_presigned_url(object_name, duration=604800):
    try:
        url = minio_client.presigned_get_object(
            MINIO_BUCKET, object_name, expires=timedelta(seconds=duration)
        )
        logging.debug(f"Generated presigned URL: {url}")
        return url
    except S3Error as e:
        logging.debug(f"Error generating presigned URL: {e}")
        raise Exception("Error generating presigned URL")


async def upload_file(file: UploadFile, object_name: str) -> tuple[str | None, dict]:
    try:
        # Check if the bucket exists; create it if it doesn't
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)

        # Read the file content
        file_content = await file.read()
        file_size = file.size if file.size else len(file_content)

        if file_size <= 0:
            raise ValueError("File is empty")

        # Upload the file to MinIO
        minio_client.put_object(
            MINIO_BUCKET, object_name, io.BytesIO(file_content), file_size
        )

        # Generate a presigned URL for the uploaded file
        seven_days = 604800
        url = generate_presigned_url(object_name, duration=seven_days)
        logging.debug(f"File {object_name} uploaded successfully to {MINIO_BUCKET}.")
        return (
            None,
            {
                "img_url": url,
                "url_expire": datetime.now() + timedelta(seconds=seven_days),
            },
        )

    except ValueError as e:
        logging.error(f"Upload failed: {e}")
        return (str(e), {})
    except S3Error as e:
        logging.error(f"Error uploading file to MinIO: {e}")
        return (str(e), {})
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return (str(e), {})


def download_file(object_name, file_path):
    try:
        file = minio_client.get_object(MINIO_BUCKET, object_name, file_path)
        logging.debug(f"File {object_name} downloaded successfully to {file_path}.")
        return file
    except S3Error as e:
        logging.debug(f"Error downloading file: {e}")
        return None


# Example usage
# upload_file("my-bucket", "path/to/file.txt", "uploaded_file.txt")
# download_file("my-bucket", "uploaded_file.txt", "path/to/downloaded_file.txt")
