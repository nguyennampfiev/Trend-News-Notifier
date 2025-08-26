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
