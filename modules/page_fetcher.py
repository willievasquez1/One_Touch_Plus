"""Page fetching logic for One_Touch_Plus.

This module asynchronously fetches HTML content using aiohttp,
parses the title and snippet using BeautifulSoup,
and includes retry logic for resilience.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from utils.retry_handler import with_retries  # Retry decorator for resilience

logger = logging.getLogger(__name__)

@with_retries(max_retries=3, delay=1, backoff=2)
async def fetch_page(url: str, config: dict) -> dict:
    """
    Fetch a web page and extract its title, snippet, and raw HTML.

    Args:
        url (str): The URL to fetch.
        config (dict): Scraper configuration (may include headers, timeout, etc.).

    Returns:
        dict: Contains 'url', 'title', 'snippet', and 'html'.
    """
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        headers = config.get("headers", {})  # Optional headers from config

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"[fetch_page] Non-200 response for {url}: {response.status}")
                    return {}

                html = await response.text()
                soup = BeautifulSoup(html, "lxml")
                title = soup.title.string.strip() if soup.title else "Untitled"
                snippet = soup.get_text()[:300]  # First 300 characters as preview

                logger.info(f"[fetch_page] Fetched {url} successfully with title: '{title}'")
                return {
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "html": html
                }

    except Exception as e:
        logger.error(f"[fetch_page] Error fetching {url}: {e}")
        return {}
