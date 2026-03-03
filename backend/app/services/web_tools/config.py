"""Crawler configuration builder for crawl4ai."""

import re

from crawl4ai import (
    BFSDeepCrawlStrategy,
    BM25ContentFilter,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    KeywordRelevanceScorer,
)

# Minimum words to consider a page as a real article
_MIN_WORDS = 150


def build_crawl_config(topic: str, max_pages: int) -> CrawlerRunConfig:
    """Build a CrawlerRunConfig tuned for topic-relevant deep crawling."""
    keywords = [w for w in re.split(r"\W+", topic.lower()) if len(w) > 2]

    # BM25 filter: produces fit_markdown containing only topic-relevant blocks
    bm25 = BM25ContentFilter(user_query=topic, bm25_threshold=1.0)
    md_gen = DefaultMarkdownGenerator(content_filter=bm25)

    # BFS deep crawl: follow internal links one level deep,
    # prioritising URLs that match topic keywords
    strategy = BFSDeepCrawlStrategy(
        max_depth=1,
        max_pages=max_pages,
        url_scorer=KeywordRelevanceScorer(keywords=keywords, weight=0.7),
        score_threshold=0.0,
    )

    return CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        markdown_generator=md_gen,
        word_count_threshold=50,
        excluded_tags=["nav", "header", "footer", "aside", "script", "style"],
        remove_overlay_elements=True,
        scan_full_page=True,
        wait_until="domcontentloaded",
        delay_before_return_html=2.0,
        page_timeout=45000,
    )
