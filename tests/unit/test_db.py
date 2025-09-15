import pytest

from news_agent.agents.db.trend import SQLiteTrendDB


@pytest.fixture
def db():
    test_db = SQLiteTrendDB(":memory:")  # Use in-memory database for testing
    yield test_db
    # No teardown needed for in-memory DB
    test_db.conn.close()


def test_save_and_get_unsent_trends(db):
    # Save  a trend
    db.save_trend(
        "Test Topic", "This is a summary.", "http://example.com", "Test Source"
    )

    # Retrieve unsent trends
    unsent_trends = db.get_unsent_trends()
    assert len(unsent_trends) == 1
    assert unsent_trends[0]["topic"] == "Test Topic"
    assert unsent_trends[0]["notified"] == 0
    assert unsent_trends[0]["summary"] == "This is a summary."
    assert unsent_trends[0]["url"] == "http://example.com"

    db.mark_as_sent(unsent_trends[0]["id"])
