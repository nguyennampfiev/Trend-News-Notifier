from __future__ import annotations

import asyncio
import json
from typing import Dict, List

from agents.mcp import MCPServerStdio

from .handlers import BaseMCPHandler, FirecrawlHandler, SerpAPISearchHandler

# logger = logging.getLogger(__name__)


class AbstractIngestion:
    """
    Abstract base class for loading and managing MCP servers.
    """

    def __init__(self, handlers: List[BaseMCPHandler]):
        self.handlers = handlers

    @classmethod
    async def from_config(cls, config_path: str) -> AbstractIngestion:
        """
        Load MCP handlers from a configuration file.
        """
        with open(config_path, "r") as f:
            config = json.load(f)

        servers: Dict[str, dict] = config.get("mcp", {}).get("servers", {})
        handlers_obj = []

        for name, params in servers.items():
            if name == "firecrawl":
                handler = FirecrawlHandler(name=name, params=params)

            elif name == "serpapisearch":
                handler = SerpAPISearchHandler(name=name, params=params)

            # if name == "scraper":
            #    handler = ScraperHandler(name=name, params=params)

            else:
                raise ValueError(f"Unknown MCP server type: {name}")

        handlers_obj.append(handler)
        await asyncio.gather(*(handler.connect() for handler in handlers_obj))
        return cls(handlers=handlers_obj)

    def get_mcp_servers(self) -> List[MCPServerStdio]:
        """
        Get a list of connected MCP server instances.
        """
        return [
            handler.get_mcp_server() for handler in self.handlers if handler.connected
        ]
