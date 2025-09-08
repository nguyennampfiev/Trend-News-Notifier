from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from agents import Runner, SQLiteSession

from news_agent.agents.base_agent import init_agent
from news_agent.agents.schema import NewsOutput

from .abstract import AbstractIngestion

# from agents import (Agent, GuardrailFunctionOutput, OpenAIResponsesModel,
#                     RunContextWrapper, Runner, SQLiteSession, output_guardrail)
# from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# guardrail_agent = Agent(
#     name="GuardrailAgent",
#     model=OpenAIResponsesModel(
#         model="openai/gpt-oss-20b",
#         openai_client=AsyncOpenAI(
#             base_url="http://0.0.0.0:8000/v1",
#             api_key="not-needed",
#         ),
#     ),
#     instructions="An agent that ensures output adheres to a specified format.",
#     output_type=NewsOutput,
# )


# @output_guardrail
# async def check_ouputformat_with_guardrail(
#     ctx: RunContextWrapper, agent: Agent, output: MessageOutput
# ) -> GuardrailFunctionOutput:
#     result = await Runner.run(guardrail_agent, output.response, context=ctx.context)
#     logger.info(f"Guardrail output: {result.final_output}")
#     return GuardrailFunctionOutput(
#         output_info=result.final_output,
#         tripwire_triggered=result.final_output.link,
#     )


class IngestionAgent:
    DEFAULT_PROMPT = """
    You are a news assistant.
    Given a trending topic or keyword, search the web using SerpApi or Firecrawl and produce a concise summary of the latest news.
    - If news is duplicated, skip it.
    - The summary must be **2-3 sentences**.
    - Include the **most relevant link** for the topic.
    - Focus on **main points only**; ignore fluff, filler, or background context unless essential.
    - Write in **clear, succinct language**, suitable for quick consumption.
    - Do not include personal opinions, commentary, or unnecessary details.
    - Output format should be List of JSON format for each news item:
    [{
    "topic": tile of the news article,
    "summary": <2-3 sentence summary of main points>,
    "link": <URL to main news article>
    }, ...]
    """

    def __init__(
        self, config_path: str, session_id: SQLiteSession, prompt: Optional[str] = None
    ):
        self.config_path = config_path
        self.session_id = session_id
        self._ingestion: Optional[AbstractIngestion] = None
        self.prompt = prompt or self.DEFAULT_PROMPT

    async def _ensure_connected(self) -> None:
        if self._ingestion is None:
            self._ingestion = await AbstractIngestion.from_config(self.config_path)

    async def process_query(self, query: str) -> Dict[str, Any]:
        await self._ensure_connected()
        mcp_servers = self._ingestion.get_mcp_servers()
        logger.info(f"Connected MCP servers: {[server.name for server in mcp_servers]}")
        # print mcp tool names
        # for server in mcp_servers:
        #    tools = await server.list_tools()
        #    logger.info(f"MCP server '{server.name}' has tools: {tools}")
        # agent = init_agent(self.prompt, mcp_servers, name="IngestionAgent", output_guardrails=[check_ouputformat_with_guardrail], output_type=MessageOutput)
        # agent
        # result = await Runner.run(agent, query, session=self.session_id)
        agent = init_agent(
            self.prompt, mcp_servers, name="IngestionAgent", output_type=NewsOutput
        )
        result = await Runner.run(agent, query, session=self.session_id)
        logger.info(f"IngestionAgent output: {result.final_output}")
        if result.final_output:
            print(result.final_output)
            return {"results": result.final_output}
        else:
            return {"results": "No results found."}
