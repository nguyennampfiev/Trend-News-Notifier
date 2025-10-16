import pytest
import pytest_asyncio


# -----------------------------
# MOCK Deduplication Agent
# -----------------------------
class MockDedupAgent:
    def __init__(self, db):
        self.db = db

    async def db_exists(self, topic, link):
        return await self.db.db_exists(topic, link)


@pytest_asyncio.fixture
def dedup_agent(db_instance):
    """Use the shared db_instance fixture."""
    return MockDedupAgent(db_instance)


# -----------------------------
# TESTS
# -----------------------------
@pytest.mark.asyncio
async def test_dedup_new_item(dedup_agent):
    exists = await dedup_agent.db_exists("New Topic", "https://example.com/new")
    assert exists is False


@pytest.mark.asyncio
async def test_dedup_existing_item(dedup_agent):
    db = dedup_agent.db
    await db.add_trend(
        topic="Existing Topic",
        summary="Existing summary",
        url="https://example.com/existing",
        tag="AI",
    )
    exists = await dedup_agent.db_exists(
        "Existing Topic", "https://example.com/existing"
    )
    assert exists is True


@pytest.mark.asyncio
async def test_dedup_similar_topic_different_link(dedup_agent):
    db = dedup_agent.db
    await db.add_trend(
        topic="AI News", summary="Summary", url="https://example.com/link1", tag="AI"
    )
    exists = await dedup_agent.db_exists("AI News", "https://example.com/link2")
    assert exists is False


@pytest.mark.asyncio
async def test_dedup_different_topic_same_link(dedup_agent):
    db = dedup_agent.db
    await db.add_trend(
        topic="First Topic",
        summary="Summary",
        url="https://example.com/shared",
        tag="AI",
    )
    exists = await dedup_agent.db_exists("Second Topic", "https://example.com/shared")
    assert exists is False


@pytest.mark.asyncio
async def test_dedup_batch_check(dedup_agent):
    db = dedup_agent.db
    await db.add_trend("Existing 1", "Summary 1", "https://example.com/1", "AI")
    await db.add_trend("Existing 2", "Summary 2", "https://example.com/2", "Tech")

    items_to_check = [
        ("Existing 1", "https://example.com/1"),
        ("New Item", "https://example.com/3"),
        ("Existing 2", "https://example.com/2"),
    ]

    results = []
    for topic, link in items_to_check:
        exists = await dedup_agent.db_exists(topic, link)
        results.append(exists)

    assert results == [True, False, True]
