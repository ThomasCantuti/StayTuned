from strands import Agent

from app.routers.schemas import URLSearchResponse
from app.clients.clients import get_model
from .prompts import URL_FINDER_AGENT_PROMPT
from .tools.tools import search_web

url_finder_agent = Agent(
    name="url_finder_agent",
    description="Agent for finding URLs",
    model=get_model(),
    tools=[search_web],
    structured_output_model=URLSearchResponse,
    system_prompt=URL_FINDER_AGENT_PROMPT,
)
