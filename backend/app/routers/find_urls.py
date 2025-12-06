from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

from app.agents.url_finder import URLFinderAgent

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize service
url_finder = URLFinderAgent()


class URLSearchRequest(BaseModel):
    """Request model for URL search."""
    topic: str
    max_sources: int = 10


class URLSearchResponse(BaseModel):
    """Response model for found URLs."""
    topic: str
    urls: list[str]


@router.post("/search", response_model=URLSearchResponse)
async def search_urls(request: URLSearchRequest):
    """
    Search for relevant URLs for a topic.
    These URLs can be saved and reused to generate podcasts.
    """
    try:
        logger.info(f"Searching URLs for topic: {request.topic}")
        
        agent = url_finder.get_agent()
        agent_response = agent.run(
            f"Give me the {request.max_sources} best sources to get updated news on {request.topic}."
        )
        urls = url_finder.agent_response_to_string(agent_response.text)
        
        logger.info(f"Found {len(urls)} URLs")
        
        return URLSearchResponse(
            topic=request.topic,
            urls=urls
        )
        
    except Exception as e:
        logger.error(f"Search URLs error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check for the find_urls router."""
    return {"status": "healthy", "service": "find_urls"}