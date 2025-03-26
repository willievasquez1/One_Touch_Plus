"""Link extraction utility for One_Touch_Plus.

This module extracts and filters anchor links from HTML content using BeautifulSoup.
It applies same-domain filtering, regex-based exclusions, and supports whitelist/blacklist
rules for both URL paths and query parameters, as driven by the configuration.
"""

from urllib.parse import urlparse, urljoin, parse_qs
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

def extract_links(html: str, base_url: str, config: dict) -> list:
    """
    Extracts and filters anchor links from the given HTML content.

    Args:
        html (str): The HTML content to parse.
        base_url (str): The URL of the page where the content came from.
        config (dict): Scraper configuration, which may include filtering rules.

    Returns:
        list: A list of filtered, fully-qualified URLs.
    """
    soup = BeautifulSoup(html, "lxml")
    found_links = set()
    base_domain = urlparse(base_url).netloc

    crawl_cfg = config.get("crawl", {})

    same_domain_only = crawl_cfg.get("same_domain_only", True)
    exclude_query_keys = crawl_cfg.get("exclude_query_keys", ["utm_", "ref", "session"])
    include_query_values = crawl_cfg.get("include_query_values", {})  # e.g. {"source": ["trusted", "api"]}
    whitelist_paths = crawl_cfg.get("whitelist_paths", [])
    blacklist_paths = crawl_cfg.get("blacklist_paths", [])
    exclude_patterns = crawl_cfg.get("exclude_patterns", [])
    whitelist_patterns = crawl_cfg.get("whitelist_patterns", [])
    blacklist_patterns = crawl_cfg.get("blacklist_patterns", [])

    for tag in soup.find_all("a", href=True):
        raw_href = tag["href"].strip()
        full_url = urljoin(base_url, raw_href)
        parsed = urlparse(full_url)
        query_params = parse_qs(parsed.query)

        # Scheme & fragment filter: only process HTTP/HTTPS URLs without fragments.
        if not parsed.scheme.startswith("http") or parsed.fragment:
            continue

        # Domain filtering: enforce same domain if configured.
        if same_domain_only and parsed.netloc != base_domain:
            continue

        # Query parameter filtering: skip if any query key starts with an excluded term.
        if any(any(key.startswith(excl) for excl in exclude_query_keys) for key in query_params):
            continue

        # Optional: include only records where specific query param keys have allowed values.
        if include_query_values:
            valid = all(
                any(val in query_params.get(k, []) for val in allowed)
                for k, allowed in include_query_values.items()
            )
            if not valid:
                continue

        # Path-level filtering.
        path = parsed.path or "/"
        # Whitelist: if provided, only include links whose path contains at least one allowed substring.
        if whitelist_paths and not any(allowed in path for allowed in whitelist_paths):
            continue
        # Blacklist: skip if path contains any disallowed substring.
        if any(bad in path for bad in blacklist_paths):
            continue

        # Regex-based filtering:
        # If whitelist_patterns are provided, only include links that match at least one.
        if whitelist_patterns and not any(re.search(pattern, full_url, re.IGNORECASE) for pattern in whitelist_patterns):
            continue
        # Exclude links that match any blacklist or exclude pattern.
        if any(re.search(pattern, full_url, re.IGNORECASE) for pattern in blacklist_patterns + exclude_patterns):
            continue

        found_links.add(full_url)

    logger.info(f"[extract_links] {len(found_links)} links passed filtering.")
    return list(found_links)
