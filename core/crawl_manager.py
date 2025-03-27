"""Crawl Manager for One_Touch_Plus.

This module manages per-domain crawl queues using a priority heap (via heapq)
to schedule URLs based on a scoring function. It also tracks visited URLs to prevent duplicates.
"""

import heapq
from urllib.parse import urlparse
from collections import defaultdict
import logging
from ml.scoring_engine import predict_url_score

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

    def score_url(self, url: str, config: dict) -> float:
        """
        Compute a priority score for a URL using the ML scoring engine.

        Args:
            url (str): The URL to score.
            config (dict): Configuration dict (reserved for future use).

        Returns:
            float: The predicted score.
        """
        return predict_url_score(url)

    def add_url(self, url: str, depth: int, config: dict = None):
        """
        Add a URL to the crawl queue for its domain if not visited and within depth limits.

        Args:
            url (str): The URL to enqueue.
            depth (int): Current crawl depth.
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
        Retrieve the next URL from the per-domain queues by rotating through domains.

        Returns:
            tuple: (url, depth) if available; otherwise, None.
        """
        for domain in list(self.queues):
            if self.queues[domain]:
                _, url, depth = heapq.heappop(self.queues[domain])
                return url, depth
        return None
