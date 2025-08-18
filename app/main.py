import redis
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.routes import auth, books
from app.db.session import get_db, Base
from app.utils.error_logger import setup_logging
from app.utils.app_redis import redis_client


setup_logging()


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Test Redis connection
    try:
        redis_client.ping()
        print("Connected to Redis")
    except redis.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
        raise
    yield
    # Shutdown: Close Redis connection
    redis_client.close()


# Initialize FastAPI
app = FastAPI(
    lifespan=lifespan,
)


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Repository For Books!!"}


# Register routers
app.include_router(auth.router, tags=["Custom Auth Management"])
app.include_router(books.router, tags=["Book Management"])
