"""CAPTCHA fallback diagnostic utility for One_Touch_Plus.

Saves HTML snapshots of suspected CAPTCHA pages for review.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def handle_captcha_failure(html: str, url: str, config: dict):
    if not config.get("captcha", {}).get("fallback_enabled", False):
        logger.debug("[CAPTCHA] Fallback not enabled.")
        return

    output_dir = config.get("captcha", {}).get("snapshot_dir", "data/captcha_logs")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_url = url.replace("https://", "").replace("http://", "").replace("/", "_")
    filename = f"{timestamp}_{safe_url}.html"
    path = os.path.join(output_dir, filename)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"[CAPTCHA] Saved fallback HTML snapshot: {path}")
    except Exception as e:
        logger.error(f"[CAPTCHA] Failed to save snapshot: {e}")
