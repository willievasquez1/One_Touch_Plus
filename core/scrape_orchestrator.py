"""Scraping orchestration logic for One_Touch_Plus.

This module coordinates asynchronous scraping tasks, managing the crawl queue,
concurrent URL fetching, and invoking various handlers (dynamic content, CAPTCHA, etc.).
It applies per-domain rate limiting, uses a retry queue for transient failures,
and routes CAPTCHA handling through a modular interface.
"""

import asyncio
import logging
import os
import sys
import yaml

# Configure logging to print to both stdout and a file.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from core.crawl_manager import CrawlManager
from core.throttle_controller import ThrottleController
from core.retry_queue import RetryQueue
from modules.output_reporter import OutputReporter
from modules.page_fetcher import fetch_page
from modules.link_extractor import extract_links
from modules.robots_checker import is_allowed_by_robots
from handlers import dynamic_content_utils, captcha_handler
from handlers.captcha_strategy import handle_captcha

CONCURRENT_TASKS = 5  # Can be adjusted via config later

async def process_url(
    url: str,
    depth: int,
    config: dict,
    crawl_mgr: CrawlManager,
    semaphore: asyncio.Semaphore,
    reporter: OutputReporter,
    retry_mgr: RetryQueue,
    attempt: int = 1
):
    """
    Process a single URL: applies per-domain throttling, fetches the page,
    expands dynamic content, handles CAPTCHA, reports output, and enqueues new URLs.
    On failure, routes the URL to the retry queue with exponential backoff.
    
    Args:
        url (str): URL to process.
        depth (int): Current crawl depth.
        config (dict): Scraper configuration.
        crawl_mgr (CrawlManager): Crawl manager instance.
        semaphore (asyncio.Semaphore): Concurrency limiter.
        reporter (OutputReporter): Output reporter instance.
        retry_mgr (RetryQueue): Retry manager for failed URLs.
        attempt (int): Current attempt count (default 1).
    """
    # Apply per-domain rate limiting.
    throttler = ThrottleController(config)
    await throttler.throttle(url)
    
    # Optional: Delay per configuration (additional rate limiting)
    await asyncio.sleep(config.get("crawl", {}).get("request_delay", 1))
    
    async with semaphore:
        try:
            # Fetch page content.
            scraped_data = await fetch_page(url, config)
            html = scraped_data.get("html", "")
            
            # Expand dynamic content.
            expanded_html = await dynamic_content_utils.expand_content(html, config)
            
            # Update snippet for reporting (first 300 characters).
            scraped_data["snippet"] = expanded_html[:300]
            
            # Handle CAPTCHA via the modular interface.
            handle_captcha(expanded_html, url, config)
            
            # Report the scraped data.
            reporter.generate_report(scraped_data)
            
            # Extract links from expanded HTML.
            new_links = extract_links(expanded_html, base_url=url, config=config)
            max_depth = config.get("scraper", {}).get("max_depth", 3)
            if depth < max_depth:
                for new_url in new_links:
                    # Check robots.txt compliance before enqueueing.
                    if config.get("crawl", {}).get("use_robots", True):
                        if not is_allowed_by_robots(new_url):
                            logger.info(f"[robots] Skipping disallowed URL: {new_url}")
                            continue
                    crawl_mgr.add_url(new_url, depth=depth + 1)
                    logger.info(f"Added new URL to crawl: {new_url} at depth {depth + 1}")
                    
        except Exception as e:
            logger.error(f"Error processing {url} (attempt {attempt}): {e}")
            retry_mgr.add(url, depth, attempt + 1)

async def start_scraping(config: dict, target):
    """
    Initiate the scraping process for a target URL or list of URLs.
    """
    max_depth = config.get('scraper', {}).get('max_depth', 3)
    crawl_mgr = CrawlManager(max_depth=max_depth)
    retry_mgr = RetryQueue(max_retries=config.get("crawl", {}).get("max_retries", 3))
    
    targets = [target] if isinstance(target, str) else target if isinstance(target, list) else []
    if not targets:
        logger.error("Invalid target(s). Must be string or list of strings.")
        return

    for url in targets:
        crawl_mgr.add_url(url, depth=0)
    logger.info(f"Initial crawl queue: {crawl_mgr.queue}")
    
    reporter = OutputReporter(config)
    semaphore = asyncio.Semaphore(CONCURRENT_TASKS)
    tasks = []

    while True:
        result = crawl_mgr.get_next_url()
        if not result:
            break
        url, depth = result
        logger.info(f"Scheduling URL: {url} at depth {depth}")
        task = asyncio.create_task(process_url(url, depth, config, crawl_mgr, semaphore, reporter, retry_mgr))
        tasks.append(task)

    if tasks:
        await asyncio.gather(*tasks)
    
    # Process any retry queue items.
    while True:
        retry_item = await retry_mgr.next()
        if not retry_item:
            break
        url, depth, attempt = retry_item
        logger.info(f"Retrying URL: {url} at depth {depth}, attempt {attempt}")
        task = asyncio.create_task(process_url(url, depth, config, crawl_mgr, semaphore, reporter, retry_mgr, attempt))
        tasks.append(task)
    if tasks:
        await asyncio.gather(*tasks)
    
    # Finalize batch-mode output.
    reporter.finalize()
    
    logger.info("✅ Scraping process completed.")

if __name__ == "__main__":
    print("Starting One_Touch_Plus scraper...")
    config_path = os.path.join("configs", "async_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    asyncio.run(start_scraping(config, "https://www.python.org"))
