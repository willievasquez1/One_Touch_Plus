"""Error handling utilities, such as retry decorators for robust scraping."""

import asyncio
import functools

def async_retry(retries=3, delay=1):
    """Decorator to retry an async function if it raises an exception.

    Args:
        retries (int): Number of retry attempts before giving up.
        delay (int): Delay in seconds between retries.

    Returns:
        function: A wrapper function that encapsulates the retry logic around the original coroutine.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    # TODO: Add logging of the exception if logger is available.
                    await asyncio.sleep(delay)
            # If we exit loop without returning, all retries failed
            # Optionally, re-raise the last exception
            # For now, just return or raise the last exception after exhausting retries.
            if last_exception:
                raise last_exception
        return wrapper
    return decorator
