"""Throttle Controller for One_Touch_Plus.

This module implements per-domain rate limiting by tracking the last request timestamp
for each domain and delaying the next request until the configured delay has passed.
"""

import asyncio
import time
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class ThrottleController:
    def __init__(self, config: dict):
        """
        Initialize the ThrottleController with configuration.

        Args:
            config (dict): Scraper configuration. Expects 'crawl.request_delay'.
        """
        self.domain_timestamps = {}
        self.delay = config.get("crawl", {}).get("request_delay", 1)

    async def throttle(self, url: str):
        """
        Throttle requests per domain based on the last request timestamp.

        Args:
            url (str): The URL for which to enforce rate limiting.
        """
        domain = urlparse(url).netloc
        now = time.time()
        last_time = self.domain_timestamps.get(domain, 0)
        elapsed = now - last_time

        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            logger.debug(f"[Throttle] Sleeping {sleep_time:.2f}s for domain: {domain}")
            await asyncio.sleep(sleep_time)

        self.domain_timestamps[domain] = time.time()
