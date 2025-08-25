from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from agents import SQLiteSession
from dotenv import load_dotenv

from src.news_agent.agents.db.db import AbstractTrendDB
from src.news_agent.agents.db.sql_db import SQLiteTrendDB
from src.news_agent.agents.ingestion.ingestion import IngestionAgent
from src.news_agent.agents.sender.abstract import AbstractSender
from src.news_agent.agents.sender.email_sender import EmailSenderAgent

load_dotenv()  # Load environment variables from .env file

smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAIL", "").split(",")
# Suppress DEBUG logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlannerAgent:
    DEFAULT_PROMPT = """
    You are a planner assistant responsible for orchestrating multiple agents
    to build a news notifier pipeline.

    Your workflow:
    1. Call IngestionAgent with trending topics or keywords.
    2. If valid results are returned, save them to the database.
    3. After saving, call SenderAgent to send unsent items to users.
    4. Ensure each item is sent only once (check notified flag in DB).

    Important:
    - Always execute steps in this order: ingestion → database save → sender.
    - If ingestion returns no results, do not call sender.
    - Keep responses structured in JSON with fields: {"action": ..., "data": ...}.
    """

    def __init__(
        self,
        config_path: str,
        session_id: SQLiteSession,
        db: Optional[AbstractTrendDB] = None,
        prompt: Optional[str] = None,
    ):
        self.config_path = config_path
        self.session_id = session_id
        self.prompt = prompt or self.DEFAULT_PROMPT
        self.config: Optional[Dict[str, Any]] = None
        self.ingestion_agent: Optional[IngestionAgent] = None
        self.sender_agent: Optional[AbstractSender] = None
        self.db: AbstractTrendDB = db or SQLiteTrendDB("trends.db")
        self.load_config()

    def load_config(self):
        """Load config from file and initialize agents."""
        with open(self.config_path, "r") as f:
            self.config = json.load(f)
        self.ingestion_agent = IngestionAgent(
            self.config.get("ingest_mcp_config", ""), self.session_id
        )
        self.sender_agent = EmailSenderAgent(
            self.db, smtp_user, smtp_pass, RECIPIENT_EMAILS
        )

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Orchestrate ingestion → save → sender workflow."""
        if not self.ingestion_agent or not self.sender_agent:
            raise RuntimeError("Agents not initialized. Call load_config() first.")

        #  Call IngestionAgent
        try:
            ingestion_result = await self.ingestion_agent.process_query(query)
        except Exception as e:
            logger.error(f"IngestionAgent failed: {e}")
            delay = (
                self.config.get("time_schedule_ingestion", 30) if self.config else 30
            )
            await asyncio.sleep(delay)
            return await self.process_query(query)

        results = ingestion_result.get("results")
        if not results or results == "No results found.":
            logger.info("No results returned from ingestion. Pipeline stopped.")
            return {"results": "No results found."}

        # Save to DB
        try:
            # Parse structured output
            for news_item in results:
                if news_item is None:
                    continue  # skip empty

                topic = getattr(news_item, "topic", "").strip()
                summary = getattr(news_item, "summary", "").strip()
                link = getattr(news_item, "link", "").strip()
                logger.info(f"Saving trend: topic='{topic}', link='{link}'")
                self.db.save_trend(
                    topic=topic, summary=summary, link=link, source="IngestionAgent"
                )
        except Exception as e:
            logger.error(f"Error saving to DB: {e}")
            return {"error": "Failed to save trend to database."}

        # 3 Call SenderAgent to send unsent items
        try:
            sender_result = await self.sender_agent.send_unsent()
            logger.info("SenderAgent completed sending unsent trends.")
        except Exception as e:
            logger.error(f"SenderAgent failed: {e}")
            return {"error": "Failed to send trends."}

        return {
            "results": f"Pipeline completed for query: {query}",
            "ingestion": results,
            "sent_status": sender_result,
        }
