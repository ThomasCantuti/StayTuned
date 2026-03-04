"""Route for discovering the best URLs for a given topic."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.routers.schemas import URLSearchRequest, URLSearchResponse
from app.services.web_tools.url_finder import URLFinder

router = APIRouter()
logger = logging.getLogger(__name__)

_finder = URLFinder()


@router.post("/search", response_model=URLSearchResponse)
async def search_urls(request: URLSearchRequest) -> URLSearchResponse:
    """
    Search for relevant URLs for a topic.
    These URLs can be saved and reused to generate podcasts.

    Uses crawl4ai to scrape Google search results and returns
    main-domain URLs whose content is most relevant to the topic.
    """
    try:
        logger.info("Searching URLs for topic: %s", request.topic)

        urls = await _finder.find_urls(
            topic=request.topic,
            n=request.max_sources,
        )

        logger.info("Found %d URLs for topic '%s'", len(urls), request.topic)

        return URLSearchResponse(
            topic=request.topic,
            urls=urls,
        )

    except Exception as e:
        logger.error("Search URLs error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/health")
async def health_check():
    """Health check for the find_urls router."""
    return {"status": "healthy", "service": "find_urls"}