import logging
from ddgs import DDGS
from strands.tools import tool
from .schemas import SearchResponse, SearchResult

logger = logging.getLogger(__name__)


@tool
def search_web(query: str, max_results: int = 10) -> SearchResponse:
    """Search the web using DuckDuckGo and return results.

    Use this tool to find URLs relevant to a topic. You can call it
    multiple times with different queries to broaden coverage.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (1-25, default 10).
    """
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        logger.error(f"DuckDuckGo search failed: {exc}")
        return SearchResponse(query=query, results=[])

    results = [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("href", ""),
            snippet=r.get("body", ""),
        )
        for r in raw
        if r.get("href")
    ]

    return SearchResponse(query=query, results=results)
