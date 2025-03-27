#!/usr/bin/env python3
"""
URL.py - Batch & Single URL Runner for One_Touch_Plus

This module serves as the control center for URL input. It supports running a single URL 
or processing a batch of URL jobs defined in a YAML file (e.g., batch_urls.yaml).

Each batch job can include metadata such as priority, description, custom configuration
overrides, concurrency settings, and output subdirectories. The module loads the global 
configuration from async_config.yaml, merges it with any job-specific settings, and then 
calls the core orchestrator (start_scraping) to run the crawl.

Usage:
    # Run a single URL:
    python URL.py --url "https://example.com"
    
    # Run batch jobs defined in batch_urls.yaml:
    python URL.py --batch
"""

import argparse
import os
import sys
import yaml
import logging
import asyncio
from copy import deepcopy

# Import the core orchestrator
from core.scrape_orchestrator import start_scraping

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
)

def load_global_config(config_path="configs/async_config.yaml"):
    """Load the global configuration."""
    if not os.path.exists(config_path):
        logger.error(f"Global config not found: {config_path}")
        sys.exit(1)
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config

def load_batch_jobs(batch_file="batch_urls.yaml"):
    """
    Load batch jobs from a YAML file.

    The YAML should have a key 'batch_urls' with a list of job dictionaries.
    """
    if not os.path.exists(batch_file):
        logger.error(f"Batch jobs file not found: {batch_file}")
        sys.exit(1)
    with open(batch_file, "r") as f:
        jobs_config = yaml.safe_load(f) or {}
    jobs = jobs_config.get("batch_urls", [])
    if not jobs:
        logger.error("No batch jobs found in the batch file.")
        sys.exit(1)
    # Sort jobs by priority (lower number means higher priority)
    jobs.sort(key=lambda job: job.get("priority", 5))
    return jobs

def merge_configs(global_config, job_config):
    """
    Recursively merge two dictionaries.

    Values from job_config override those in global_config.
    """
    def merge(a, b):
        for key, value in b.items():
            if key in a and isinstance(a[key], dict) and isinstance(value, dict):
                merge(a[key], value)
            else:
                a[key] = value
        return a
    merged = deepcopy(global_config)
    return merge(merged, job_config)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="One_Touch_Plus URL Runner - Execute single URL or batch jobs."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", type=str, help="Single URL to crawl.")
    group.add_argument("--batch", action="store_true", help="Run batch jobs from batch_urls.yaml.")
    return parser.parse_args()

async def run_single_url(global_config, url):
    """Run the crawler for a single URL using the global configuration."""
    logger.info(f"Running single URL: {url}")
    await start_scraping(global_config, url)

async def run_batch_jobs(global_config):
    """Run batch jobs from batch_urls.yaml."""
    jobs = load_batch_jobs()
    logger.info(f"Loaded {len(jobs)} batch jobs.")
    # For each job, merge its custom config (if any) with the global configuration
    for job in jobs:
        job_url = job.get("url")
        if not job_url:
            logger.error("Job missing required URL.")
            continue
        job_config = job.get("custom_config", {})
        # Merge custom config into the global configuration
        merged_config = merge_configs(global_config, job_config)
        # Log additional job metadata if provided
        priority = job.get("priority", 5)
        description = job.get("description", "")
        logger.info(f"Starting job for URL: {job_url} (priority {priority}) - {description}")
        # Optionally, output_subdir and concurrency overrides could be handled here
        await start_scraping(merged_config, job_url)

def main():
    args = parse_args()
    global_config = load_global_config()

    if args.url:
        asyncio.run(run_single_url(global_config, args.url))
    elif args.batch:
        asyncio.run(run_batch_jobs(global_config))

if __name__ == "__main__":
    main()
