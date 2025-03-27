"""CLI entry point for the One_Touch_Plus web scraper.

This module parses command-line arguments and initiates the scraping process.
It supports single URL mode and batch mode (for future use), as well as utility 
flags for cleaning data directories and generating template configuration files.
"""

import sys
import os
import argparse
import asyncio
import logging
import shutil
import yaml

# Ensure the project root (One_Touch_Plus) is in the sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up basic logging for CLI operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments for the One_Touch_Plus scraper CLI."""
    parser = argparse.ArgumentParser(description="One_Touch_Plus Web Scraper CLI")
    parser.add_argument("--url", help="Single URL to scrape", type=str)
    parser.add_argument("--batch", help="Path to a batch file containing URLs to scrape", type=str)
    parser.add_argument("--clean", help="Clean temporary files and exit", action="store_true")
    parser.add_argument("--generate-temp-config", help="Generate a template temp_config.yaml and exit", action="store_true")
    return parser.parse_args()

async def main():
    """Main asynchronous entry point for running the web scraper."""
    args = parse_args()

    # Handle utility flags before starting scrape
    if args.clean:
        logger.info("🧹 Cleaning temporary files and directories...")
        # Remove generated data directories and temporary config if they exist
        for path in ['data/images', 'data/pdfs', 'data/captcha_images', 'data/temp_config.yaml']:
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    logger.debug(f"Removed {path}")
                except Exception as e:
                    logger.error(f"Error removing {path}: {e}")
        logger.info("✅ Data directories cleaned.")
        return

    if args.generate_temp_config:
        logger.info("Generating template configuration file...")
        # Example template configuration structure
        template_config = {
            'scraper': {'concurrency': 5, 'max_depth': 3},
            'performance': {'max_scroll': 8},
            'pdf': {'ocr_enabled': True}
        }
        os.makedirs('data', exist_ok=True)
        with open('data/temp_config.yaml', 'w') as f:
            yaml.safe_dump(template_config, f, sort_keys=False)
        logger.info("✅ Template temp_config.yaml created in /data directory.")
        return

    # Load and validate configuration
    from modules import config_manager
    config = config_manager.load_config()
    config_manager.validate_config(config)

    # Determine scraping mode and start accordingly
    if args.url:
        logger.info(f"Starting scrape for URL: {args.url}")
        # For single URL, run the scraping orchestrator (possibly asynchronous)
        from core import scrape_orchestrator
        await scrape_orchestrator.start_scraping(config, targets=args.url)
    elif args.batch:
        logger.info(f"Starting batch scrape for file: {args.batch}")
        # Batch mode: iterate through URLs in batch file (placeholder)
        # TODO: Implement reading URLs from batch file and orchestrate multi-URL scraping
        logger.warning("Batch mode is not yet implemented.")
    else:
        parser = argparse.ArgumentParser()  # reuse parser to print usage
        parser.print_usage()
        logger.error("No target provided. Use --url or --batch to specify targets.")

if __name__ == "__main__":
    # Run the main function in the event loop
    asyncio.run(main())
