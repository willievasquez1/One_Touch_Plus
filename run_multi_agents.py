"""Multi-Agent Runner for One_Touch_Plus.

This script loads the configuration and launches multiple crawl agents via the agent dispatcher.
"""

import os
import yaml
import asyncio
from core.agent_dispatcher import launch_agents

if __name__ == "__main__":
    config_path = os.path.join("configs", "async_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Full list of seed URLs.
    seed_targets = [
        "https://www.python.org",
        "https://docs.python.org/3/",
        "https://example.com",
        "https://www.djangoproject.com",
        "https://flask.palletsprojects.com"
    ]

    # Launch agents (for example, 2 agents).
    asyncio.run(launch_agents(config, seed_targets, num_agents=2))
