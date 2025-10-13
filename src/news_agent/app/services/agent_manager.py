import asyncio
import logging

from agents import SQLiteSession

from news_agent.agents.db.sqlachemy_db import SQLAlchemySubscriptionDB
from news_agent.agents.planner.planner import PlannerAgent

logger = logging.getLogger(__name__)
DB = SQLAlchemySubscriptionDB()
planner = PlannerAgent(
    "src/news_agent/config/planner_config.json", SQLiteSession(session_id="user123")
)


async def automatic_agent_loop(interval_minutes: int = 60):
    """Background task to run the agent periodically."""
    while True:
        try:
            logger.info("Starting automatic agent run...")
            topics = await DB.get_all_topics()
            if not topics:
                logger.info("No topics found in the database. Skipping this run.")
            else:
                for topic in topics:
                    logger.info(f"Processing topic: {topic}")
                    await planner.run(topic)
            logger.info("Automatic agent run completed.")
        except Exception as e:
            logger.error(f"Error during automatic agent run: {e}")
        await asyncio.sleep(interval_minutes * 60)


def start_automatic_agent(loop):
    loop.create_task(automatic_agent_loop())


def run_query_agent(query: str):

    return ""


def run_chat_agent(message: str):
    return ""


# def notify_subscribers(email: str, subject: str, body: str):
#     topic = trend.get("topic", "")
#     subscribers = DB.get_subscribers_for_topic(topic)
#     logger.info(f"Notifying {len(subscribers)} subscribers for topic '{topic}'")
