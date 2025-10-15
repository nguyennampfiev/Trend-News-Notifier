from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from sqlalchemy import select

from news_agent.agents.db.sqlachemy_db import (
    SQLAlchemySubscriptionDB,
    Tag,
    Trend,
    get_db,
    trend_tags,
)
from news_agent.agents.ingestion.ingestion import IngestionAgent
from news_agent.agents.sender.abstract import AbstractSender
from news_agent.agents.sender.email_sender import EmailSenderAgent
from news_agent.agents.validator.deduplication_agent import DeduplicationAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Planner:
    """
    Workflow:
    1. Call IngestionAgent to get trending news items.
    2. Use DeduplicationAgent / DB to filter duplicates.
    3. Save new trends to the DB.
    4. Use SenderAgent to notify subscribers.
    """

    def __init__(
        self,
        config_path: str,
        session_id: str,
        db: SQLAlchemySubscriptionDB,
        ingestion_agent: Optional[IngestionAgent] = None,
        sender_agent: Optional[AbstractSender] = None,
        deduplication_agent: Optional[DeduplicationAgent] = None,
    ):
        self.config_path = config_path
        self.session_id = session_id
        self.db = db
        self.ingestion_agent = ingestion_agent
        self.sender_agent = sender_agent or EmailSenderAgent()
        self.deduplication_agent = deduplication_agent

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a single query/topic."""
        try:
            ingestion_results = await self.ingestion_agent.process_query(query)
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return {"error": str(e)}

        results = ingestion_results.get("results", [])
        if not results:
            logger.info("No results from ingestion.")
            return {"results": []}

        processed_items = []

        async with get_db() as db:  # SINGLE session context
            for item in results.news:
                topic = getattr(item, "topic", "").strip()
                summary = getattr(item, "summary", "").strip()
                link = getattr(item, "link", "").strip()
                tag_name = query

                if not topic or not link:
                    logger.warning(f"Skipping incomplete item: {item}")
                    continue

                # Deduplication check
                if await self.deduplication_agent.db_exists(topic, link):
                    logger.info(f"Duplicate skipped: {topic}")
                    continue

                # Check or create tag
                result = await db.execute(select(Tag).where(Tag.name == tag_name))
                tag_obj = result.scalar_one_or_none()
                if not tag_obj:
                    tag_obj = Tag(name=tag_name)
                    db.add(tag_obj)
                    await db.flush()

                # Create trend
                trend = Trend(topic=topic, summary=summary, url=link, notified=False)
                db.add(trend)
                await db.flush()  # ensure trend.id is populated

                # Insert into junction table directly
                stmt = trend_tags.insert().values(trend_id=trend.id, tag_id=tag_obj.id)
                await db.execute(stmt)

                processed_items.append(
                    {
                        "topic": topic,
                        "summary": summary,
                        "link": link,
                        "tags": [tag_name],
                    }
                )
                logger.info(f"New trend added with tag '{tag_name}': {topic}")

            await db.commit()  # commit everything at once

        # Send updates to subscribers
        send_results = await self.sender_agent.send_for_subscriptions()

        logger.info(f"Email send results: {send_results}")

        return {
            "results": f"Pipeline completed for query: {query}",
            "ingestion": processed_items,
            "sent_status": send_results,
        }

    async def automatic_agent_loop(self, interval_minutes: int = 60):
        """Continuously process all topics in the DB."""
        while True:
            try:
                logger.info("Starting automatic agent run...")
                topics = await self.db.get_all_topics()
                if not topics:
                    logger.info("No topics found. Skipping run.")
                else:
                    for topic in topics:
                        logger.info(f"Processing topic: {topic}")
                        await self.process_query(topic)
                logger.info("Automatic agent run completed.")
            except Exception as e:
                logger.error(f"Error during automatic agent run: {e}")
            await asyncio.sleep(interval_minutes * 60)
