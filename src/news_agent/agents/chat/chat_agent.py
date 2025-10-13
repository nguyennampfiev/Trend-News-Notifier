from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from agents import Agent, Runner, SQLiteSession
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv

from news_agent.agents.base_agent import init_agent
from news_agent.agents.ingestion.ingestion import IngestionAgent
from news_agent.agents.schema import ChatOutput

# -----------------------------------------------------------------------------
# Load environment variables (.env for local, environment vars in AWS)
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# Configure logging
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ChatAgent:
    """Unified Chat + News handoff agent for the Trend News Notifier."""

    DEFAULT_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are an intelligent news assistant that helps users discover and interact with trending news content.
If the user asks about trending topics, recent news, you must move to news mode otherwise use simple chat mode.

Modes of operation:

**NEWS MODE:**
1. Understand intent (search topics, trending news, recent events)
2. Use IngestionAgent for trending topics or keywords
3. Respond conversationally with summaries, insights, and follow-ups
4. Track context and user preferences

**SIMPLE CHAT MODE:**
1. Respond to general conversation, questions, or casual chat
2. Do not fetch news or external data
3. Keep responses natural, engaging, and helpful
4. Follow context and maintain continuity

**Guidelines:**
- Natural, helpful responses
- Suggest alternatives if no news found
- Provide context for why topics trend
- Handle follow-up questions gracefully

**Error Handling:**
- Explain ingestion failures, suggest alternatives
- Always stay helpful and user-focused
"""

    def __init__(
        self,
        config_path: str,
        session_id: SQLiteSession,
        prompt: Optional[str] = None,
    ):
        self.config_path = config_path
        self.session_id = session_id
        self.prompt = prompt or self.DEFAULT_PROMPT

        self.config: Optional[Dict[str, Any]] = None
        self.ingestion_agent: Optional[Agent] = None
        self.chat_agent: Optional[Agent] = None

    # -------------------------------------------------------------------------
    # Factory method: initialize agent asynchronously
    # -------------------------------------------------------------------------
    @classmethod
    async def create(
        cls,
        config_path: Optional[str],
        session_id: SQLiteSession,
        prompt: Optional[str] = None,
    ) -> ChatAgent:
        """Factory method to async-initialize ChatAgent for use in app startup."""
        self = cls(
            config_path
            or os.getenv(
                "CHAT_AGENT_CONFIG", "src/news_agent/config/agent_config.json"
            ),
            session_id,
            prompt,
        )

        try:
            await self._load_config()
            await self._setup_ingestion_agent()

            # Initialize ChatAgent with IngestionAgent as a handoff
            self.chat_agent = init_agent(
                name="ChatAgent",
                instructions=self.prompt,
                handoffs=[self.ingestion_agent],
                output_type=ChatOutput,
            )

            logger.info("✅ ChatAgent initialized successfully")
            return self

        except Exception as e:
            logger.exception("❌ Failed to create ChatAgent")
            raise RuntimeError("Failed to initialize ChatAgent") from e

    # -------------------------------------------------------------------------
    # Load configuration JSON safely
    # -------------------------------------------------------------------------
    async def _load_config(self) -> None:
        """Load configuration file from provided path or fallback defaults."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(
                    f"Config file not found at {self.config_path}. Using defaults."
                )

                self.config = {
                    "ingest_mcp_config": os.getenv(
                        "INGEST_MCP_CONFIG",
                        "src/news_agent/config/ingest_mcp_config.json",
                    )
                }
                return

            with open(self.config_path, "r") as f:
                self.config = json.load(f)

            logger.info(f"Loaded ChatAgent config from {self.config_path}")

        except Exception as e:
            logger.exception("Error loading ChatAgent configuration")
            raise RuntimeError("Failed to load ChatAgent configuration") from e

    # -------------------------------------------------------------------------
    # Initialize IngestionAgent
    # -------------------------------------------------------------------------
    async def _setup_ingestion_agent(self) -> None:
        """Initialize the ingestion agent safely."""
        try:
            ingest_config_path = self.config.get(
                "ingest_mcp_config",
                os.getenv(
                    "INGEST_MCP_CONFIG", "src/news_agent/config/ingest_mcp_config.json"
                ),
            )

            ingestion_wrapper = IngestionAgent(ingest_config_path, self.session_id)
            self.ingestion_agent = await ingestion_wrapper.get_agent()

            logger.info("✅ IngestionAgent initialized successfully")

        except Exception as e:
            logger.exception("Failed to setup IngestionAgent")
            raise RuntimeError("Failed to setup IngestionAgent") from e

    # -------------------------------------------------------------------------
    # Main chat entrypoint
    # -------------------------------------------------------------------------
    async def chat(self, message: str) -> dict:
        """Primary chat entrypoint — decides between simple or news mode."""
        try:
            result = await Runner.run(self.chat_agent, message)
            logger.info(f"ChatAgent final output: {result.final_output}")

            if hasattr(result.final_output, "news") and result.final_output.news:
                news_dicts = [
                    {
                        "topic": getattr(item, "topic", "").strip(),
                        "summary": getattr(item, "summary", "").strip(),
                        "link": getattr(item, "link", "").strip(),
                        "title": getattr(item, "title", item.topic).strip(),
                    }
                    for item in result.final_output.news
                ]
                return {"news": news_dicts}

            return {
                "response": result.final_output.response if result.final_output else ""
            }

        except Exception:
            logger.exception("Error during chat execution")
            return {
                "response": "Sorry, something went wrong while processing your request."
            }
