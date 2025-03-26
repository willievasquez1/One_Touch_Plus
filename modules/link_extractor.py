"""Link extraction utility for One_Touch_Plus.

This module extracts and filters anchor links from HTML content using BeautifulSoup.
It applies same-domain filtering, regex-based exclusions, and supports whitelist/blacklist
rules as driven by the configuration. It also filters out URLs with certain query parameters.
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

    crawl_config = config.get("crawl", {})
    same_domain_only = crawl_config.get("same_domain_only", True)
    exclude_query_keys = crawl_config.get("exclude_query_keys", ["utm_", "ref", "session"])
    include_paths = crawl_config.get("whitelist_paths", [])
    exclude_paths = crawl_config.get("blacklist_paths", [])
    exclude_patterns = crawl_config.get("exclude_patterns", [
        r"^javascript:", r"^mailto:", r"#", r"\.pdf$", r"\.zip$"
    ])
    whitelist_patterns = crawl_config.get("whitelist_patterns", [])
    blacklist_patterns = crawl_config.get("blacklist_patterns", [])

    for tag in soup.find_all("a", href=True):
        raw_href = tag["href"].strip()
        full_url = urljoin(base_url, raw_href)
        parsed = urlparse(full_url)

        # Scheme & fragment filtering
        if not parsed.scheme.startswith("http") or parsed.fragment:
            continue

        # Domain filter: enforce same domain if required.
        if same_domain_only and parsed.netloc != base_domain:
            continue

        # Query parameter filtering: skip if any query key starts with an excluded term.
        query_params = parse_qs(parsed.query)
        if any(any(key.startswith(excl) for excl in exclude_query_keys) for key in query_params):
            continue

        # Path-level filtering:
        path = parsed.path or "/"
        if include_paths and not any(p in path for p in include_paths):
            continue
        if any(p in path for p in exclude_paths):
            continue

        # Regex-based filtering:
        if whitelist_patterns and not any(re.search(p, full_url, re.IGNORECASE) for p in whitelist_patterns):
            continue
        if any(re.search(p, full_url, re.IGNORECASE) for p in blacklist_patterns + exclude_patterns):
            continue

        found_links.add(full_url)

    logger.info(f"[extract_links] {len(found_links)} links passed filtering.")
    return list(found_links)
