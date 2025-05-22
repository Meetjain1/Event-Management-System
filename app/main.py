from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
import uvicorn
import os
from dotenv import load_dotenv
import logging

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

# Startup event to initialize rate limiter
@app.on_event("startup")
async def startup():
    try:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.error("REDIS_URL environment variable is not set")
            return

        logger.info(f"Connecting to Redis at: {redis_url.split('@')[-1]}")  # Log only host part for security
        redis_instance = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,  # 5 seconds timeout
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        # Test the connection
        await redis_instance.ping()
        logger.info("Successfully connected to Redis")
        
        await FastAPILimiter.init(redis_instance)
        logger.info("Rate limiter initialized successfully")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        # Continue without rate limiting if Redis is not available
    except Exception as e:
        logger.error(f"Unexpected error during startup: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
