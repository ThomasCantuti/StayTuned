from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
