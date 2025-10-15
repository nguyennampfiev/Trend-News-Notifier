from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents import SQLiteSession

from news_agent.agents.ingestion.abstract import AbstractIngestion
from news_agent.agents.ingestion.ingestion import IngestionAgent
from news_agent.agents.schema import NewsItem, NewsOutput


@pytest.mark.asyncio
@patch("agents.Runner.run", new_callable=AsyncMock)
@patch(
    "news_agent.agents.ingestion.ingestion.AbstractIngestion.from_config",
    new_callable=AsyncMock,
)
async def test_query_mocked_by_ingestion_agent(mock_from_config, mock_run):
    """
    Test that IngestionAgent.process_query correctly returns mocked news items.
    """

    # Create mock NewsItem and NewsOutput objects
    mock_news_item = NewsItem(
        topic="Test News",
        summary="This is a test summary.",
        link="https://example.com/test",
    )
    mock_news_output = NewsOutput(news=[mock_news_item])

    # Create a mock result object that has a final_output attribute
    mock_result = MagicMock()
    mock_result.final_output = mock_news_output

    # Set up the return value for Runner.run
    mock_run.return_value = mock_result

    # Create a mock ingestion instance
    mock_agent = AsyncMock()

    # from_config returns the mock ingestion instance
    mock_from_config.return_value = mock_agent

    # Create the agent
    agent = IngestionAgent(
        config_path="src/news_agent/config/ingest_mcp_config.json",
        session_id=SQLiteSession("123"),
    )

    # Replace the agent's internal agent with the mock
    agent.agent = mock_agent

    # Call process_query
    result = await agent.process_query("test query")

    # Assertions
    assert "results" in result
    assert isinstance(result["results"], NewsOutput)
    assert len(result["results"].news) == 1
    assert result["results"].news[0].topic == "Test News"
    assert result["results"].news[0].summary == "This is a test summary."
    assert result["results"].news[0].link == "https://example.com/test"


@pytest.mark.asyncio
async def test_from_config_multiple_servers(tmp_path):
    """
    Test AbstractIngestion.from_config with multiple mocked MCP servers.
    """

    import json

    # Fake configuration with two MCP servers
    fake_config = {
        "mcp": {
            "servers": {
                "serpapisearch": {
                    "command": "python",
                    "args": [
                        "src/news_agent/agents/ingestion/serpapi_search_mcp_server.py"
                    ],
                },
                "firecrawl": {
                    "command": "npx",
                    "args": ["-y", "firecrawl-mcp"],
                    "env": {"FIRECRAWL_API_KEY": "fc-xx"},
                },
            }
        }
    }

    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(fake_config, f)

    # Mock handler instances with async connect
    mock_firecrawl_instance = AsyncMock()
    mock_firecrawl_instance.connect = AsyncMock()
    mock_firecrawl_instance.get_mcp_server = MagicMock()

    mock_serpapi_instance = AsyncMock()
    mock_serpapi_instance.connect = AsyncMock()
    mock_serpapi_instance.get_mcp_server = MagicMock()

    # Patch both handler classes at once
    with patch.multiple(
        "news_agent.agents.ingestion.abstract",
        FirecrawlHandler=MagicMock(return_value=mock_firecrawl_instance),
        SerpAPISearchHandler=MagicMock(return_value=mock_serpapi_instance),
    ):
        ingestion = await AbstractIngestion.from_config(str(config_path))

        # Assert both connect methods were awaited
        mock_firecrawl_instance.connect.assert_awaited_once()
        mock_serpapi_instance.connect.assert_awaited_once()

        # Ingestion object should have 2 handlers
        assert len(ingestion.handlers) == 2
