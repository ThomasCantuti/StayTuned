"""Scraping service using crawl4ai deep crawling + BM25 content filtering."""

import logging

from crawl4ai import AsyncWebCrawler, BrowserConfig

from app.services.web_tools.config import _MIN_WORDS, build_crawl_config
from app.services.web_tools.schemas import ScrapedArticle
from app.services.web_tools.scoring import score_relevance

logger = logging.getLogger(__name__)


class CrawlScraper:
    """Scrapes a URL using crawl4ai BFS deep crawl + BM25 topic filtering.

    Given a seed URL (e.g. a blog index) and a topic, it:
    1. Crawls the seed page and follows internal links (depth=1)
    2. Prioritises links whose text/URL match topic keywords
    3. Filters each page's content with BM25 to keep only topic-relevant text
    4. Returns scored articles sorted by relevance
    """

    def __init__(self) -> None:
        self._browser_cfg = BrowserConfig(headless=True, verbose=False)

    async def scrape_url(
        self, url: str, topic: str, *, max_follow: int = 5
    ) -> list[ScrapedArticle]:
        """Scrape *one* seed URL, following article links, and return
        a list of articles ranked by topic relevance.

        Args:
            url: Seed URL (e.g. a blog listing page).
            topic: The topic to search for.
            max_follow: Max pages to crawl (seed + followed links).
        """
        config = build_crawl_config(topic, max_pages=max_follow + 1)
        articles: list[ScrapedArticle] = []

        try:
            async with AsyncWebCrawler(config=self._browser_cfg) as crawler:
                raw = await crawler.arun(url=url, config=config)

                # arun() may return a list-like container or an
                # async generator (when stream=True). Normalise to a list.
                if hasattr(raw, "__aiter__"):
                    results = [r async for r in raw]  # type: ignore[union-attr]
                else:
                    results = list(raw)  # type: ignore[arg-type]

                for r in results:
                    if not r.success:
                        continue

                    title = (r.metadata or {}).get("title", "")

                    # Prefer BM25-filtered fit_markdown, fall back to raw
                    md = ""
                    if r.markdown:
                        md = (
                            r.markdown.fit_markdown
                            or r.markdown.raw_markdown
                            or str(r.markdown)
                        )

                    if not md or len(md.split()) < _MIN_WORDS:
                        continue

                    score = score_relevance(title, md, topic)
                    articles.append(
                        ScrapedArticle(
                            url=r.url, title=title,
                            content=md.strip(), relevance_score=score,
                        )
                    )
        except Exception as e:
            logger.error("Error scraping %s: %s", url, e)

        articles.sort(key=lambda a: a.relevance_score, reverse=True)
        return articles

    async def scrape_and_rank(
        self,
        urls: list[str],
        topic: str,
        *,
        min_relevance: float = 0.1,
        max_follow: int = 5,
    ) -> list[ScrapedArticle]:
        """Scrape multiple seed URLs in parallel and merge results by relevance."""
        import asyncio

        tasks = [self.scrape_url(u, topic, max_follow=max_follow) for u in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles: list[ScrapedArticle] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.error("Scrape task failed: %s", result)
                continue
            articles.extend(a for a in result if a.relevance_score >= min_relevance)

        articles.sort(key=lambda a: a.relevance_score, reverse=True)
        logger.info(
            "Scraped %d articles from %d seed URLs (min_relevance=%s)",
            len(articles), len(urls), min_relevance,
        )
        return articles
