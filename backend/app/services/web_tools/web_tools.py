from strands import tool
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from .schemas import (
    TopicNewsRequest,
    TopicNewsResponse,
    ScraperRequest,
    ScraperResponse,
    BrowsePageRequest,
    BrowsePageResponse,
    ReadArticleRequest,
    ReadArticleResponse,
    SearchLinksRequest,
    SearchLinksResponse,
    EvaluateContentRequest,
    EvaluateContentResponse,
)


def _extract_rss_links(xml_bytes: bytes, max_items: int) -> list[str]:
    root = ET.fromstring(xml_bytes)
    links: list[str] = []
    seen: set[str] = set()

    # Typical RSS shape: rss/channel/item/link
    for item in root.findall(".//item"):
        link_el = item.find("link")
        if link_el is None:
            continue
        link = (link_el.text or "").strip()
        if not link or link in seen:
            continue
        seen.add(link)
        links.append(link)
        if len(links) >= max_items:
            break

    return links


@tool
def get_topic_news_urls(request: TopicNewsRequest) -> TopicNewsResponse:
    """Return top N news URLs for a topic.

    Source: Google News RSS search endpoint.
    """
    if not request.topic or not isinstance(request.topic, str):
        return TopicNewsResponse(
            topic="",
            requested_count=request.num_urls,
            urls=[]
        )

    topic = request.topic.strip()
    if not topic:
        return TopicNewsResponse(
            topic="",
            requested_count=request.num_urls,
            urls=[]
        )

    try:
        import requests  # type: ignore
    except Exception:
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )

    query = quote_plus(topic)
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TopicNewsTool/1.0; +https://example.com/bot)"
    }

    try:
        response = requests.get(
            rss_url, headers=headers, timeout=request.timeout_seconds
        )
    except requests.Timeout:
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )
    except requests.RequestException as exc:
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )

    status_code = response.status_code
    content_type = response.headers.get("Content-Type", "")

    if status_code >= 400:
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )

    body = response.content or b""
    if not body.strip():
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )

    try:
        urls = _extract_rss_links(body, request.num_urls)
    except ET.ParseError:
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )
    except Exception as exc:
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )

    if not urls:
        return TopicNewsResponse(
            topic=topic,
            requested_count=request.num_urls,
            urls=[]
        )

    return TopicNewsResponse(
        topic=topic,
        requested_count=request.num_urls,
        urls=urls,
    )


@tool
def browse_page(request: BrowsePageRequest) -> BrowsePageResponse:
    """
    Acts like opening a page in a browser. 
    It returns the page title, the first few paragraphs to understand the context, 
    and a list of the visible links present on the page (formatted as 'Text: URL').
    Use this to explore a homepage or a blog root page.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(request.url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.get_text(strip=True) if soup.title else "No Title Found"
        
        # Get brief summary (first few valid paragraphs)
        paragraphs = soup.find_all('p')
        summary_lines = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 40:
                summary_lines.append(text)
            if len(summary_lines) >= 3:
                break
        summary = " ".join(summary_lines) if summary_lines else "No meaningful text overview found on this page."
        
        # Extract links
        links = []
        seen_hrefs = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if isinstance(href, list):
                href = href[0] if href else ""
            else:
                href = str(href)
                
            absolute_url = urljoin(request.url, href)
            link_text = a_tag.get_text(strip=True)
            
            # Avoid empty texts and duplicate links
            if link_text and len(link_text) > 2 and absolute_url not in seen_hrefs:
                links.append(f"{link_text}: {absolute_url}")
                seen_hrefs.add(absolute_url)
                
            if len(links) >= 100:  
                break
                
        return BrowsePageResponse(
            url=request.url,
            title=title,
            summary=summary,
            links=links
        )
        
    except requests.exceptions.RequestException as e:
        return BrowsePageResponse(
            url=request.url,
            title="Error",
            summary=f"Network error: {str(e)}",
            links=[]
        )
    except Exception as e:
        return BrowsePageResponse(url=request.url, title="Error", summary=f"Unexpected error: {str(e)}", links=[])


@tool
def read_article(request: ReadArticleRequest) -> ReadArticleResponse:
    """
    Acts like reading a specific news article. 
    It removes noisy elements like navigation and footers, extracting purely the title and text of the article.
    Use this when you have found a specific article link you want to read in full.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(request.url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.get_text(strip=True) if soup.title else "No Title Found"
        
        # Clean up the HTML by removing noisy elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
            
        paragraphs = soup.find_all('p')
        article_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        if not article_text:
            article_text = soup.get_text(separator='\n', strip=True)
            
        return ReadArticleResponse(
            url=request.url,
            title=title,
            content=article_text
        )
        
    except requests.exceptions.RequestException as e:
        return ReadArticleResponse(
            url=request.url,
            title="Error",
            content=f"Network error: {str(e)}"
        )
    except Exception as e:
        return ReadArticleResponse(
            url=request.url,
            title="Error",
            content=f"Unexpected error: {str(e)}"
        )

@tool
def search_links(request: SearchLinksRequest) -> SearchLinksResponse:
    """
    Acts like Ctrl+F on the links of a webpage. 
    It searches all links on the given URL for text or URLs matching the query.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(request.url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        matching_links = []
        seen_hrefs = set()
        query = request.query.lower()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if isinstance(href, list):
                href = href[0] if href else ""
            else:
                href = str(href)
                
            absolute_url = urljoin(request.url, href)
            link_text = a_tag.get_text(strip=True)
            
            if (query in link_text.lower() or query in absolute_url.lower()) and absolute_url not in seen_hrefs:
                matching_links.append(f"{link_text}: {absolute_url}")
                seen_hrefs.add(absolute_url)
                
            if len(matching_links) >= 50:
                break
                
        return SearchLinksResponse(
            url=request.url,
            matching_links=matching_links
        )
        
    except requests.exceptions.RequestException as e:
        return SearchLinksResponse(
            url=request.url,
            matching_links=[f"Network error: {str(e)}"]
        )
    except Exception as e:
        return SearchLinksResponse(
            url=request.url,
            matching_links=[f"Unexpected error: {str(e)}"]
        )


@tool
def evaluate_content(request: EvaluateContentRequest) -> EvaluateContentResponse:
    """
    Self-evaluation tool: Assess whether extracted article content is relevant to the topic.
    Use this AFTER reading an article to decide if you should keep it or try another link.
    This helps you make smarter decisions about which articles to include in your final response.
    """
    topic_lower = request.topic.lower()
    content_lower = request.content_snippet.lower()
    title_lower = request.article_title.lower()

    # Split the topic into keywords
    topic_keywords = [w for w in topic_lower.split() if len(w) > 2]

    # Count keyword matches in title and content
    title_matches = sum(1 for kw in topic_keywords if kw in title_lower)
    content_matches = sum(1 for kw in topic_keywords if kw in content_lower)
    total_keywords = len(topic_keywords) if topic_keywords else 1

    title_score = title_matches / total_keywords
    content_score = content_matches / total_keywords

    # Heuristic: content is too short or looks like an error page
    is_error_page = any(
        marker in content_lower
        for marker in ["404", "page not found", "access denied", "subscribe to continue", "cookie policy"]
    )

    is_relevant = (title_score > 0.3 or content_score > 0.3) and not is_error_page
    should_try_another = not is_relevant or len(request.content_snippet.strip()) < 100

    if is_error_page:
        reason = "Content appears to be an error page, paywall, or cookie notice — not a real article."
    elif title_score > 0.3 and content_score > 0.3:
        reason = f"Strong match: topic keywords found in both title and content."
    elif title_score > 0.3:
        reason = f"Moderate match: topic keywords found in title but limited in content body."
    elif content_score > 0.3:
        reason = f"Moderate match: topic keywords found in content but not in title."
    else:
        reason = f"Weak match: few topic keywords found. Consider trying a different article."

    return EvaluateContentResponse(
        is_relevant=is_relevant,
        relevance_reason=reason,
        should_try_another=should_try_another,
    )
