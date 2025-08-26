import asyncio
import json

from agents import SQLiteSession
from fastapi import FastAPI
from pydantic import BaseModel

from news_agent.agents.planner.planner import PlannerAgent


class QueryRequest(BaseModel):
    query: str


app = FastAPI(title="News Agent Notifier")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ingresion")
async def ingresion(query: QueryRequest):
    agent_ingestion = PlannerAgent(
        config_path="src/news_agent/config/general_config.json",
        session_id=SQLiteSession("123"),
    )
    # agent_ingestion.load_config()
    query = query.query  # Extract the query string from the request body
    result = await agent_ingestion.process_query(query)

    return {"result": result}


# --- NEW: Automatic ingestion based on planner config ---
async def automatic_ingression():
    # Load planner config
    with open("src/news_agent/config/planner_config.json") as f:
        config = json.load(f)
    crawl_interval = config.get("crawl_interval_minutes", 30)
    session = SQLiteSession("auto")
    planner_agent = PlannerAgent(
        config_path="src/news_agent/config/general_config.json",
        session_id=session,
    )
    while True:
        # You can customize the query or fetch from a source
        query = "latest France news"
        await planner_agent.process_query(query)
        await asyncio.sleep(crawl_interval * 60)


@app.on_event("startup")
async def startup_event():
    # Run automatic ingestion in the background
    asyncio.create_task(automatic_ingression())
