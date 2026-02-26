"""Scraping service using crawl4ai for high-quality content extraction."""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from strands import Agent

from app.clients.clients import get_model

logger = logging.getLogger(__name__)

# Link text patterns that indicate navigation/non-article links
_SKIP_PATTERNS = re.compile(
    r"^(home|about|contact|privacy|terms|sign.?in|log.?in|subscribe|menu|"
    r"cookie|newsletter|careers|faq|help|search|skip|more|load more)$",
    re.IGNORECASE,
)

# Minimum word count to consider a page as having real article content
_ARTICLE_MIN_WORDS = 200

# Max chars of raw markdown to send to the LLM for cleaning
_LLM_CONTENT_LIMIT = 6000

_CLEAN_SYSTEM_PROMPT = """\
You are a content extractor. You receive raw markdown scraped from a web page.
Your job is to return ONLY the actual article body — the main text content that \
a reader came to the page to read.

REMOVE completely:
- Navigation menus, breadcrumbs, header/footer links
- Cookie notices, consent banners, privacy popups
- Sidebar content, ads, promotional blocks
- "Related articles", "Read more", "Share this" sections
- Image markdown, captions, alt-text blocks
- Author bios, social media links
- Any content that is not part of the main article

KEEP:
- The article title (as a heading)
- The full article body text
- Key quotes and data mentioned in the article

Return clean, readable plain text. No markdown formatting. \
Do not add commentary or summaries — return the actual article text as-is, just cleaned."""


def _build_cleaner_agent() -> Agent:
    """Build a strands Agent for content cleaning using the shared LLM client."""
    return Agent(
        name="content_cleaner",
        description="Cleans raw scraped markdown into plain article text",
        model=get_model(),
        system_prompt=_CLEAN_SYSTEM_PROMPT,
        tools=[],
    )


def _llm_clean(raw_markdown: str, topic: str) -> str:
    """Send raw markdown to the LLM via strands Agent and get back clean article text."""
    truncated = raw_markdown[:_LLM_CONTENT_LIMIT]
    user_message = (
        f"Topic: {topic}\n\n"
        f"--- RAW PAGE CONTENT ---\n{truncated}\n--- END ---\n\n"
        "Extract and return only the clean article text."
    )

    try:
        agent = _build_cleaner_agent()
        result = agent(user_message)
        content = str(result).strip()

        # Some models wrap output in <think> tags — strip those
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        if len(content) > 50:
            return content

        logger.warning("LLM returned too-short cleaned content, using raw")
        return raw_markdown

    except Exception as e:
        logger.error(f"LLM cleaning failed: {e}")
        return raw_markdown


def _root_domain(netloc: str) -> str:
    """Strip 'www.' and port to get a comparable root domain."""
    host = netloc.split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host


@dataclass
class ScrapedArticle:
    url: str
    title: str
    markdown: str
    relevance_score: float = 0.0


@dataclass
class _CrawlResult:
    """Raw result from a single page crawl."""
    url: str
    title: str
    markdown: str
    internal_links: list[dict] = field(default_factory=list)
    word_count: int = 0


class CrawlScraper:
    """Scrapes URLs using crawl4ai and ranks content by topic relevance."""

    def __init__(self) -> None:
        self._browser_cfg = BrowserConfig(headless=True, verbose=False)
        self._crawler_cfg = CrawlerRunConfig(
            word_count_threshold=50,
            excluded_tags=["nav", "header", "footer", "aside", "script", "style"],
            scan_full_page=True,
            wait_until="domcontentloaded",
            delay_before_return_html=2.0,
            page_timeout=45000,
        )

    # ------------------------------------------------------------------
    # Low-level crawling
    # ------------------------------------------------------------------

    async def _crawl_single(
        self, url: str, crawler: AsyncWebCrawler
    ) -> _CrawlResult | None:
        """Crawl one page and return raw result with links."""
        try:
            result = await crawler.arun(url=url, config=self._crawler_cfg)

            if not result.success:
                logger.warning("Failed to crawl %s: %s", url, result.error_message)
                return None

            title = (result.metadata or {}).get("title", "")

            md_obj = result.markdown
            if md_obj is None:
                return None

            markdown = md_obj.raw_markdown or str(md_obj)
            if not markdown.strip():
                return None

            internal_links = (
                result.links.get("internal", [])
                if isinstance(result.links, dict)
                else []
            )

            return _CrawlResult(
                url=url,
                title=title,
                markdown=markdown.strip(),
                internal_links=internal_links,
                word_count=len(markdown.split()),
            )

        except Exception as e:
            logger.error("Error crawling %s: %s", url, e)
            return None

    # ------------------------------------------------------------------
    # Link selection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_article_links(
        links: list[dict],
        topic: str,
        base_domain: str,
        max_links: int = 5,
    ) -> list[str]:
        """From internal links, pick the ones most likely to be articles about the topic."""
        topic_keywords = [w.lower() for w in re.split(r"\W+", topic) if len(w) > 2]
        candidates: list[tuple[float, str]] = []

        for link in links:
            href = link.get("href", "")
            text = (link.get("text") or "").strip()

            if not href or not text or len(text) < 10:
                continue
            if _SKIP_PATTERNS.match(text):
                continue

            parsed = urlparse(href)
            if _root_domain(parsed.netloc or "") != _root_domain(base_domain):
                continue

            text_lower = text.lower()
            hits = sum(1 for kw in topic_keywords if kw in text_lower)
            score = hits / len(topic_keywords) if topic_keywords else 0.0

            path = parsed.path.lower()
            if any(seg in path for seg in ("/index/", "/blog/", "/article", "/post/", "/news/")):
                score += 0.1

            candidates.append((score, href))

        candidates.sort(key=lambda x: x[0], reverse=True)

        seen: set[str] = set()
        result: list[str] = []
        for _, href in candidates:
            if href not in seen:
                seen.add(href)
                result.append(href)
            if len(result) >= max_links:
                break
        return result

    @staticmethod
    def _is_index_page(crawl_result: _CrawlResult) -> bool:
        """Detect if a page is an index/listing rather than an article."""
        links_count = len(crawl_result.internal_links)
        wc = crawl_result.word_count

        if wc < _ARTICLE_MIN_WORDS and links_count > 3:
            return True
        if wc > 0 and (links_count / wc) > 0.02 and wc < 800:
            return True
        return False

    # ------------------------------------------------------------------
    # Relevance scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _score_relevance(article: ScrapedArticle, topic: str) -> float:
        """Score how relevant an article is to the given topic (0.0 – 1.0)."""
        keywords = [w for w in re.split(r"\W+", topic.lower()) if len(w) > 2]
        if not keywords:
            return 0.5

        title_lower = article.title.lower()
        content_lower = article.markdown[:2000].lower()

        title_hits = sum(1 for kw in keywords if kw in title_lower)
        content_hits = sum(1 for kw in keywords if kw in content_lower)

        title_score = title_hits / len(keywords)
        content_score = content_hits / len(keywords)
        combined = (title_score * 0.4) + (content_score * 0.6)

        length = len(article.markdown)
        if length > 3000:
            combined = min(1.0, combined + 0.1)
        elif length < 500:
            combined = max(0.0, combined - 0.1)

        return round(min(1.0, combined), 3)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scrape_url(
        self, url: str, topic: str, *, max_follow: int = 3
    ) -> list[ScrapedArticle]:
        """
        Scrape a URL. If it's an index/listing page, follow the best
        article links and scrape those too.
        """
        articles: list[ScrapedArticle] = []
        base_domain = urlparse(url).netloc

        try:
            async with AsyncWebCrawler(config=self._browser_cfg) as crawler:
                seed = await self._crawl_single(url, crawler)
                if seed is None:
                    return articles

                if self._is_index_page(seed):
                    logger.info(
                        "Index page detected (%d words, %d links): %s",
                        seed.word_count, len(seed.internal_links), url,
                    )
                    follow_urls = self._pick_article_links(
                        seed.internal_links, topic, base_domain, max_links=max_follow,
                    )
                    logger.info("Following %d article links from %s", len(follow_urls), url)

                    tasks = [self._crawl_single(u, crawler) for u in follow_urls]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for r in results:
                        if isinstance(r, (Exception, type(None))):
                            continue
                        if r.word_count >= _ARTICLE_MIN_WORDS:
                            articles.append(
                                ScrapedArticle(url=r.url, title=r.title, markdown=r.markdown)
                            )
                else:
                    if seed.word_count >= _ARTICLE_MIN_WORDS // 2:
                        articles.append(
                            ScrapedArticle(url=seed.url, title=seed.title, markdown=seed.markdown)
                        )

        except Exception as e:
            logger.error("Error in scrape_url for %s: %s", url, e)

        return articles

    async def _clean_with_llm(self, article: ScrapedArticle, topic: str) -> ScrapedArticle:
        """Clean a single article's content via the LLM (runs blocking call in executor)."""
        loop = asyncio.get_event_loop()
        cleaned = await loop.run_in_executor(None, _llm_clean, article.markdown, topic)
        article.markdown = cleaned
        return article

    async def scrape_and_rank(
        self,
        urls: list[str],
        topic: str,
        *,
        min_relevance: float = 0.1,
        max_follow: int = 3,
    ) -> list[ScrapedArticle]:
        """Scrape all URLs (following article links from index pages), rank by relevance."""
        tasks = [self.scrape_url(url, topic, max_follow=max_follow) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles: list[ScrapedArticle] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Scrape task exception: %s", result)
                continue
            for article in result:
                article.relevance_score = self._score_relevance(article, topic)
                if article.relevance_score >= min_relevance:
                    articles.append(article)

        articles.sort(key=lambda a: a.relevance_score, reverse=True)

        if articles:
            logger.info("Cleaning %d articles with LLM...", len(articles))
            clean_tasks = [self._clean_with_llm(a, topic) for a in articles]
            articles = list(await asyncio.gather(*clean_tasks))

        logger.info(
            "Scraped %d articles from %d seed URLs (min_relevance=%s)",
            len(articles), len(urls), min_relevance,
        )
        return articles
