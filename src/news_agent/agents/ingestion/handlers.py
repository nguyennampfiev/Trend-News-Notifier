from __future__ import annotations

import abc
from typing import Any, Dict, Optional

from agents.mcp import MCPServerStdio

# logger = logging.getLogger(__name__)


class BaseMCPHandler(abc.ABC):
    """
    Abstract base class for MCP handlers.
    """

    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params
        self.server: Optional[MCPServerStdio] = None
        self.connected = False

    async def connect(self) -> None:
        """
        Connect to the MCP server.
        """
        self.server = MCPServerStdio(params=self.params, name=self.name)
        await self.server.connect()
        self.connected = True
        # logger.info(f"Connected to MCP server: {self.name}")

    def get_mcp_server(self) -> MCPServerStdio:
        """
        Get the MCP server instance.
        """
        if not self.connected:
            raise RuntimeError("MCP server is not connected.")
        return self.server


class FirecrawlHandler(BaseMCPHandler):
    """
    Handler for Firecrawl MCP server.
    """

    pass


class SerpAPISearchHandler(BaseMCPHandler):
    """
    Handler for SerpAPISearch MCP server.
    """

    pass
