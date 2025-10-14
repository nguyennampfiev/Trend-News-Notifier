# tests/test_planner_async.py
import logging

import pytest
from sqlalchemy import select

from news_agent.agents.db.sqlachemy_db import (
    AsyncSessionLocal,
    SQLAlchemySubscriptionDB,
    Tag,
    Trend,
)

# -----------------------------
# FIXTURES
# -----------------------------


@pytest.fixture(scope="session")
async def db():
    """
    Async in-memory DB for testing.
    """
    test_db = SQLAlchemySubscriptionDB()
    await test_db.init_db()
    yield test_db
    await test_db.engine.dispose()


# Mock Ingestion
class MockIngestionAgent:
    async def process_query(self, query):
        return {
            "results": {
                "news": [
                    type(
                        "NewsItem",
                        (),
                        {
                            "topic": f"{query} news 1",
                            "summary": "Summary 1",
                            "link": "http://link1.com",
                        },
                    )(),
                    type(
                        "NewsItem",
                        (),
                        {
                            "topic": f"{query} news 2",
                            "summary": "Summary 2",
                            "link": "http://link2.com",
                        },
                    )(),
                ]
            }
        }


# Mock Sender
class MockSenderAgent:
    async def send_for_subscriptions(self):
        logging.info("Mock sending emails...")
        return {"sent_count": 2, "failed_count": 0}


# Mock Deduplication
class MockDedupAgent:
    async def db_exists(self, topic, link):
        return False


# -----------------------------
# MOCK PLANNER
# -----------------------------
class MockPlanner:
    def __init__(self, db):
        self.db = db
        self.ingestion_agent = MockIngestionAgent()
        self.sender_agent = MockSenderAgent()
        self.dedup_agent = MockDedupAgent()

    async def process_query(self, query):
        ingestion_results = await self.ingestion_agent.process_query(query)
        processed_items = []

        async with AsyncSessionLocal() as session:
            for item in ingestion_results["results"]["news"]:
                topic = item.topic
                summary = item.summary
                link = item.link

                if await self.dedup_agent.db_exists(topic, link):
                    continue

                # Save trend
                trend = Trend(topic=topic, summary=summary, url=link, notified=False)
                session.add(trend)

                # Attach tag
                result = await session.execute(select(Tag).where(Tag.name == query))
                tag_obj = result.scalar_one_or_none()
                if not tag_obj:
                    tag_obj = Tag(name=query)
                    session.add(tag_obj)
                    await session.flush()
                trend.tags.append(tag_obj)

                processed_items.append(topic)

            await session.commit()

        await self.sender_agent.send_for_subscriptions()
        return processed_items


# -----------------------------
# TEST CASES
# -----------------------------
@pytest.mark.asyncio
async def test_pipeline(db: SQLAlchemySubscriptionDB):
    planner = MockPlanner(db)
    query = "AI"
    results = await planner.process_query(query)

    assert len(results) == 2  # two news items
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Trend).join(Trend.tags).where(Tag.name == query)
        )
        trends = result.scalars().all()
    assert len(trends) == 2
    for trend in trends:
        assert trend.notified is False
        assert trend.topic in results


@pytest.mark.asyncio
async def test_deduplication(db: SQLAlchemySubscriptionDB):
    planner = MockPlanner(db)
    query = "Tech"

    # Add a trend manually to simulate existing data
    await db.add_trend("Tech news 1", "Summary 1", "http://link1.com", query)

    # Override dedup agent to return True for first news
    class DedupAgentOverride:
        async def db_exists(self, topic, link):
            return topic == "Tech news 1"

    planner.dedup_agent = DedupAgentOverride()
    results = await planner.process_query(query)
    assert "Tech news 1" not in results  # skipped due to duplicate
    assert "Tech news 2" in results
