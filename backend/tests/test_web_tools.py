from fastapi import APIRouter, HTTPException, status
import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.routers.schemas import URLSearchRequest, URLSearchResponse, ScrapeRequest, ScrapeResponse, ScrapedArticleOut
from app.services.web_tools.agents import url_finder_agent, scraper_agent, scraper_tool_limit
from app.services.web_tools.schemas import ScraperRequest, ScraperResponse
from app.services.scraper import CrawlScraper

router = APIRouter()
logger = logging.getLogger(__name__)

_scraper = CrawlScraper()

@router.post("/search", response_model=URLSearchResponse)
async def search_urls(request: URLSearchRequest):
    """
    Search for relevant URLs for a topic.
    These URLs can be saved and reused to generate podcasts.
    """
    try:
        logger.info(f"Searching URLs for topic: {request.topic}")
        result = url_finder_agent(
            prompt=f"Find the most relevant news URLs for the topic: {request.topic}",
            structured_output_model=URLSearchResponse,
        )
        assert isinstance(result.structured_output, URLSearchResponse), "Expected URLSearchResponse"
        urls_response = result.structured_output
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


@router.post("/scrape", response_model=ScraperResponse)
async def scrape_url(request: ScraperRequest):
    """
    Scrape a URL for relevant content about a topic.
    The agent will autonomously loop: explore → read → evaluate → retry
    until it finds the best article.
    """
    try:
        logger.info(f"Scraping URL: {request.url} for topic: {request.topic}")
        scraper_tool_limit.reset()
        result = scraper_agent(
            prompt=(
                f"Your task is to find the most relevant article about '{request.topic}' "
                f"starting from this URL: {request.url}.\n\n"
                "Follow your agent loop workflow:\n"
                "1. Use `browse_page` or `search_links` to explore the page and find article links.\n"
                "2. Use `read_article` on the most promising link.\n"
                "3. Use `evaluate_content` to check if the article is relevant to the topic.\n"
                "4. If the evaluation says `should_try_another`, pick a different link and repeat.\n"
                "5. Once you have a good article, synthesize it into a clean summary.\n\n"
                "Return the specific article URL, its title, and the summarized content."
            ),
            structured_output_model=ScraperResponse,
        )
        assert isinstance(result.structured_output, ScraperResponse), "Expected ScraperResponse"
        scraper_response = result.structured_output
        logger.info(f"URL successfully scraped: {scraper_response.url}")

        return ScraperResponse(
            url=scraper_response.url,
            content=scraper_response.content,
            title=scraper_response.title,
            relevance_score=scraper_response.relevance_score,
        )

    except Exception as e:
        logger.error(f"Scrape URL error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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