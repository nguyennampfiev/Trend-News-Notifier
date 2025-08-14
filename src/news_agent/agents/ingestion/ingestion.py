from __future__ import annotations

from typing import Any, Dict, Optional

from agents import Agent, OpenAIResponsesModel, Runner, SQLiteSession
from openai import AsyncOpenAI

from .abstract import AbstractIngestion


def init_agent(mcp_servers):
    """Initialize the agent with all connected MCP servers as tools."""
    return Agent(
        name="Assistant",
        instructions="Use available MCP tools to answer queries.",
        model=OpenAIResponsesModel(
            model="openai/gpt-oss-20b",
            openai_client=AsyncOpenAI(
                base_url="http://0.0.0.0:8000/v1",
                api_key="not-needed",
            ),
        ),
        mcp_servers=mcp_servers,
    )


class IngestionAgent:
    """High-level façade used by your app to process queries."""

    def __init__(self, config_path: str, session_id: SQLiteSession):
        self.config_path = config_path
        self.session_id = session_id
        self._ingestion: Optional[AbstractIngestion] = None

    async def _ensure_connected(self) -> None:
        if self._ingestion is None:
            self._ingestion = await AbstractIngestion.from_config(self.config_path)

    async def process_query(self, query: str) -> Dict[str, Any]:
        await self._ensure_connected()
        mcp_servers = self._ingestion.get_mcp_servers()
        agent = init_agent(mcp_servers)
        result = await Runner.run(agent, query, session=self.session_id)
        if result.final_output:
            return {"results": result.final_output}
        else:
            return {"results": "No results found."}
