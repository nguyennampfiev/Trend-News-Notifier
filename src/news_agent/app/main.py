# news_agent/app/main.py
import asyncio
import logging

from agents import SQLiteSession
from fastapi import FastAPI

from news_agent.agents.chat.chat_agent import ChatAgent
from news_agent.agents.planner.planner import PlannerAgent
from news_agent.app import state
from news_agent.app.routes import chat, subscriptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="News Agent Notifier")

# Register routers (chat router will check state.chat_ready_event)
app.include_router(subscriptions.router, prefix="/api/subscriptions")
app.include_router(chat.router, prefix="/api/chat")  # chat router defines /chat


async def init_chat_agent_background(config_path: str, session_id: SQLiteSession):
    """
    Initialize ChatAgent in background so startup doesn't block if MCP is slow or unavailable.
    Sets state.chat_agent and state.chat_ready_event when ready.
    """
    async with state.chat_init_lock:
        # If already initialized by another task, just return
        if state.chat_ready_event.is_set() and state.chat_agent is not None:
            logger.info("ChatAgent already initialized.")
            return

        try:
            logger.info("Background: initializing ChatAgent...")
            agent = await ChatAgent.create(config_path, session_id)
            state.chat_agent = agent
            state.chat_ready_event.set()
            logger.info("Background: ChatAgent initialized successfully.")
        except Exception as e:
            logger.exception("Background: failed to initialize ChatAgent: %s", e)
            # Do NOT set the event — leave it not set so routes know it's not ready.


@app.on_event("startup")
async def startup_event():
    logger.info("Starting application initialization...")

    # Start chat agent initialization in background (non-blocking)
    asyncio.create_task(
        init_chat_agent_background(
            config_path="src/news_agent/config/planner_config.json",
            session_id=SQLiteSession(session_id="user123"),
        )
    )

    # Initialize planner agent synchronously (it shouldn't block on MCP unless it does)
    try:
        logger.info("Initializing PlannerAgent...")
        state.planner_agent = PlannerAgent(
            "src/news_agent/config/planner_config.json",
            SQLiteSession(session_id="user123"),
            db=state.DB,
        )
        # start its background loop if PlannerAgent provides it
        if hasattr(state.planner_agent, "automatic_agent_loop"):
            loop = asyncio.get_event_loop()
            loop.create_task(state.planner_agent.automatic_agent_loop())
            logger.info("PlannerAgent background loop started.")
    except Exception as e:
        logger.exception("Failed to initialize PlannerAgent: %s", e)

    logger.info("Application startup tasks scheduled.")
