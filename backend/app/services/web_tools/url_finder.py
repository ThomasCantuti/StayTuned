"""URL discovery service using crawl4ai to find relevant news URLs for a topic.

Given a topic string, this module searches Google News and Google Web,
extracts result URLs, and returns the top-N unique main-domain URLs whose
content is most likely to provide insightful news — even when page titles
use different wording.
"""

import asyncio
from crawl4ai.types import CrawlResult
from typing import cast
import logging
import re
from urllib.parse import urlparse, quote_plus

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

logger = logging.getLogger(__name__)

# Domains to always exclude (search engines, social media, video, etc.)
_EXCLUDED_DOMAINS = frozenset({
    "google.com", "www.google.com", "google.it", "www.google.it",
    "gstatic.com", "googleapis.com",
    "accounts.google.com", "support.google.com",
    "maps.google.com", "translate.google.com",
    "webcache.googleusercontent.com", "news.google.com",
    "youtube.com", "www.youtube.com",
    "facebook.com", "www.facebook.com",
    "twitter.com", "x.com", "www.x.com",
    "instagram.com", "www.instagram.com",
    "linkedin.com", "www.linkedin.com",
    "pinterest.com", "www.pinterest.com",
    "reddit.com", "www.reddit.com",
    "tiktok.com", "www.tiktok.com",
    "schema.org",
})

# Pattern to match real http(s) URLs in markdown link syntax [text](url)
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)]+)\)")

# Pattern to unwrap Google redirect URLs (/url?q=<actual_url>&...)
_GOOGLE_REDIRECT_RE = re.compile(
    r"https?://(?:www\.)?google\.\w+/url\?.*?q=(https?://[^&]+)"
)


def _extract_main_domain(url: str) -> str | None:
    """Return the main domain URL (scheme + netloc) or None if invalid."""
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return None


def _is_excluded(domain_url: str) -> bool:
    """Check whether a domain should be filtered out."""
    try:
        host = urlparse(domain_url).netloc.lower().split(":")[0]
        return any(host == ex or host.endswith("." + ex) for ex in _EXCLUDED_DOMAINS)
    except Exception:
        return True


class URLFinder:
    """Discovers the most relevant news-source URLs for a given topic.

    Uses crawl4ai to query Google News and Google Web search with a single
    browser session, combines results, deduplicates by main domain, and
    returns up to *n* unique domain URLs likely to contain insightful content.

    Google News is searched first (news-specific results), then regular
    Google is used as a supplement to broaden coverage.
    """

    def __init__(self) -> None:
        self._browser_cfg = BrowserConfig(
            headless=True,
            verbose=False,
            text_mode=True,
        )
        self._crawl_cfg = CrawlerRunConfig(
            word_count_threshold=0,
            excluded_tags=["script", "style"],
            remove_overlay_elements=True,
            wait_until="domcontentloaded",
            delay_before_return_html=3.0,
            page_timeout=30000,
        )

    async def find_urls(self, topic: str, n: int = 10) -> list[str]:
        """Return up to *n* unique main-domain URLs relevant to *topic*.

        Args:
            topic: Free-text description of the topic to search for.
            n: Maximum number of domain URLs to return.

        Returns:
            A list of up to *n* strings, each a main-domain URL
            (e.g. ``"https://example.com"``).
        """
        raw_urls = await self._search(topic, n)
        logger.info("Extracted %d raw URLs from search results", len(raw_urls))

        # Deduplicate by main domain, preserving discovery order
        # (Google News results come first, so they get priority)
        seen: set[str] = set()
        domains: list[str] = []

        for url in raw_urls:
            domain = _extract_main_domain(url)
            if domain is None:
                continue
            domain_lower = domain.lower()
            if domain_lower in seen or _is_excluded(domain):
                continue
            seen.add(domain_lower)
            domains.append(domain)
            if len(domains) >= n:
                break

        logger.info(
            "Returning %d domain URLs for topic '%s': %s",
            len(domains), topic, domains,
        )
        return domains

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _search(self, topic: str, n: int) -> list[str]:
        """Run Google News + Google Web searches using a single browser."""
        query = quote_plus(topic)

        # Google News search — surfaces actual news articles
        news_url = (
            f"https://www.google.com/search?q={query}"
            f"&tbm=nws&num={n + 10}&hl=en"
        )
        # Regular Google with news-oriented query as supplement
        web_url = (
            f"https://www.google.com/search?q={query}+news+latest"
            f"&num={n + 5}&hl=en"
        )

        all_urls: list[str] = []

        try:
            async with AsyncWebCrawler(config=self._browser_cfg) as crawler:
                for url in [news_url, web_url]:
                    result = cast(
                        CrawlResult,
                        await crawler.arun(url=url, config=self._crawl_cfg),
                    )
                    if not result.success:
                        logger.warning("Search crawl failed: %s", result.url)
                        continue
                    all_urls.extend(self._extract_urls(result))
        except Exception as e:
            logger.error("Error during Google search: %s", e)

        return all_urls

    @staticmethod
    def _extract_urls(result: CrawlResult) -> list[str]:
        """Extract outbound URLs from a crawl result."""
        urls: list[str] = []

        # Extract from markdown
        if result.markdown:
            md = result.markdown.raw_markdown or str(result.markdown)
            for _text, link in _MD_LINK_RE.findall(md):
                redirect = _GOOGLE_REDIRECT_RE.match(link)
                if redirect:
                    link = redirect.group(1)
                urls.append(link)

        # Extract from HTML links if available
        if hasattr(result, "links") and result.links:
            for link_info in result.links.get("external", []):
                href = (
                    link_info.get("href", "")
                    if isinstance(link_info, dict)
                    else str(link_info)
                )
                if href.startswith("http"):
                    redirect = _GOOGLE_REDIRECT_RE.match(href)
                    if redirect:
                        href = redirect.group(1)
                    urls.append(href)

        return urls


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        finder = URLFinder()
        topic = input("Enter topic: ")
        urls = await finder.find_urls(topic, n=10)
        print(f"\nFound {len(urls)} URLs for topic '{topic}':")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")

    asyncio.run(main())
