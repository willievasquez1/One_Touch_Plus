"""Robots.txt compliance utility for One_Touch_Plus.

This module provides a basic function to check whether a URL is allowed
to be crawled based on the site's robots.txt file. This is a stub and should be
extended for production use.
"""

import logging
import aiohttp
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)

async def is_allowed_by_robots(url: str, user_agent: str = "*") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(robots_url) as response:
                if response.status != 200:
                    logger.warning(f"robots.txt not accessible for {url} (HTTP {response.status}).")
                    return True  # Fail open
                robots_text = await response.text()
                rp = RobotFileParser()
                rp.parse(robots_text.splitlines())
                allowed = rp.can_fetch(user_agent, url)
                logger.info(f"Robots.txt compliance for {url}: {allowed}")
                return allowed
    except Exception as e:
        logger.error(f"Error checking robots.txt for {url}: {e}")
        return True  # Fail open

# For quick testing:
if __name__ == "__main__":
    import asyncio
    test_url = "https://www.python.org"
    result = asyncio.run(is_allowed_by_robots(test_url))
    print(f"Allowed: {result}")
