from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse

from src.minio.minio import upload_file, download_file, generate_presigned_url


router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        upload_file(file.file, file.filename)
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
