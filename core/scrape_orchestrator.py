"""Scraping orchestration logic for One_Touch_Plus.

This module coordinates asynchronous crawling across multiple domains.
It uses per-domain crawl queues (with priority ordering), applies domain-aware throttling,
uses a retry queue with exponential backoff, and routes CAPTCHA handling through a modular interface.
"""

import asyncio
import logging
import os
import yaml

from core.crawl_manager import CrawlManager
from core.throttle_controller import ThrottleController
from core.retry_queue import RetryQueue
from modules.output_reporter import OutputReporter
from modules.page_fetcher import fetch_page
from modules.link_extractor import extract_links
from modules.robots_checker import is_allowed_by_robots
from handlers import dynamic_content_utils, captcha_handler
from handlers.captcha_strategy import handle_captcha
from modules.dashboard import print_dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONCURRENT_TASKS = 5

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
    Process a single URL: apply per-domain throttling, fetch and process content,
    handle CAPTCHA, report output, and enqueue new URLs.
    On failure, route the URL to the retry queue with exponential backoff.

    Args:
        url (str): URL to process.
        depth (int): Current crawl depth.
        config (dict): Scraper configuration.
        crawl_mgr (CrawlManager): Crawl manager instance.
        semaphore (asyncio.Semaphore): Concurrency limiter.
        reporter (OutputReporter): Output reporter instance.
        retry_mgr (RetryQueue): Retry manager instance.
        attempt (int): Current attempt number.
    """
    # Per-domain throttling.
    throttler = ThrottleController(config)
    await throttler.throttle(url)
    await asyncio.sleep(config.get("crawl", {}).get("request_delay", 1))

    async with semaphore:
        try:
            scraped_data = await fetch_page(url, config)
            html = scraped_data.get("html", "")
            expanded_html = await dynamic_content_utils.expand_content(html, config)
            scraped_data["snippet"] = expanded_html[:300]

            handle_captcha(expanded_html, url, config)

            reporter.generate_report(scraped_data)

            new_links = extract_links(expanded_html, base_url=url, config=config)
            max_depth = config.get("scraper", {}).get("max_depth", 3)
            if depth < max_depth:
                for new_url in new_links:
                    if config.get("crawl", {}).get("use_robots", True):
                        if not is_allowed_by_robots(new_url):
                            logger.info(f"[robots] Skipping disallowed URL: {new_url}")
                            continue
                    crawl_mgr.add_url(new_url, depth=depth + 1, config=config)
                    logger.info(f"Added new URL to crawl: {new_url} at depth {depth + 1}")
        except Exception as e:
            logger.error(f"Error processing {url} (attempt {attempt}): {e}")
            retry_mgr.add(url, depth, attempt + 1)

async def start_scraping(config: dict, targets):
    """
    Initiate the crawling process for a list of target URLs.

    Args:
        config (dict): Scraper configuration.
        targets (list or str): Starting URLs.
    """
    max_depth = config.get('scraper', {}).get('max_depth', 3)
    crawl_mgr = CrawlManager(max_depth=max_depth)
    retry_mgr = RetryQueue(max_retries=config.get("crawl", {}).get("max_retries", 3))

    if isinstance(targets, str):
        targets = [targets]
    if not targets:
        logger.error("No valid target URLs provided.")
        return

    for url in targets:
        crawl_mgr.add_url(url, depth=0, config=config)
    logger.info(f"Initial crawl queue: {crawl_mgr.queues}")

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

    reporter.finalize()
    logger.info("✅ Scraping process completed.")

if __name__ == "__main__":
    print("Starting One_Touch_Plus scraper...")
    config_path = os.path.join("configs", "async_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    start_urls = [
        "https://www.python.org",
        "https://docs.python.org/3/",
        "https://example.com"
    ]
    asyncio.run(start_scraping(config, start_urls))
    print_dashboard(config.get("db_path", "data/crawler.db"))