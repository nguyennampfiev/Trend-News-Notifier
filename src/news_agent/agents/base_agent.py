from __future__ import annotations

from typing import List

from agents import Agent, OpenAIResponsesModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI


def init_agent(
    instructions: str,
    mcp_servers: List[MCPServerStdio],
    tool: List = [],
    name: str = "Assistant",
) -> Agent:
    """
    Initialize the agent with custom instructions and connected MCP servers.
    """
    if tool is None:
        tool = []
    return Agent(
        name=name,
        instructions=instructions,
        model=OpenAIResponsesModel(
            model="openai/gpt-oss-20b",
            openai_client=AsyncOpenAI(
                base_url="http://0.0.0.0:8000/v1",
                api_key="not-needed",
            ),
        ),
        mcp_servers=mcp_servers,
        tools=tool,
    )
