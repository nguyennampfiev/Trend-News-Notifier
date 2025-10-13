import logging

from fastapi import APIRouter

from news_agent.agents.schema import AskRequest
from news_agent.app import state

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/")
async def ask(req: AskRequest):
    chat_agent = state.chat_agent
    if chat_agent is None:
        logger.warning("ChatAgent not initialized")
        return {"type": "error", "message": "ChatAgent not initialized", "news": None}

    logger.info("Received message: %s", req.message)
    result = await chat_agent.chat(req.message)
    logger.info("ChatAgent response: %s", result)

    if "news" in result and result["news"]:
        return {"type": "news", "news": result["news"], "message": None}
    else:
        return {"type": "chat", "message": result.get("response", ""), "news": None}
