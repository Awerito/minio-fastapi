from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse

from src.database import MongoDBConnectionManager
from src.minio.minio import upload_file, download_file, generate_presigned_url


router = APIRouter()


@router.post("/upload")
async def upload(
    user: str,
    title: str,
    description: str,
    file: UploadFile = File(...),
):
    try:
        if file.content_type != "image/jpeg":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG files are allowed.",
            )

        # add a unique identifier to the filename, ex: file_1234.jpg -> file_1234_<uuid4>.jpg
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required."
            )

        ext = file.content_type.split("/")[1]
        parts = file.filename.split(".")

        if len(parts) > 1:
            if parts[-1] == ext:
                name = ".".join(parts[:-1])
            else:
                name = ".".join(parts)

            filename = f"{name}_{uuid4()}.{ext}"
        else:
            filename = f"{file.filename}_{uuid4()}.{ext}"

        upload_file(file.file, filename)

        async with MongoDBConnectionManager() as db:
            await db.posts.insert_one(
                {
                    "user": user,
                    "title": title,
                    "description": description,
                    "filename": filename,
                    "created_at": datetime.now(),
                }
            )

        return {"message": "File uploaded successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/download")
async def download(object_name: str):
    try:
        file_path = f"downloads/{object_name}"
        file = download_file(object_name, file_path)

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {object_name} not found.",
            )

        return StreamingResponse(file, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/file-url")
async def file_url(object_name: str):
    try:
        url = generate_presigned_url(object_name)
        return {"url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
