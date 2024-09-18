import logging
import tempfile

from datetime import timedelta as td

from minio import Minio
from minio.error import S3Error

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


def upload_file(file_path, object_name):
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)

        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            tmp_file.write(file_path.read())
            tmp_file.flush()
            tmp_file.seek(0)
            minio_client.fput_object(MINIO_BUCKET, object_name, tmp_file.name)

        logging.debug(f"File {object_name} uploaded successfully to {MINIO_BUCKET}.")
    except S3Error as e:
        logging.debug(f"Error uploading file: {e}")


def download_file(object_name, file_path):
    try:
        file = minio_client.get_object(MINIO_BUCKET, object_name, file_path)
        logging.debug(f"File {object_name} downloaded successfully to {file_path}.")
        return file
    except S3Error as e:
        logging.debug(f"Error downloading file: {e}")
        return None


def generate_presigned_url(object_name, expiry=604800):
    try:
        url = minio_client.presigned_get_object(
            MINIO_BUCKET, object_name, expires=td(seconds=expiry)
        )
        logging.debug(f"Generated presigned URL: {url}")
        return url
    except S3Error as e:
        logging.debug(f"Error generating presigned URL: {e}")
        raise


# Example usage
# upload_file("my-bucket", "path/to/file.txt", "uploaded_file.txt")
# download_file("my-bucket", "uploaded_file.txt", "path/to/downloaded_file.txt")
