import logging

import numpy as np
from agents import Runner, SQLiteSession

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
        """Check if an identical topic or link already exists."""
        try:
            async with self.db.async_session() as session:
                result = await session.execute(
                    self.db.select_trend_by_topic_or_link(topic, link)
                )
                exists = result.scalar_one_or_none() is not None
                return exists
        except Exception as e:
            logger.error(f"Database existence check failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # 2️⃣ Semantic embedding similarity check (optional)
    # -------------------------------------------------------------------------
    async def semantic_exists(self, topic: str, summary: str) -> bool:
        """Compute cosine similarity between new topic and stored embeddings."""
        if not self.embedding_model or not hasattr(self.db, "get_all_embeddings"):
            return False

        try:
            # Generate new embedding
            new_vec = np.array(self.embedding_model.embed([f"{topic} {summary}"])[0])

            # Fetch existing entries with embeddings
            entries = await self.db.get_all_embeddings()
            if not entries:
                return False

            similarities = []
            for _, existing_vec in entries:
                existing_vec = np.array(existing_vec)
                sim = np.dot(new_vec, existing_vec) / (
                    np.linalg.norm(new_vec) * np.linalg.norm(existing_vec)
                )
                similarities.append(sim)

            if similarities and max(similarities) > 0.9:
                logger.info("Semantic duplicate detected (cosine similarity > 0.9)")
                return True
            return False

        except Exception as e:
            logger.error(f"Semantic deduplication failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # 3️⃣ LLM fallback reasoning
    # -------------------------------------------------------------------------
    async def llm_exists(self, topic: str, summary: str, link: str) -> bool:
        """Ask LLM to decide if this is a duplicate."""
        try:
            existing_titles = await self.db.get_recent_topics(limit=10)
            query = (
                f"Topic: {topic}\nSummary: {summary}\nLink: {link}\n\n"
                f"Existing recent topics:\n{existing_titles}\n\n"
                f"Is this new item a duplicate of any existing ones?"
            )
            result = await Runner.run(self.agent, query)
            return getattr(result.final_output, "exists", False)
        except Exception as e:
            logger.error(f"LLM duplicate check failed: {e}")
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

        # 2️⃣ Semantic similarity (optional)
        if await self.semantic_exists(topic, summary):
            logger.info(f"Semantic duplicate found for: {topic}")
            return True

        # 3️⃣ LLM fallback reasoning
        if await self.llm_exists(topic, summary, link):
            logger.info(f"LLM confirmed duplicate for: {topic}")
            return True

        logger.info(f"No duplicate found for: {topic}")
        return False
