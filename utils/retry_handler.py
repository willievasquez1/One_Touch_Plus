"""Retry handler for One_Touch_Plus.

This module provides a decorator, `with_retries`, to wrap asynchronous functions.
It automatically retries the function on exceptions up to a maximum number of attempts,
waiting with exponential backoff between retries.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

def with_retries(max_retries=3, delay=1, backoff=2):
    """
    Decorator to retry an async function upon failure.

    Args:
        max_retries (int): Maximum number of retry attempts.
        delay (int or float): Initial delay in seconds before the first retry.
        backoff (int or float): Multiplier applied to the delay after each attempt.

    Returns:
        function: The decorated function with retry logic.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logger.warning(f"[Retry] {func.__name__} failed (attempt {retries}): {e}")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            logger.error(f"[Retry] {func.__name__} failed after {max_retries} attempts.")
            return None
        return wrapper
    return decorator
