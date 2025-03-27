"""Agent Dispatcher for One_Touch_Plus.

Launches multiple asynchronous crawl agents, each with its own agent ID.
Each agent is assigned a slice of the seed URL list.
"""

import asyncio
import uuid
import logging
from core.scrape_orchestrator import start_scraping

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def launch_agents(config: dict, targets: list[str], num_agents: int = 2):
    """
    Launch multiple crawl agents concurrently.

    Args:
        config (dict): The shared crawler configuration.
        targets (list): The full list of seed URLs.
        num_agents (int): Number of parallel crawl agents.
    """
    logger.info(f"🚀 Launching {num_agents} crawl agents...")
    # Determine chunk size for splitting targets
    chunk_size = max(1, len(targets) // num_agents)
    tasks = []
    
    for i in range(num_agents):
        agent_id = str(uuid.uuid4())[:8]
        # Each agent gets a slice of targets
        agent_targets = targets[i * chunk_size : (i + 1) * chunk_size]
        
        if not agent_targets:
            continue
        
        logger.info(f"[Agent {agent_id}] Assigned {len(agent_targets)} URLs")
        task = asyncio.create_task(
            start_scraping(config, agent_targets, agent_id=agent_id)
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
