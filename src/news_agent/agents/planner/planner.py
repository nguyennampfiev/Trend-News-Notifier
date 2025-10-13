from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from agents import Runner, SQLiteSession
from dotenv import load_dotenv

from news_agent.agents.base_agent import init_agent
from news_agent.agents.db.sqlachemy_db import SQLAlchemySubscriptionDB
from news_agent.agents.db.trend import SQLiteTrendDB
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
        db: Optional[SQLAlchemySubscriptionDB] = None,
        prompt: Optional[str] = None,
    ):
        self.config_path = config_path
        self.session_id = session_id
        self.prompt = prompt or self.DEFAULT_PROMPT
        self.config: Optional[Dict[str, Any]] = None
        self.ingestion_agent: Optional[IngestionAgent] = None
        self.sender_agent: Optional[AbstractSender] = None
        self.db: SQLAlchemySubscriptionDB = db or SQLiteTrendDB("trends.db")
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
        # Create list of handoffs
        handoffs = [self.ingestion_agent, self.deduplication_agent, self.sender_agent]

        self.planner_agent = init_agent(
            instructions=self.prompt,
            mcp_servers=[],
            name="PlannerAgent",
            handoffs=handoffs,
        )

    async def process_query(self, query: str) -> Dict[str, Any]:
        results = await Runner.run(self.planner_agent, query)
        return {"results": results.final_output}

    async def automatic_agent_loop(self, interval_minutes: int = 60):
        """Background task to run the agent periodically."""
        while True:
            try:
                logger.info("Starting automatic agent run...")
                topics = await self.db.get_all_topics()
                if not topics:
                    logger.info("No topics found in the database. Skipping this run.")
                else:
                    for topic in topics:
                        logger.info(f"Processing topic: {topic}")
                        await self.process_query(topic)
                logger.info("Automatic agent run completed.")
            except Exception as e:
                logger.error(f"Error during automatic agent run: {e}")
            await asyncio.sleep(interval_minutes * 60)
