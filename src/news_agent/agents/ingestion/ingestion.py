from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from agents import Runner, SQLiteSession

from src.news_agent.agents.base_agent import init_agent

from .abstract import AbstractIngestion

# Suppress DEBUG logs from all libraries
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
#     handlers=[
#         logging.StreamHandler(sys.stderr),
#             ]
# )
# logger = logging.getLogger(__name__)


class IngestionAgent:
    DEFAULT_PROMPT = """
    You are a news assistant.
    Given a trending topic or keyword, search the web using SerpApi or Firecrawl and produce a concise summary of the latest news.

    - The summary must be **2-3 sentences**.
    - Include the **most relevant link** for the topic.
    - Focus on **main points only**; ignore fluff, filler, or background context unless essential.
    - Write in **clear, succinct language**, suitable for quick consumption.
    - Do not include personal opinions, commentary, or unnecessary details.
    - Output format should be:

    Topic: <TRENDING TOPIC>
    Summary: <2-3 sentence summary of main points>
    Link: <URL to main news article>
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
        # logger.info(f"Connected MCP servers: {[server.name for server in mcp_servers]}")
        agent = init_agent(self.prompt, mcp_servers, name="IngestionAgent")
        result = await Runner.run(agent, query, session=self.session_id)

        if result.final_output:
            return {"results": result.final_output}
        else:
            return {"results": "No results found."}
