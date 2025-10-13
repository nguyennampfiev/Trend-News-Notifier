# news_agent/app/state.py
import asyncio
from typing import Optional

from news_agent.agents.chat.chat_agent import ChatAgent
from news_agent.agents.db.sqlachemy_db import SQLAlchemySubscriptionDB
from news_agent.agents.planner.planner import PlannerAgent

DB = SQLAlchemySubscriptionDB()
chat_agent: Optional[ChatAgent] = None
planner_agent: Optional[PlannerAgent] = None

# Event used to signal chat agent readiness
chat_ready_event: asyncio.Event = asyncio.Event()
# Optional lock to protect initialization
chat_init_lock: asyncio.Lock = asyncio.Lock()
