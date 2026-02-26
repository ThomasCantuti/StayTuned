from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import podcasts, find_urls, scrape

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting AI Podcast Generator API")
    yield
    logger.info("Shutting down AI Podcast Generator API")

# Create FastAPI app
app = FastAPI(
    title="AI Podcast Generator API",
    description="Generate AI-powered podcasts from latest news",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(find_urls.router, prefix="/urls", tags=["urls"])
app.include_router(podcasts.router, prefix="/podcasts", tags=["podcasts"])
app.include_router(scrape.router, prefix="/scrape", tags=["scrape"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Podcast Generator API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-podcast-generator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )