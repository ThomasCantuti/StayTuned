from strands import Agent

from app.routers.schemas import URLSearchResponse
from .schemas import ScraperResponse
from .web_tools import get_topic_news_urls, browse_page, read_article, search_links, evaluate_content
from app.clients.clients import get_model
from .prompts import URL_FINDER_AGENT_PROMPT, SCRAPER_AGENT_PROMPT
from .hooks import MaxToolCallsHook

url_finder_agent = Agent(
    name="url_finder_agent",
    description="Agent for finding URLs",
    model=get_model(),
    tools=[get_topic_news_urls],
    structured_output_model=URLSearchResponse,
    system_prompt=URL_FINDER_AGENT_PROMPT,
)

# Hook to prevent the agent from looping forever with smaller models.
# Max 6 tool calls: enough for explore → read → evaluate → retry once → read → evaluate
scraper_tool_limit = MaxToolCallsHook(max_calls=6)

scraper_agent = Agent(
    name="scraper_agent",
    description="Agent for navigating and scraping URLs with iterative exploration",
    model=get_model(),
    structured_output_model=ScraperResponse,
    tools=[browse_page, read_article, search_links, evaluate_content],
    system_prompt=SCRAPER_AGENT_PROMPT,
    hooks=[scraper_tool_limit],
)