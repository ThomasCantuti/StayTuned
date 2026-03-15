"""Route for discovering the best URLs for a given topic."""
from fastapi import APIRouter
import logging

from app.routers.schemas import URLSearchRequest, URLSearchResponse
from app.services.agents.agents import url_finder_agent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search", response_model=URLSearchResponse)
async def search_urls(request: URLSearchRequest) -> URLSearchResponse:
    """Search for relevant URLs for a topic."""
    try:
        logger.info("Searching URLs for topic: %s", request.topic)

        response = url_finder_agent(prompt=f"Topic: {request.topic}, Number of URLs: {request.max_sources}")

        if not isinstance(response.structured_output, URLSearchResponse):
            raise ValueError("Agent failed to return valid URL structure.")

        logger.info("Found %d URLs for topic '%s'", len(response.structured_output.urls), request.topic)

        return URLSearchResponse(
            topic=request.topic,
            urls=response.structured_output.urls,
        )

    except Exception as e:
        logger.error("Search URLs error: %s", e)
        return URLSearchResponse(topic=request.topic, urls=[])


@router.get("/health")
async def health_check():
    """Health check for the find_urls router."""
    return {"status": "healthy", "service": "find_urls"}
