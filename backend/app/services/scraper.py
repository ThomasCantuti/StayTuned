import logging

logger = logging.getLogger(__name__)

class ScraperService:
    def extract_text_from_html(self, url: str) -> str:
        """Extracts and returns the main text content from a given URL."""
        import trafilatura
        
        page_content = trafilatura.fetch_url(url)
        text = trafilatura.extract(page_content, include_comments=False, include_tables=True)
        return text or ""
    
    def extract_article_links(self, url: str, max_links: int = 5) -> list[str]:
        """Extracts article links from a news site homepage."""
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        base_domain = urlparse(url).netloc
        article_links = []
        
        # Search for links in typical article elements
        selectors = [
            'article a[href]',
            'h2 a[href]', 'h3 a[href]',
            '.post a[href]', '.entry a[href]',
            '[class*="article"] a[href]',
            '[class*="story"] a[href]',
            '[class*="card"] a[href]',
        ]
        
        seen = set()
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if not href:
                    continue
                
                # Build absolute URL
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)
                
                # Filter: same domain, long enough path (indicates article)
                if (parsed.netloc == base_domain and 
                    len(parsed.path) > 10 and 
                    full_url not in seen and
                    not any(x in full_url for x in ['#', 'login', 'signup', 'subscribe', 'tag/', 'category/', 'author/'])):
                    seen.add(full_url)
                    article_links.append(full_url)
                    
                if len(article_links) >= max_links:
                    break
            if len(article_links) >= max_links:
                break
        
        return article_links


    def scrape_news_site(self, site_url: str, max_articles: int = 3) -> list[dict]:
        """Downloads the homepage, extracts article links and reads their content."""
        import time
        
        logger.info(f"Analyzing: {site_url}")
        
        article_links = self.extract_article_links(site_url, max_links=max_articles)
        logger.info(f"Found {len(article_links)} articles")
        
        articles = []
        for link in article_links:
            logger.info(f"Downloading: {link[:60]}...")
            try:
                content = self.extract_text_from_html(link)
                if content and len(content) > 100:
                    articles.append({
                        'url': link,
                        'content': content
                    })
            except Exception as e:
                logger.warning(f"Error: {e}")
            time.sleep(1)  # Rate limiting
        
        return articles