from app.services.llm import LLMService
from pydantic import BaseModel
import ddgs
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
tool_model = os.getenv("TOOL_MODEL")
base_url_runtime = os.getenv("BASE_URL_RUNTIME")
llm_service = LLMService()

class URLResponseModel(BaseModel):
    """Model for URL response."""
    urls: list[str]

class URLFinderService:
    """Service to find URLs related to a specific topic using DuckDuckGo (Free)."""

    def __init__(self):
        self.local_client = llm_service.get_client(tool_model, base_url_runtime)
    
    def _perform_free_search(self, query: str, max_results: int) -> str:
        """
        Executes a free web search using DuckDuckGo.
        Returns a string summary of results.
        """
        try:
            results_list = []
            with ddgs.DDGS() as ddgs_client:
                search_results = ddgs_client.text(query=query, max_results=max_results)
                
                for r in search_results:
                    results_list.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
            
            return "\n---\n".join(results_list)
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return ""

    def urls_search(self, topic: str, max_sources: int = 10) -> URLResponseModel:
        """
        1. Searches the web using DuckDuckGo (Python code, not LLM tool).
        2. Uses LLM to select the best URLs and format them.
        """
        
        logger.info(f"Step 1: Searching DuckDuckGo for '{topic}'...")
        search_query = f"{topic} latest news"
        
        raw_search_results = self._perform_free_search(search_query, max_results=max_sources + 5)
        
        if not raw_search_results:
            raise Exception("Search engine returned no results.")

        logger.info(f"Step 2: Formatting results with LLM...")
        struct_response = self.local_client.structured_response(
            input=f"""
            I have performed a web search about '{topic}'.
            Here are the raw results:
            
            {raw_search_results}
            
            Task:
            1. Select the {max_sources} most relevant and reliable URLs from the list above.
            2. Ignore ads or irrelevant links.
            3. Return the output strictly as a JSON list of URLs.
            """,
            output_cls=URLResponseModel
        )

        if struct_response.structured_data:
            return struct_response.structured_data[0]
        
        raise Exception("Unable to format search results into structured data.")