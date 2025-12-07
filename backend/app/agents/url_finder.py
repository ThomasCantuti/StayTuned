from app.services.llm import LLMService
from datapizza.agents import Agent
from datapizza.tools.web_fetch import WebFetchTool
import re
import os
from dotenv import load_dotenv
load_dotenv()

tool_model = os.getenv("TOOL_MODEL")
base_url_runtime = os.getenv("BASE_URL_RUNTIME")
llm_service = LLMService()

class URLFinderAgent:
    """Agent to find URLs related to a specific topic using a web fetch tool."""

    def __init__(self):
        self.local_client = llm_service.get_client(tool_model, base_url_runtime)
        
    def get_agent(self) -> Agent:
        """Creates and returns the URL finding agent."""
        return Agent(
            name="Find URLs Assistant",
            client=self.local_client,
            system_prompt="""You are a helpful research assistant.
                Your goal is to provide the 10 best URLs of the 10 best sources which give the best and updated news on the user's topic.

                Follow these steps:
                1.  Receive a user request where you understand the topic they are interested in.
                2.  Use the `WebFetchTool` tool to find the URLs of the best sources on the topic.
                3.  Write the 10 best URLs in a numbered list format as your final answer.
                """,
            tools=[WebFetchTool()]
        )
    
    def agent_response_to_string(self, response: list[str]) -> str:
        """Converts the agent's response to a string format."""
        return re.findall(r'https?://[^\s]+', response)