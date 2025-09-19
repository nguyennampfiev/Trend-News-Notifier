import asyncio
import json
from contextlib import asynccontextmanager

from agents import SQLiteSession
from fastapi import FastAPI
from pydantic import BaseModel

from news_agent.agents.chat.chat_agent import ChatAgent
from news_agent.agents.db.subscriptions import SQLiteSubcriptionDB
from news_agent.agents.planner.planner import PlannerAgent


class QueryRequest(BaseModel):
    query: str


class SubscriptionRequest(BaseModel):
    email: str
    topics: list[str]


class Chat(BaseModel):
    message: str


# Global agent instance
chat_agent_instance = None
planner_agent_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chat_agent_instance
    print("🚀 Initializing ChatAgent...")

    chat_agent_instance = await ChatAgent.create(
        config_path="src/news_agent/config/general_config.json",
        session_id=SQLiteSession("main_session"),
    )

    print("✅ ChatAgent ready!")
    yield
    print("🔄 Shutting down ChatAgent...")


app = FastAPI(title="News Agent Notifier", lifespan=lifespan)

# app = FastAPI(t)
db = SQLiteSubcriptionDB("subscriptions.db")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/subscribe")
async def subscribe(req: SubscriptionRequest):
    print("Received subscription request:", req)
    for topic in req.topics:
        db.add_subscription(req.email, [topic])
        print(f"Subscribed {req.email} to topic: {topic}")
    return {"status": "subcribe ok", "topics": req.topics}


@app.post("/api/chat")
async def chat(message: Chat):
    print(message)
    response = await chat_agent_instance.chat(message.message)
    return response


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
        subscriptions = db.get_all_subscriptions()
        if subscriptions:
            for sub in subscriptions:
                email = sub["email"]
                topics_str = sub["topics"]  # comma-separated string
                topics = topics_str.split(",")  # convert back to list
                for topic in topics:
                    print(f"Running for topic: {topic}")
                    try:
                        await planner_agent.process_query_by_user(topic, email)
                    except Exception as e:
                        print(f"Error processing topic : {topic}: {e}")

        await asyncio.sleep(crawl_interval * 6000)


# @app.on_event("startup")
# async def startup_event():
#     # Run automatic ingestion in the background
#     asyncio.create_task(automatic_ingression())
