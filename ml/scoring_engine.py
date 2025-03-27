"""ML Scoring Engine for One_Touch_Plus.

This module provides lightweight ML-like scoring and anomaly detection for scraped URLs.
It scores a URL based on its path and keywords, and detects anomalies in the scraped data.
"""

import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def predict_url_score(url: str) -> float:
    """
    Heuristically score a URL based on path keywords.
    Lower scores indicate higher priority.

    Args:
        url (str): The URL to score.

    Returns:
        float: A score between 0 and 1 (lower is higher priority).
    """
    path = urlparse(url).path.lower()

    # Boost keywords reduce score.
    boosts = ["docs", "api", "guide", "reference", "tutorial"]
    # Penalty keywords increase score.
    penalties = ["privacy", "legal", "unsubscribe", "logout", "terms"]

    score = 1.0
    for boost in boosts:
        if boost in path:
            score -= 0.2
    for penalty in penalties:
        if penalty in path:
            score += 0.3
    # Penalty for long URLs.
    if len(url) > 120:
        score += 0.2

    final_score = max(0, round(score, 2))
    logger.debug(f"[scoring_engine] Score for {url}: {final_score}")
    return final_score

def detect_scrape_anomalies(data: dict) -> list:
    """
    Detect anomalies in the scraped data.

    Checks include:
      - Missing or very short title.
      - Insufficient snippet text.
      - Absence of a <title> tag in the HTML.
      - Indicators of a 404 error.

    Args:
        data (dict): The scraped data with keys 'title', 'snippet', and 'html'.

    Returns:
        list: A list of anomaly messages.
    """
    issues = []

    title = data.get("title", "").strip()
    snippet = data.get("snippet", "").strip()
    html = data.get("html", "").lower()

    if not title or len(title) < 5:
        issues.append("Missing or short title")
    if not snippet or len(snippet) < 30:
        issues.append("Insufficient snippet text")
    if "<title>" not in html:
        issues.append("HTML lacks <title> tag")
    if "404" in title or "not found" in html:
        issues.append("Potential 404 error")

    if issues:
        logger.debug(f"[scoring_engine] Anomalies detected: {issues}")
    return issues
