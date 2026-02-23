from pydantic import BaseModel

class URLSearchRequest(BaseModel):
    """Request model for URL search."""
    topic: str
    max_sources: int = 10

class URLSearchResponse(BaseModel):
    """Response model for found URLs."""
    topic: str
    urls: list[str]

class PodcastRequest(BaseModel):
    """Request model for podcast generation."""
    topic: str
    urls: list[str]
    duration: int = 10
    max_articles_per_site: int = 3

class PodcastResponse(BaseModel):
    """Response model for generated podcast."""
    topic: str
    duration: int
    script: str
    sources: list[str]
    audio_path: str