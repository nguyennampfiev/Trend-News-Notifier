import asyncio
import logging
import os

from agents import SQLiteSession
from fastapi import FastAPI

from news_agent.agents.chat.chat_agent import ChatAgent
from news_agent.agents.db.sqlachemy_db import SQLAlchemySubscriptionDB
from news_agent.agents.ingestion.ingestion import IngestionAgent
from news_agent.agents.planner.planner import Planner
from news_agent.agents.sender.email_sender import EmailSenderAgent
from news_agent.agents.validator.deduplication_agent import DeduplicationAgent
from news_agent.app import state
from news_agent.app.routes import chat, subscriptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="News Agent Notifier")

# Routers
app.include_router(subscriptions.router, prefix="/api/subscribe")
app.include_router(chat.router, prefix="/api/chat")


@app.on_event("startup")
async def startup_event():
    logger.info("Starting application initialization...")

    # Initialize DB
    state.DB = SQLAlchemySubscriptionDB()
    await state.DB.init_db()
    logger.info("Database initialized successfully.")

    # Initialize session
    session_id = SQLiteSession(session_id="user123")

    # Initialize agents once
    state.ingestion_agent = IngestionAgent(
        "src/news_agent/config/ingest_mcp_config.json", session_id
    )
    await state.ingestion_agent._ensure_connected()
    logger.info("IngestionAgent initialized.")

    state.chat_agent = await ChatAgent.create(
        session_id,
        state.ingestion_agent,
    )
    state.chat_ready_event.set()

    state.sender_agent = EmailSenderAgent(
        state.DB, os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")
    )
    logger.info("SenderAgent initialized.")

    state.deduplication_agent = DeduplicationAgent(state.DB, session_id)
    logger.info("DeduplicationAgent initialized.")

    # Initialize Planner with already created agents
    state.planner = Planner(
        config_path="src/news_agent/config/planner_config.json",
        session_id=session_id,
        db=state.DB,
        ingestion_agent=state.ingestion_agent,
        sender_agent=state.sender_agent,
        deduplication_agent=state.deduplication_agent,
    )
    # Start background loop
    asyncio.create_task(state.planner.automatic_agent_loop())
    logger.info("PlannerAgent background loop started.")
