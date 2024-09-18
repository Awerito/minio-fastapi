import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from src.config import FASTAPI_CONFIG, MIDDLEWARE_CONFIG, DEVELOPMENT
from src.routes.files.files import router as files_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Start of the application
    if DEVELOPMENT:
        logging.warning("Running in development mode!")

    yield

    # End of the application
    pass


app = FastAPI(**FASTAPI_CONFIG, lifespan=lifespan)
app.add_middleware(CORSMiddleware, **MIDDLEWARE_CONFIG)

# Endpoints
app.include_router(files_router, prefix="/files", tags=["Files"])
