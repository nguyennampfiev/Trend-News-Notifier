# Trend-News-Notifier


Trend-News-Notifier is a multi-agent system designed to automatically fetch, process, and notify users about trending news from the internet. It leverages LLM-powered agents, custom tools, and guardrails to ensure relevant, accurate, and well-formatted news delivery.

> **Note:** This project uses [openai-agents](https://openai.github.io/openai-agents-python/) with the open-source `gpt-oss-20b` model for agent orchestration and language understanding.


## Features

- **Multi-Agent Architecture:** Modular agents for ingestion, planning, and sending notifications.
- **News Ingestion:** Fetches hot/trending news using SerpAPI, and Firecrawl.
- **Custom Tools:** Easily extendable with new search or processing tools.
- **Guardrails:** Ensures output format and content quality.
- **Async Processing:** Efficient, scalable news fetching and processing.
- **Email Notification:** Sends news summaries via email.
- **Configurable:** Easily customize sources, output formats, and notification settings.

## Quick Start

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Set up environment variables:**
   - Copy `.env.example` to `.env` and add your API keys (e.g., `SERPAPI_KEY`).

3. **Run the main application:**
   ```bash
   poetry run python src/news_agent/app/main.py
   ```

4. **Run tests:**
   ```bash
   poetry run pytest
   ```

## Configuration

- **News sources and agent settings:**
  Edit `src/news_agent/config/ingest_mcp_config.json` and other config files to customize sources, agent behavior, and notification details.

## How It Works

- **Ingestion Agent:** Loads MCP servers and tools, fetches news from multiple sources.
- **Planner Agent:** Plans and organizes news delivery.
- **Sender Agent:** Sends notifications (e.g., email) to users.
- **Guardrails:** Validate and format output before sending.

## Contributing

1. Fork the repo and clone your fork.
2. Create a new branch for your feature or fix.
3. Make changes and add tests.
4. Run `pre-commit` hooks and ensure all tests pass.
5. Submit a pull request.

## Planned Features

- **Duplicate News Validation:**
  Future versions will include logic to detect and filter out duplicate news articles, ensuring users receive unique and relevant updates.

- **Personalized News Delivery:**
  Users will be able to set their preferred news categories. The system will send notifications tailored to each user's interests.

## License

MIT

---
