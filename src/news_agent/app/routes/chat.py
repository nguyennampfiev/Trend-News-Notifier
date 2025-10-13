import logging

from fastapi import APIRouter, HTTPException

from news_agent.agents.schema import AskRequest
from news_agent.app import state

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/")
async def ask(req: AskRequest):
    """
    If chat agent is not ready, return 503 with friendly message.
    Once ready, forward to chat_agent.chat() and normalize output.
    """
    # If chat not initialized yet, return 503 (or a friendly "initializing" message)
    if not state.chat_ready_event.is_set() or state.chat_agent is None:
        logger.warning("ChatAgent not initialized - returning 503")
        raise HTTPException(
            status_code=503, detail="ChatAgent is initializing, try again in a moment"
        )

    # agent is ready
    chat_agent = state.chat_agent
    if chat_agent is None:
        logger.warning("ChatAgent not initialized - returning 503")
        raise HTTPException(status_code=503, detail="ChatAgent initializing")

    logger.info(f"Received message: {req.message}")
    result = await chat_agent.chat(req.message)
    logger.info(f"ChatAgent result: {result}")

    # ✅ Normalize backend output to what frontend expects
    if isinstance(result, dict) and "news" in result and result["news"]:
        return {"news": result["news"], "response": None}

    return {"response": result.get("response", ""), "news": None}
