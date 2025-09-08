from __future__ import annotations

from typing import List

from agents import Agent, OpenAIResponsesModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI


def init_agent(
    instructions: str,
    mcp_servers: List[MCPServerStdio] | None = None,
    tool: List = [],
    name: str = "Assistant",
    output_guardrails: List = None,
    output_type: type = None,
) -> Agent:
    """
    Initialize the agent with custom instructions and connected MCP servers.
    """
    if mcp_servers is None:
        mcp_servers = []

    if tool is None:
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
            output_type=output_type,
        )
    else:
        return Agent(
            name=name,
            instructions=instructions,
            model=OpenAIResponsesModel(
                model="openai/gpt-oss-20b",
                openai_client=AsyncOpenAI(
                    base_url="http://0.0.0.0:8000/v1",
                    api_key="gg",
                ),
            ),
            mcp_servers=mcp_servers,
            tools=tool,
            output_type=output_type,
        )
