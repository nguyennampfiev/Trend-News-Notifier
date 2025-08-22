from agents import SQLiteSession
from fastapi import FastAPI
from pydantic import BaseModel

from src.news_agent.agents.ingestion.ingestion import IngestionAgent


class QueryRequest(BaseModel):
    query: str


app = FastAPI(title="News Agent Notifier")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ingresion")
async def ingresion(query: QueryRequest):
    agent_ingestion = IngestionAgent(
        config_path="src/news_agent/config/mcpservers_config.json",
        session_id=SQLiteSession("123"),
    )
    query = query.query  # Extract the query string from the request body
    result = await agent_ingestion.process_query(query)

    return {"result": result}
