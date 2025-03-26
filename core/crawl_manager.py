"""Manages the crawling queue and visited URLs for recursive scraping.

The CrawlManager handles URL queueing, depth limiting, and can be extended to persist 
crawling state (for pause/resume functionality). It helps orchestrate which URLs 
to scrape next and ensures each URL is processed at most once.
"""

from collections import deque

class CrawlManager:
    """A manager for crawling URLs with support for depth control and optional persistence."""
    def __init__(self, max_depth: int = None):
        """Initialize the CrawlManager with an empty queue and seen set.

        Args:
            max_depth (int, optional): Maximum depth for recursive crawling. 
                                       URLs beyond this depth will be ignored.
        """
        self.queue = deque()     # Queue to store (url, depth)
        self.seen = set()        # Set to store visited URLs
        self.max_depth = max_depth if max_depth is not None else float('inf')
        # TODO: Optionally initialize a persistence layer (e.g., a database) to save crawl state.
    
    def add_url(self, url: str, depth: int = 0):
        """Add a new URL to the queue if not seen and within depth limit.

        Args:
            url (str): The URL to crawl.
            depth (int): The depth level of this URL (0 for initial URLs).
        """
        if url in self.seen:
            return
        if depth > self.max_depth:
            return
        self.queue.append((url, depth))
        self.seen.add(url)
        # TODO: If using persistence, save the new URL and depth to persistent storage.
    
    def get_next_url(self):
        """Retrieve the next URL and its depth from the queue.

        Returns:
            tuple: (url, depth) for the next URL to crawl, or None if the queue is empty.
        """
        if not self.queue:
            return None
        url, depth = self.queue.popleft()
        return (url, depth)
    
    def __len__(self):
        """Return the number of URLs currently in the queue."""
        return len(self.queue)
    
    # Additional methods (optional):
    # def save_state(self): ...
    # def load_state(self): ...
    # TODO: Implement persistence methods to allow saving and restoring the crawl state.
