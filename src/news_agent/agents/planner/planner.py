from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from agents import SQLiteSession
from dotenv import load_dotenv

from news_agent.agents.db.db import AbstractTrendDB
from news_agent.agents.db.sql_db import SQLiteTrendDB
from news_agent.agents.ingestion.ingestion import IngestionAgent
from news_agent.agents.sender.abstract import AbstractSender
from news_agent.agents.sender.email_sender import EmailSenderAgent
from news_agent.agents.validator.deduplication_agent import DeduplicationAgent

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

        # Load config parameters
        ingest_config_path = self.config.get(
            "ingest_mcp_config", "src/news_agent/config/ingest_mcp_config.json"
        )
        self.email_send_interval = self.config.get("email_send_interval_minutes", 60)
        self.crawl_interval = self.config.get("crawl_interval_minutes", 30)
        self.process_retry_delay = self.config.get("process_retry_delay_seconds", 30)
        self.max_ingestion_retries = self.config.get("max_ingestion_retries", 5)
        self.ingestion_failure_delay = self.config.get(
            "ingestion_failure_delay_minutes", 15
        )

        self.ingestion_agent = IngestionAgent(ingest_config_path, self.session_id)
        self.sender_agent = EmailSenderAgent(
            self.db, smtp_user, smtp_pass, RECIPIENT_EMAILS
        )
        self.deduplication_agent = DeduplicationAgent(self.db, self.session_id)

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Orchestrate ingestion → save → sender workflow."""
        if not self.ingestion_agent or not self.sender_agent:
            raise RuntimeError("Agents not initialized. Call load_config() first.")

        # Call IngestionAgent with retry logic based on config
        retries = 0
        while retries < self.max_ingestion_retries:
            try:
                ingestion_result = await self.ingestion_agent.process_query(query)
                break
            except Exception as e:
                logger.error(f"IngestionAgent failed (attempt {retries+1}): {e}")
                await asyncio.sleep(self.process_retry_delay)
                retries += 1
        else:
            logger.error("Max ingestion retries reached. Delaying before next attempt.")
            await asyncio.sleep(self.ingestion_failure_delay * 60)
            return {"results": "No results found due to repeated ingestion failures."}

        results = ingestion_result.get("results")
        if not results or results == "No results found.":
            logger.info("No results returned from ingestion. Pipeline stopped.")
            results = []

        if results:
            # Save to DB
            try:
                for news_item in results.news:
                    if news_item is None:
                        continue  # skip empty

                    topic = getattr(news_item, "topic", "").strip()
                    summary = getattr(news_item, "summary", "").strip()
                    link = getattr(news_item, "link", "").strip()
                    check_duplicate = await self.deduplication_agent.is_duplicate(
                        topic, summary, link
                    )

                    if check_duplicate:  # Skip duplicates
                        logger.info(
                            f"Duplicate found, skipping: topic='{topic}', link='{link}'"
                        )
                        continue
                    else:
                        logger.info(f"Saving trend: topic='{topic}', link='{link}'")
                        self.db.save_trend(
                            topic=topic,
                            summary=summary,
                            url=link,
                            source="IngestionAgent",
                        )
            except Exception as e:
                logger.error(f"Error saving to DB: {e}")
                return {"error": "Failed to save trend to database."}

        # Call SenderAgent to send unsent items
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
