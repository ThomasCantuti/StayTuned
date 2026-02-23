import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from test_web_tools import router as web_tools_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(tests: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Tests")
    yield
    logger.info("Shutting down Tests")

# Create FastAPI app
tests = FastAPI(
    title="Tests",
    description="Generate AI-powered podcasts from latest news",
    version="1.0.0",
    lifespan=lifespan
)

tests.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
tests.include_router(web_tools_router, prefix="/urls", tags=["urls"])

@tests.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tests", "version": "1.0.0"}

@tests.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tests"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "test_main:tests",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )