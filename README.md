# Trend-News-Notifier

Trend-News-Notifier is a multi-agent system designed to automatically fetch, process, and notify users about trending news from the internet. It leverages LLM-powered agents, custom tools, and guardrails to ensure relevant, accurate, and well-formatted news delivery.

> Note: This project uses openai-agents (https://openai.github.io/openai-agents-python/) with the open-source `gpt-oss-20b` model for agent orchestration and language understanding.

## Features

- Multi-Agent Architecture: Modular agents for ingestion, planning, and sending notifications.
- News Ingestion: Fetches hot/trending news using SerpAPI, and Firecrawl.
- Custom Tools: Easily extendable with new search or processing tools.
- Guardrails: Ensures output format and content quality.
- Async Processing: Efficient, scalable news fetching and processing.
- Email Notification: Sends news summaries via email.
- Configurable: Easily customize sources, output formats, and notification settings.
- Observability: Metrics collection via OpenTelemetry, Prometheus scraping, and Grafana dashboards.

## Quick Start

1. Install dependencies:
   poetry install

2. Set up environment variables:
   Copy `.env.example` to `.env` and add your API keys (e.g., `SERPAPI_KEY`).

3. Run the main components:

   Backend API:
   poetry run uvicorn news_agent.app.main:app --reload --port 8002

   Frontend (if applicable):
   npm run dev

   VLLM Serve (if used):
   vllm serve openai/gpt-oss-20b

   OpenTelemetry Collector:
   ./otelcol --config src/news_agent/observability/otel-collector-config.yaml

   Prometheus:
   ./prometheus --config.file=prometheus.yml
   (Default Prometheus port: 9090)

   Grafana:
   GF_SERVER_HTTP_PORT=8080 ./grafana-12.2.0/bin/grafana-server
   (Access at http://localhost:8080 and configure Prometheus as data source: http://localhost:9090)

4. Run tests:
   poetry run pytest

## Configuration

- News sources and agent settings:
  Edit `src/news_agent/config/ingest_mcp_config.json` and other config files to customize sources, agent behavior, and notification details.

- Observability:
  - Metrics exported via OpenTelemetry Collector HTTP endpoint (localhost:4318).
  - Prometheus scrapes OTEL metrics on port 9464.
  - Grafana visualizes metrics from Prometheus.

## How It Works

- Ingestion Agent: Loads MCP servers and tools, fetches news from multiple sources.
- Planner Agent: Plans and organizes news delivery.
- Sender Agent: Sends notifications (e.g., email) to users.
- Telemetry & Metrics: Backend records CPU, RAM, and request latency, collected by OpenTelemetry, scraped by Prometheus, visualized in Grafana.
- Guardrails: Validate and format output before sending.

## Contributing

1. Fork the repo and clone your fork.
2. Create a new branch for your feature or fix.
3. Make changes and add tests.
4. Run pre-commit hooks and ensure all tests pass.
5. Submit a pull request.

## Planned Features

- Duplicate News Validation: Detect and filter duplicate news articles.
- Personalized News Delivery: Users can set preferred news categories for tailored notifications.

## License

MIT
