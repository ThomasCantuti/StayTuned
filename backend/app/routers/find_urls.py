from fastapi import APIRouter, HTTPException, status
import logging

from app.routers.schemas import URLSearchRequest, URLSearchResponse
from app.services.web_tools.agents import url_finder_agent

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/search", response_model=URLSearchResponse)
async def search_urls(request: URLSearchRequest):
    """
    Search for relevant URLs for a topic.
    These URLs can be saved and reused to generate podcasts.
    """
    try:
        logger.info(f"Searching URLs for topic: {request.topic}")
        urls_response = url_finder_agent.structured_output(
            output_model=URLSearchResponse, 
            prompt=f"Find the most relevant news URLs for the topic: {request.topic}"
        )
        logger.info(f"URLs found: {urls_response.urls}")
        
        return URLSearchResponse(
            topic=request.topic,
            urls=urls_response.urls
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