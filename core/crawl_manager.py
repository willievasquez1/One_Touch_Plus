"""Crawl Manager for One_Touch_Plus.

This module manages per-domain crawl queues using a priority heap (via heapq)
to schedule URLs based on a scoring function. It also tracks visited URLs to
prevent duplicates.
"""

import heapq
from urllib.parse import urlparse
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class CrawlManager:
    def __init__(self, max_depth=3):
        """
        Initialize the CrawlManager with per-domain queues and a visited set.

        Args:
            max_depth (int): The maximum crawl depth.
        """
        self.queues = defaultdict(list)  # domain → priority heap [(score, url, depth)]
        self.visited = set()
        self.max_depth = max_depth

    def score_url(self, url: str, config: dict) -> int:
        """
        Compute a priority score for a URL based on its path.
        
        Lower scores indicate higher priority.

        Args:
            url (str): The URL to score.
            config (dict): Configuration dict with optional priority rules.

        Returns:
            int: The computed score.
        """
        score = 100  # Default base score
        path = urlparse(url).path.lower()

        # Boost: lower score if boost keywords are present.
        for boost in config.get("priority", {}).get("boost_keywords", []):
            if boost in path:
                score -= 20

        # Penalty: increase score if penalty keywords are present.
        for penalty in config.get("priority", {}).get("penalty_keywords", []):
            if penalty in path:
                score += 20

        return score

    def add_url(self, url: str, depth: int, config: dict = None):
        """
        Add a URL to the crawl queue for its domain if not already visited and within depth limits.

        Args:
            url (str): The URL to enqueue.
            depth (int): The current crawl depth.
            config (dict, optional): Configuration dict for priority scoring.
        """
        if url in self.visited or depth > self.max_depth:
            logger.debug(f"Skipping duplicate or out-of-depth URL: {url}")
            return
        domain = urlparse(url).netloc
        score = self.score_url(url, config or {})
        heapq.heappush(self.queues[domain], (score, url, depth))
        self.visited.add(url)
        logger.debug(f"Enqueued URL: {url} at depth {depth} under domain {domain} with score {score}")

    def get_next_url(self):
        """
        Retrieve the next URL from the per-domain queues by iterating through all domains.

        Returns:
            tuple: (url, depth) if available; otherwise, None.
        """
        for domain in list(self.queues):
            if self.queues[domain]:
                _, url, depth = heapq.heappop(self.queues[domain])
                return url, depth
        return None
