import asyncio

from news_agent.agents.db.sqlachemy_db import SQLAlchemySubscriptionDB
from news_agent.agents.ingestion.ingestion import IngestionAgent
from news_agent.agents.planner.planner import Planner
from news_agent.agents.sender.email_sender import EmailSenderAgent
from news_agent.agents.validator.deduplication_agent import DeduplicationAgent

DB: SQLAlchemySubscriptionDB | None = None
ingestion_agent: IngestionAgent | None = None
sender_agent: EmailSenderAgent | None = None
deduplication_agent: DeduplicationAgent | None = None
planner: Planner | None = None

# Event used to signal chat agent readiness
chat_ready_event: asyncio.Event = asyncio.Event()
# Optional lock to protect initialization
chat_init_lock: asyncio.Lock = asyncio.Lock()
