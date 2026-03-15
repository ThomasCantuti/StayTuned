"""
Test script for the URL finder agent.

Usage: python3 tests/test_find_urls.py --topic <topic> --max_sources <max_sources>
"""

import logging
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.routers.schemas import URLSearchResponse
from app.services.agents.agents import url_finder_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(topic: str, max_sources: int):
    logger.info("Test: Searching URLs for topic: %s", topic)
    response = url_finder_agent(prompt=f"Topic: {topic}, Number of URLs: {max_sources}")
    if not isinstance(response.structured_output, URLSearchResponse):
        raise ValueError("Agent failed to return valid URL structure.")
    logger.info("Test: Found %d URLs for topic '%s'", len(response.structured_output.urls), topic)
    logger.info("Test: URLs: %s", response.structured_output.urls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for URLs based on a topic.")
    parser.add_argument("--topic", required=True, type=str, help="The topic to search for URLs.")
    parser.add_argument("--max_sources", required=False, type=int, default=10, help="The maximum number of URLs to return.")

    args = parser.parse_args()
    run(args.topic, args.max_sources)
