"""Retry Queue for One_Touch_Plus.

This module implements a simple retry mechanism. Failed URLs are added to a retry queue,
with each retry attempt delayed by an exponential backoff.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

class RetryQueue:
    def __init__(self, max_retries=3, backoff=2):
        """
        Initialize the RetryQueue.

        Args:
            max_retries (int): Maximum number of retry attempts.
            backoff (int or float): Exponential backoff multiplier.
        """
        self.queue = []
        self.max_retries = max_retries
        self.backoff = backoff

    def add(self, url, depth, attempt=1):
        """
        Add a URL to the retry queue if it has not exceeded the maximum retries.

        Args:
            url (str): The URL to retry.
            depth (int): The current crawl depth.
            attempt (int): The current attempt count.
        """
        if attempt <= self.max_retries:
            self.queue.append((url, depth, attempt))
            logger.info(f"[Retry] Re-enqueued {url} (attempt {attempt})")

    async def next(self):
        """
        Retrieve the next URL from the retry queue after waiting for exponential backoff.

        Returns:
            tuple: (url, depth, attempt) or None if the queue is empty.
        """
        if not self.queue:
            return None
        url, depth, attempt = self.queue.pop(0)
        await asyncio.sleep(self.backoff ** (attempt - 1))
        return url, depth, attempt
