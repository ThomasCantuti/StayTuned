from pydantic import BaseModel

class TopicNewsRequest(BaseModel):
    topic: str
    num_urls: int = 5
    timeout_seconds: int = 15

class TopicNewsResponse(BaseModel):
    topic: str
    requested_count: int
    urls: list[str]

class ScraperRequest(BaseModel):
    topic: str
    url: str
    timeout_seconds: int = 15

class ScraperResponse(BaseModel):
    url: str
    content: str
    title: str = ""
    relevance_score: float = 0.0

class EvaluateContentRequest(BaseModel):
    """Request for the agent to self-evaluate extracted content."""
    topic: str
    article_title: str
    content_snippet: str  # first ~500 chars of content to evaluate

class EvaluateContentResponse(BaseModel):
    """Result of content quality evaluation."""
    is_relevant: bool
    relevance_reason: str
    should_try_another: bool

class BrowsePageRequest(BaseModel):
    url: str

class BrowsePageResponse(BaseModel):
    url: str
    title: str
    summary: str
    links: list[str]

class ReadArticleRequest(BaseModel):
    url: str

class ReadArticleResponse(BaseModel):
    url: str
    title: str
    content: str

class SearchLinksRequest(BaseModel):
    url: str
    query: str

class SearchLinksResponse(BaseModel):
    url: str
    matching_links: list[str]