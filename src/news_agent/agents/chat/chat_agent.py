from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import psutil
from agents import Runner, SQLiteSession
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from opentelemetry.metrics import (
    Histogram,
    ObservableGauge,
    Observation,
    get_meter_provider,
)

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
        session_id: SQLiteSession,
        prompt: Optional[str] = None,
    ):
        self.session_id = session_id
        self.prompt = prompt or self.DEFAULT_PROMPT
        self.config: Optional[Dict[str, Any]] = None

        meter = get_meter_provider().get_meter("trend-news-metrics")
        self.chat_lantency_histogram: Histogram = meter.create_histogram(
            name="chat.agent.latency",
            description="Latency of ChatAgent operations",
            unit="s",
        )
        self.cpu_gauge: ObservableGauge = meter.create_observable_gauge(
            name="chat.agent.cpu",
            description="CPU percent during ChatAgent operations",
            unit="percent",
            callbacks=[self._cpu_callback],
        )
        self.ram_gauge: ObservableGauge = meter.create_observable_gauge(
            name="chat.agent.ram",
            description="RAM percent during ChatAgent operations",
            unit="percent",
            callbacks=[self._ram_callback],
        )
        self._current_cpu = 0.0
        self._current_ram = 0.0

    # -------------------------
    # Observable callbacks
    # -------------------------
    def _cpu_callback(self, options):
        return [Observation(self._current_cpu)]

    def _ram_callback(self, options):
        return [Observation(self._current_ram)]

    # -------------------------------------------------------------------------
    # Factory method: initialize agent asynchronously
    # -------------------------------------------------------------------------
    @classmethod
    async def create(
        cls,
        session_id: SQLiteSession,
        ingestion_agent: IngestionAgent,
        prompt: Optional[str] = None,
    ) -> ChatAgent:
        """Factory method to async-initialize ChatAgent for use in app startup."""
        self = cls(
            session_id,
            prompt,
        )

        try:
            # Initialize ChatAgent with IngestionAgent as a handoff
            self.chat_agent = init_agent(
                name="ChatAgent",
                instructions=self.prompt,
                handoffs=[ingestion_agent],
                output_type=ChatOutput,
            )

            logger.info("✅ ChatAgent initialized successfully")
            return self

        except Exception as e:
            logger.exception("❌ Failed to create ChatAgent")
            raise RuntimeError("Failed to initialize ChatAgent") from e

    # -------------------------------------------------------------------------
    # Main chat entrypoint
    # -------------------------------------------------------------------------
    async def chat(self, message: str) -> dict:
        """Primary chat entrypoint — decides between simple or news mode."""
        start_time = time.perf_counter()
        try:
            result = await Runner.run(self.chat_agent, message)
            end_time = time.perf_counter()
            latency = end_time - start_time
            self._current_cpu = psutil.cpu_percent(interval=0.1)
            self._current_ram = psutil.virtual_memory().percent
            self.chat_lantency_histogram.record(latency)
            logger.info(
                f"ChatAgent processed message in {latency:.3f}s | CPU={self._current_cpu:.1f}% | RAM={self._current_ram:.1f}%"
            )
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
            end_time = time.perf_counter()
            latency = end_time - start_time
            self._current_cpu = psutil.cpu_percent(interval=0.1)
            self._current_ram = psutil.virtual_memory().percent
            self.chat_lantency_histogram.record(latency)
            logger.exception(
                f"Error during chat execution | latency={latency:.3f}s, CPU={self._current_cpu:.1f}%, RAM={self._current_ram:.1f}%"
            )
            return {
                "response": "Sorry, something went wrong while processing your request."
            }
