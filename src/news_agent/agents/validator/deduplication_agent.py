import logging

# from typing import Dict
from agents import Runner, SQLiteSession

from news_agent.agents.base_agent import init_agent
from news_agent.agents.schema import CheckExistence

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DeduplicationAgent:
    def __init__(self, db, session_id: SQLiteSession):
        self.db = db
        DEFAULT_PROMPT = """
        You are a deduplication agent.
        Given a news topic and link, determine if this news item is a duplicate of any existing
        entries in the database based on the topic and URL.
        Return True if it is a duplicate, otherwise return False.
        """
        # self.session_id = SQLiteSession("123")
        self.promt = DEFAULT_PROMPT
        self.agent = init_agent(
            self.promt,
            mcp_servers=None,
            name="DeduplicationAgent",
            output_type=CheckExistence,
        )

    async def is_duplicate(self, topic, summary, link) -> bool:
        # Load existing entries from the database
        existing_entries = self.db.get_all_entries()
        query = f"Is the following news item a duplicate of any existing entries? Topic: {topic}, Summary: {summary}, Link: {link}. Existing entries: {existing_entries}"
        result = await Runner.run(self.agent, query)
        # Using as exisiting_entries to
        try:
            if result.final_output.exists:
                logger.info(f"Duplicate found for topic: {topic}, link: {link}")
                return True
            else:
                logger.info(f"Can not check topic: {topic}, link: {link}, skipping.")
                return False

        except Exception as e:
            logger.error(
                f"Error checking duplicate for topic: {topic}, link: {link}: {e}"
            )
            return False
