"""Robots.txt compliance utility for One_Touch_Plus.

This module provides a basic function to check whether a URL is allowed
to be crawled based on the site's robots.txt file. It caches the rules per domain.
"""

import urllib.robotparser
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)
_robots_cache = {}

def is_allowed_by_robots(url: str, user_agent: str = "*") -> bool:
    """
    Check if the given URL is allowed to be crawled based on robots.txt.

    Args:
        url (str): The URL to check.
        user_agent (str): The user agent string to use for the check.

    Returns:
        bool: True if allowed, False otherwise.
    """
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    if domain not in _robots_cache:
        robots_url = f"{domain}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
            _robots_cache[domain] = rp
            logger.info(f"[robots_checker] Fetched robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"[robots_checker] Failed to read robots.txt from {robots_url}: {e}")
            return True  # Fail open on error

    return _robots_cache[domain].can_fetch(user_agent, url)
