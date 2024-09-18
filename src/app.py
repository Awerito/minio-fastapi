import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from src.auth import create_admin_user
from src.config import FASTAPI_CONFIG, MIDDLEWARE_CONFIG, DEVELOPMENT
from src.routes.auth.auth import router as auth_router
from src.routes.files.files import router as files_router
from src.routes.posts.posts import router as posts_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Start of the application
    if DEVELOPMENT:
        logging.warning("Running in development mode!")

    # Create the admin user if it does not exist
    user = await create_admin_user()
    if user:
        logging.warning("Admin user created!")

    yield

    # End of the application
    pass


app = FastAPI(**FASTAPI_CONFIG, lifespan=lifespan)
app.add_middleware(CORSMiddleware, **MIDDLEWARE_CONFIG)

# Endpoints
app.include_router(auth_router, tags=["Users and Authentication"])
app.include_router(files_router, prefix="/files", tags=["Files"])
app.include_router(posts_router, prefix="/posts", tags=["Posts"])
