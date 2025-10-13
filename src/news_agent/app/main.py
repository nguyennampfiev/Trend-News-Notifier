import asyncio
import logging

from agents import SQLiteSession
from fastapi import FastAPI

from news_agent.agents.chat.chat_agent import ChatAgent
from news_agent.agents.planner.planner import PlannerAgent
from news_agent.app.routes import chat, subscriptions
from news_agent.app.state import DB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="News Agent Notifier")

app.include_router(subscriptions.router, prefix="/api/subscriptions")
app.include_router(chat.router, prefix="/api/chat")


@app.on_event("startup")
async def startup_event():
    global chat_agent, planner_agent

    logger.info("Initializing ChatAgent...")
    chat_agent = await ChatAgent.create(
        "src/news_agent/config/planner_config.json", SQLiteSession(session_id="user123")
    )
    logger.info("ChatAgent initialized.")

    logger.info("Initializing PlannerAgent...")
    planner_agent = PlannerAgent(
        "src/news_agent/config/planner_config.json",
        SQLiteSession(session_id="user123"),
        db=DB,
    )

    logger.info("Starting PlannerAgent automatic loop...")
    loop = asyncio.get_event_loop()
    loop.create_task(planner_agent.automatic_agent_loop())
