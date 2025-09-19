from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from agents import Agent, OpenAIResponsesModel, Runner, SQLiteSession, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from news_agent.agents.ingestion.ingestion import IngestionAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatOutput(BaseModel):
    response: str


class ChatAgent:
    DEFAULT_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are an intelligent news assistant that helps users discover and interact with trending news content.
If the user asks about trending topics, recent news, you must move to news mode otherwise use simple chat mode

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

    @classmethod
    async def create(
        cls,
        config_path: str,
        session_id: SQLiteSession,
        prompt: Optional[str] = None,
    ) -> ChatAgent:
        """Factory method to async-initialize ChatAgent."""
        self = cls(config_path, session_id, prompt)
        await self._load_config()

        # Create the handoff object
        news_handoff_obj = handoff(
            agent=self.ingestion_agent,
            is_enabled=True,
        )

        # Create main ChatAgent with handoff
        self.chat_agent = Agent(
            name="ChatAgent",
            instructions=self.prompt,
            model=OpenAIResponsesModel(
                model="openai/gpt-oss-20b",
                openai_client=AsyncOpenAI(
                    base_url="http://0.0.0.0:8000/v1",
                    api_key="not-needed",
                ),
            ),
            handoffs=[news_handoff_obj],
            output_type=ChatOutput,
        )

        return self

    async def _load_config(self) -> None:
        """Load config and initialize ingestion agent."""
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

        ingest_config_path = self.config.get(
            "ingest_mcp_config",
            "src/news_agent/config/ingest_mcp_config.json",
        )

        ingestion_agent_wrapper = IngestionAgent(ingest_config_path, self.session_id)
        self.ingestion_agent = await ingestion_agent_wrapper.get_agent()

    async def chat(self, message: str) -> dict:
        """Chat interface - LLM automatically decides whether to handoff."""
        result = await Runner.run(self.chat_agent, message)
        print(result.final_output)
        # If news handoff was triggered, the ingestion agent returns final_output.news
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

        # Otherwise, treat as normal chat
        return {"response": result.final_output.response if result.final_output else ""}
