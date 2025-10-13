# news_agent/app/state.py
from typing import Optional

from news_agent.agents.chat.chat_agent import ChatAgent
from news_agent.agents.db.sqlachemy_db import SQLAlchemySubscriptionDB
from news_agent.agents.planner.planner import PlannerAgent

DB = SQLAlchemySubscriptionDB()
chat_agent: Optional[ChatAgent] = None
planner_agent: Optional[PlannerAgent] = None
