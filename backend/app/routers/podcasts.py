from fastapi import APIRouter, HTTPException, status
import logging

from app.services.script_generator import ScriptGeneratorService
from app.services.tts import TTSGeneratorService
from app.routers.schemas import PodcastRequest, PodcastResponse
from app.services.web_tools.agents import scraper_agent, scraper_tool_limit
from app.services.web_tools.schemas import ScraperResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
script_generator = ScriptGeneratorService()
tts_generator = TTSGeneratorService()

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
            scraper_tool_limit.reset()
            result = scraper_agent(
                prompt=(
                    f"Find and extract the most relevant article about '{request.topic}' "
                    f"starting from this URL: {url}.\n\n"
                    "Follow your loop: browse_page → read_article → evaluate_content → decide.\n"
                    "If the first article isn't relevant, try another link. "
                    "Return the article URL, title, and a concise summary."
                ),
                structured_output_model=ScraperResponse,
            )
            assert isinstance(result.structured_output, ScraperResponse), "Expected ScraperResponse"
            article = result.structured_output
            all_articles.append({
                "script": article.content,
                "sources": article.url
            })
        
        if not all_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found from the provided URLs"
            )
        
        logger.info(f"Scraped {len(all_articles)} articles")
        
        news_content = "\n\n".join([
            f"URL: {article['sources']}\n\n{article['script']}" 
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
            script="".join([article["script"] for article in all_articles]),
            sources=[article["sources"] for article in all_articles],
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
