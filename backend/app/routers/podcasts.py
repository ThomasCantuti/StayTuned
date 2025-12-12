from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging
import time

from app.services.scraper import ScraperService
from app.services.script_generator import ScriptGeneratorService
from app.services.tts import TTSGeneratorService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
scraper = ScraperService()
script_generator = ScriptGeneratorService()
tts_generator = TTSGeneratorService()

class PodcastRequest(BaseModel):
    """Request model for podcast generation."""
    topic: str
    urls: list[str]  # URLs provided by the user
    duration: int = 10  # duration in minutes
    max_articles_per_site: int = 3


class PodcastResponse(BaseModel):
    """Response model for generated podcast."""
    topic: str
    duration: int
    script: str
    sources: list[str]
    audio_path: str


@router.post("/generate", response_model=PodcastResponse)
async def generate_podcast(request: PodcastRequest):
    """
    Generate a new podcast from the provided URLs:
    1. Scrape article content from the URLs
    2. Generate podcast script
    """
    try:
        logger.info(f"Generating podcast for topic: {request.topic}")
        logger.info(f"Using {len(request.urls)} URLs")
        
        all_articles = []
        for url in request.urls:
                articles = scraper.scrape_news_site(url, max_articles=request.max_articles_per_site)
                all_articles.extend(articles)
                time.sleep(1)
        
        if not all_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found from the provided URLs"
            )
        
        logger.info(f"Scraped {len(all_articles)} articles")
        
        news_content = "\n\n".join([
            f"URL: {article['url']}\n\n{article['content']}" 
            for article in all_articles
        ])
        
        logger.info(f"Generated podcast script: {news_content}")
        
        script = script_generator.generate_podcast_script(
            duration=request.duration,
            topic=request.topic,
            news_content=news_content
        )
        
        audio_path = tts_generator.generate_audio(script)
        
        return PodcastResponse(
            topic=request.topic,
            duration=request.duration,
            script=script,
            sources=[article['url'] for article in all_articles],
            audio_path=audio_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate podcast error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check for the podcasts router."""
    return {"status": "healthy", "service": "podcasts"}
