import os

from uuid import uuid4
from bson import ObjectId
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends

from src.schemas.filter import MemesFilter
from src.auth import User, current_active_user
from src.database import MongoDBConnectionManager
from src.minio.minio import upload_file, is_image


router = APIRouter(prefix="/memes")


@router.get("/")
async def get_memes(filter: MemesFilter = Depends(MemesFilter)):
    sort = {"created_at": -1} if filter.sort_by == "new" else {"likes": -1}
    async with MongoDBConnectionManager() as db:
        # With _id to str
        requests = db.memes.find({}, sort=sort).skip((filter.page - 1) * filter.limit)
        memes = await requests.to_list(length=filter.limit)
        for meme in memes:
            meme["_id"] = str(meme["_id"])

    return memes


@router.get("/{id}")
async def get_meme(id: str):
    async with MongoDBConnectionManager() as db:
        meme = await db.memes.find_one({"_id": ObjectId(id)})

    if not meme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meme not found"
        )

    meme["_id"] = str(meme["_id"])

    # TODO: Lookup comments

    return meme


@router.put("/{id}")
async def update_meme(id: str, user: User = Depends(current_active_user)):
    async with MongoDBConnectionManager() as db:
        meme = await db.memes.find_one({"_id": ObjectId(id)})

        if not meme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meme not found"
            )

        existing_like = await db.likes.find_one({"user": user.username, "meme": id})

        if not existing_like:
            # Add like to user
            add_user_like_result = await db.likes.insert_one(
                {"user": user.username, "meme": id, "created_at": datetime.now()}
            )

            if not add_user_like_result.inserted_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Update failed",
                )

            # Increment like to post
            inc_like_result = await db.memes.update_one(
                {"_id": ObjectId(id)}, {"$inc": {"likes": 1}}
            )

            if not inc_like_result.modified_count:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Update failed",
                )
        else:
            # Remove like from user
            remove_user_like_result = await db.likes.delete_one(
                {"user": user.username, "meme": id}
            )

            if not remove_user_like_result.deleted_count:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Update failed",
                )

            # Substract like to post
            dec_like_result = await db.memes.update_one(
                {"_id": ObjectId(id)}, {"$inc": {"likes": -1}}
            )

            if not dec_like_result.modified_count:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Update failed",
                )

    return {"message": "Meme updated"}


@router.post("/")
async def upload(
    title: str,
    description: str,
    file: UploadFile = File(...),
    user: User = Depends(current_active_user),
):
    if not file.filename or not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File not provided"
        )

    # Validate file as an image file
    if not is_image(file.filename, file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only image files"
        )

    # Validate file size (20MB)
    if not file.size or file.size > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File too large"
        )

    # Generate a unique object name
    _, ext = os.path.splitext(file.filename)
    object_name = f"{uuid4()}{ext}"

    # Upload file to MinIO
    error, url = await upload_file(file, object_name)

    if error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error
        )

    meme = {
        "title": title,
        "description": description,
        "object_name": object_name,
        "filename": file.filename,
        "img_url": url,
        "created_at": datetime.now(),
        "user": user.username,
        "likes": 0,
    }

    # Save meme to MongoDB
    async with MongoDBConnectionManager() as db:
        result = await db.memes.insert_one(meme)

    return {"id": str(result.inserted_id), "url": url}
