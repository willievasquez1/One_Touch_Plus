"""Scraping orchestration logic for One_Touch_Plus.

This module coordinates asynchronous scraping tasks, managing the crawl queue,
concurrent URL fetching, and invoking various handlers (dynamic content, CAPTCHA, PDF extraction).
It uses an asyncio.Semaphore to limit concurrent tasks.

TODO:
    - Integrate CAPTCHA handling via captcha_handler.handle_captcha.
    - Enhance error handling and retry strategies.
    - Add config-driven output formats and storage paths.
"""

import asyncio
import logging
import os
import yaml

# Configure logging to output to the console.
logging.basicConfig(level=logging.INFO)

from core.crawl_manager import CrawlManager
from modules.output_reporter import OutputReporter
from modules.page_fetcher import fetch_page
from modules.link_extractor import extract_links  # Real link extraction
from handlers import dynamic_content_utils, captcha_handler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONCURRENT_TASKS = 5  # Can be adjusted from config later

async def process_url(
    url: str,
    depth: int,
    config: dict,
    crawl_mgr: CrawlManager,
    semaphore: asyncio.Semaphore,
    reporter: OutputReporter
):
    """
    Process a single URL: fetch the page, expand dynamic content, extract links,
    invoke the CAPTCHA handler, report output, and enqueue new URLs if within depth limits.
    """
    async with semaphore:
        try:
            # Step 1: Fetch page content.
            scraped_data = await fetch_page(url, config)

            # Use full HTML instead of snippet for processing.
            html = scraped_data.get("html", "")

            # Step 2: Expand dynamic content (stub or real handler).
            expanded_html = await dynamic_content_utils.expand_content(html, config)

            # Update snippet for better logging/reporting (first 300 characters).
            scraped_data["snippet"] = expanded_html[:300]

            # Step 3: Invoke the CAPTCHA handler (stub for now).
            await captcha_handler.handle_captcha(expanded_html, config)

            # Step 4: Report the scraped data.
            reporter.generate_report(scraped_data)

            # Step 5: Extract links from expanded HTML.
            new_links = extract_links(expanded_html, base_url=url, config=config)
            max_depth = config.get('scraper', {}).get('max_depth', 3)
            if depth < max_depth:
                for new_url in new_links:
                    crawl_mgr.add_url(new_url, depth=depth + 1)
                    logger.info(f"Added new URL to crawl: {new_url} at depth {depth + 1}")

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

async def start_scraping(config: dict, target):
    """
    Initiate the scraping process for a target URL or list of URLs.
    """
    max_depth = config.get('scraper', {}).get('max_depth', 3)
    crawl_mgr = CrawlManager(max_depth=max_depth)

    targets = [target] if isinstance(target, str) else target if isinstance(target, list) else []
    if not targets:
        logger.error("Invalid target(s). Must be string or list of strings.")
        return

    for url in targets:
        crawl_mgr.add_url(url, depth=0)

    reporter = OutputReporter(config)
    semaphore = asyncio.Semaphore(CONCURRENT_TASKS)
    tasks = []

    while True:
        result = crawl_mgr.get_next_url()
        if not result:
            break
        url, depth = result
        logger.info(f"Scheduling URL: {url} at depth {depth}")
        task = asyncio.create_task(process_url(url, depth, config, crawl_mgr, semaphore, reporter))
        tasks.append(task)

    if tasks:
        await asyncio.gather(*tasks)

    logger.info("✅ Scraping process completed.")

if __name__ == "__main__":
    config_path = os.path.join("configs", "async_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    asyncio.run(start_scraping(config, "https://www.python.org"))
