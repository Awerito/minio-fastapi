from fastapi import APIRouter

from src.database import MongoDBConnectionManager


router = APIRouter()


@router.get("/")
async def read_posts():
    async with MongoDBConnectionManager() as db:
        posts = await db.posts.find({}, {"_id": 0}).to_list(None)
        return posts
