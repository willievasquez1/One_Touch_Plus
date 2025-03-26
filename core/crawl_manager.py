"""Crawl Manager for One_Touch_Plus.

This module manages the crawling queue and tracks visited URLs to prevent duplicate processing.
"""

import logging

logger = logging.getLogger(__name__)

class CrawlManager:
    def __init__(self, max_depth=3):
        """
        Initialize the CrawlManager with an empty queue and visited set.

        Args:
            max_depth (int): The maximum depth for crawling.
        """
        self.queue = []
        self.visited = set()
        self.max_depth = max_depth

    def add_url(self, url: str, depth: int):
        """
        Add a URL to the crawl queue if it has not been visited yet.

        Args:
            url (str): The URL to enqueue.
            depth (int): The depth level of the URL.
        """
        if url in self.visited:
            logger.debug(f"Skipping duplicate URL: {url}")
            return  # Skip already visited URLs.
        self.queue.append((url, depth))
        self.visited.add(url)
        logger.debug(f"Enqueued URL: {url} at depth {depth}")

    def get_next_url(self):
        """
        Retrieve the next URL from the queue.

        Returns:
            tuple: A tuple of (url, depth) or None if the queue is empty.
        """
        return self.queue.pop(0) if self.queue else None
