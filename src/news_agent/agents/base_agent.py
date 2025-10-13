from __future__ import annotations

from typing import Any, List, Optional

from agents import Agent, OpenAIResponsesModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI


def init_agent(
    instructions: str,
    mcp_servers: Optional[List[MCPServerStdio]] = None,
    tool: Optional[List[Any]] = None,
    name: str = "Assistant",
    output_guardrails: Optional[List[Any]] = None,
    handoffs: Optional[List[Any]] = None,
    output_type: Optional[type] = None,
) -> Agent:
    """
    Initialize an Agent with default configuration.
    Makes `handoffs` optional (defaults to an empty list).
    """

    # Default values for optional args
    if mcp_servers is None:
        mcp_servers = []
    if tool is None:
        tool = []
    if handoffs is None:
        handoffs = []  # ✅ key fix here

    # Initialize OpenAI-compatible model
    model = OpenAIResponsesModel(
        model="openai/gpt-oss-20b",
        openai_client=AsyncOpenAI(
            base_url="http://0.0.0.0:8000/v1",
            api_key="not-needed",
        ),
    )

    # Return configured agent
    return Agent(
        name=name,
        instructions=instructions,
        model=model,
        mcp_servers=mcp_servers,
        tools=tool,
        output_type=output_type,
        handoffs=handoffs,
    )
