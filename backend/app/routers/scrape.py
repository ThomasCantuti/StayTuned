"""Route for scraping URLs using crawl4ai and returning best content."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.routers.schemas import ScrapeRequest, ScrapeResponse, ScrapedArticleOut
from app.services.scraper import CrawlScraper

router = APIRouter()
logger = logging.getLogger(__name__)

_scraper = CrawlScraper()


@router.post("/extract", response_model=ScrapeResponse)
async def extract_content(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape the given URLs and return the best content related to the topic.

    Uses crawl4ai (Playwright-based) for JS-rendered pages, then ranks
    articles by topic relevance and cleans them via the LLM.
    """
    logger.info("Scraping %d URLs for topic: '%s'", len(request.urls), request.topic)

    try:
        articles = await _scraper.scrape_and_rank(
            urls=request.urls,
            topic=request.topic,
            min_relevance=request.min_relevance,
        )
    except Exception as e:
        logger.error("Scrape error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    if not articles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant content found from the provided URLs",
        )

    top_articles = articles[: request.max_articles]

    response = ScrapeResponse(
        topic=request.topic,
        articles=[
            ScrapedArticleOut(
                url=a.url,
                title=a.title,
                content=a.markdown,
                relevance_score=a.relevance_score,
            )
            for a in top_articles
        ],
    )

    logger.info(
        "Returning %d articles (best score: %s)",
        len(response.articles),
        response.articles[0].relevance_score,
    )
    return response


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check for the scrape router."""
    return {"status": "healthy", "service": "scrape"}
