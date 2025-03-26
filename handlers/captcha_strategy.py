"""CAPTCHA Strategy Interface for One_Touch_Plus.

This module defines handle_captcha, which routes CAPTCHA handling based on the configured mode.
Options include 'none', 'fallback', and 'solver' (for future integration).
"""

import logging
from handlers import captcha_fallback

logger = logging.getLogger(__name__)

def handle_captcha(html: str, url: str, config: dict):
    mode = config.get("captcha", {}).get("mode", "fallback")

    if mode == "none":
        logger.debug("[CAPTCHA] Mode: none — skipping CAPTCHA handling.")
    elif mode == "fallback":
        logger.info("[CAPTCHA] Mode: fallback — invoking fallback diagnostic.")
        captcha_fallback.handle_captcha_failure(html, url, config)
    elif mode == "solver":
        logger.warning("[CAPTCHA] Mode: solver selected — no solver integrated yet.")
    else:
        logger.error(f"[CAPTCHA] Unknown mode: {mode}. Skipping CAPTCHA handling.")
