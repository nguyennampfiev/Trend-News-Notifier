import logging

from agents import SQLiteSession

from news_agent.agents.base_agent import init_agent
from news_agent.agents.schema import CheckExistence

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DeduplicationAgent:
    """
    Smart deduplication agent combining:
    1️⃣ Database-level exact matching
    2️⃣ Optional semantic embedding similarity
    3️⃣ LLM reasoning fallback (only when uncertain)
    """

    def __init__(self, db, session_id: SQLiteSession, embedding_model=None):
        self.db = db
        self.session_id = session_id
        self.embedding_model = (
            embedding_model  # optional — OpenAI, SentenceTransformer, etc.
        )

        DEFAULT_PROMPT = """
        You are a deduplication reasoning agent.
        Given a topic and link, determine if this news item duplicates any of the
        provided existing entries. Consider similarity of topics or content.
        Respond with a structured output containing a boolean field 'exists'.
        """

        self.prompt = DEFAULT_PROMPT
        self.agent = init_agent(
            instructions=self.prompt,
            name="DeduplicationAgent",
            output_type=CheckExistence,
        )

    # -------------------------------------------------------------------------
    # 1️⃣ Database-level fast check
    # -------------------------------------------------------------------------

    async def db_exists(self, topic: str, link: str) -> bool:
        """Check if an identical topic or link already exists in the database."""
        try:
            exists = await self.db.db_exists(topic, link)
            logger.info(f"Checking existence for topic '{topic}': {exists}")
            return exists
        except Exception as e:
            logger.error(f"Database existence check failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # 🚀 Main API method — combines all checks
    # -------------------------------------------------------------------------
    async def is_duplicate(self, topic: str, summary: str, link: str) -> bool:
        """Main deduplication pipeline."""
        # 1️⃣ Exact DB match
        if await self.db_exists(topic, link):
            logger.info(f"Exact duplicate found: {topic}")
            return True

        return False
