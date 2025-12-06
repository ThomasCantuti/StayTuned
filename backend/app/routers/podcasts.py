from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging
import time

from app.services.scraper import ScraperService
from app.services.script_generator import ScriptGeneratorService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
scraper = ScraperService()
script_generator = ScriptGeneratorService()


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
        
        # Step 1: Scrape content from URLs
        all_articles = []
        for url in request.urls:
            try:
                articles = scraper.scrape_news_site(url, max_articles=request.max_articles_per_site)
                all_articles.extend(articles)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.warning(f"Error scraping {url}: {e}")
                continue
        
        if not all_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found from the provided URLs"
            )
        
        logger.info(f"Scraped {len(all_articles)} articles")
        
        # Step 2: Prepare content and generate script
        news_content = "\n\n".join([
            f"URL: {article['url']}\n\n{article['content']}" 
            for article in all_articles
        ])
        
        script = script_generator.generate_podcast_script(
            duration=request.duration,
            topic=request.topic,
            news_content=news_content
        )
        
        return PodcastResponse(
            topic=request.topic,
            duration=request.duration,
            script=script,
            sources=[article['url'] for article in all_articles]
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