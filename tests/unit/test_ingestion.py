from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest
from agents import SQLiteSession

from news_agent.agents.ingestion.abstract import AbstractIngestion
from news_agent.agents.ingestion.ingestion import IngestionAgent


@pytest.mark.asyncio
@patch("agents.Runner.run", new_callable=AsyncMock)
@patch(
    "news_agent.agents.ingestion.ingestion.AbstractIngestion.from_config",
    new_callable=AsyncMock,
)
async def test_query_mocked_by_ingestion_agent(mock_from_config, mock_run):

    # Autospec for ingestion
    mock_ingestion = create_autospec(AbstractIngestion, instance=True)
    mock_ingestion.process_query = AsyncMock(
        return_value={
            "results": [
                {
                    "topic": "Test News",
                    "summary": "This is a test summary.",
                    "link": "https://example.com/test",
                }
            ]
        }
    )
    mock_ingestion.get_mcp_servers.return_value = []

    mock_from_config.return_value = mock_ingestion

    # Fix Runner.run to return real data
    mock_run.return_value = AsyncMock()
    mock_run.return_value.final_output = [
        {
            "topic": "Test News",
            "summary": "This is a test summary.",
            "link": "https://example.com/test",
        }
    ]

    agent = IngestionAgent(
        config_path="src/news_agent/config/ingest_mcp_config.json",
        session_id=SQLiteSession("123"),
    )

    result = await agent.process_query("test query")

    assert result["results"][0]["topic"] == "Test News"
    assert "summary" in result["results"][0]
    assert "link" in result["results"][0]


@pytest.mark.asyncio
async def test_from_config_multiple_servers(tmp_path):
    import json

    # Fake config
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

    # Mocked handler instances
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

        # Assert both connects were called
        mock_firecrawl_instance.connect.assert_awaited_once()
        mock_serpapi_instance.connect.assert_awaited_once()

        # ingestion object has 2 handlers
        assert len(ingestion.handlers) == 2
