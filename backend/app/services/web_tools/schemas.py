from pydantic import BaseModel

class ScrapedArticle(BaseModel):
    url: str
    title: str
    content: str
    relevance_score: float = 0.0