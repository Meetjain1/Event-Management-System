from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
import uvicorn
import os
from dotenv import load_dotenv
import logging
import asyncio
from alembic.config import Config
from alembic import command
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import routers
from app.api import auth, events  # adjust if path is different

app = FastAPI(
    title="Event Management System",
    description="A collaborative event management system with version control and real-time updates",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Add your routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/events", tags=["events"])

def run_migrations():
    try:
        logger.info("Running database migrations...")
        # Get the absolute path to alembic.ini
        alembic_ini_path = str(Path(__file__).parent.parent / "alembic.ini")
        
        # Create Alembic configuration and run upgrade
        alembic_cfg = Config(alembic_ini_path)
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise

# Startup event to initialize rate limiter and run migrations
@app.on_event("startup")
async def startup():
    # Run database migrations
    try:
        run_migrations()
    except Exception as e:
        logger.error(f"Failed to run migrations: {str(e)}")
        # Continue startup even if migrations fail
    
    # Initialize Redis rate limiter
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost")
        logger.info(f"Connecting to Redis at: {redis_url.split('@')[-1]}")
        redis_instance = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        await FastAPILimiter.init(redis_instance)
        logger.info("Rate limiter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        # Continue without rate limiting if Redis is not available

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
