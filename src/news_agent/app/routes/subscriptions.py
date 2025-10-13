import logging

from fastapi import APIRouter, HTTPException, Request

from news_agent.app import state
from news_agent.app.schemas import SubscribeRequest, UnsubscribeRequest

DB = state.DB
router = APIRouter()

# Configure logger
logger = logging.getLogger("subscription_router")
logger.setLevel(logging.INFO)


@router.post("")
async def subscribe(req: SubscribeRequest, request: Request):
    logger.info(
        f"Incoming subscription request from {request.client.host}: {req.json()}"
    )
    try:
        subscription_data = await DB.add_subscription(req.email, req.topics, req.notes)
        return {
            "message": "Subscription added successfully",
            **subscription_data,  # now safe: only primitive types
        }
    except Exception as e:
        logger.exception("Failed to add subscription: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe")
async def unsubscribe(req: UnsubscribeRequest, request: Request):
    logger.info(
        f"Incoming unsubscribe request from {request.client.host}: {req.json()}"
    )
    try:
        result = await DB.remove_subscription(req.email)
        logger.info(f"Unsubscribed successfully: {req.email}")
        return {"message": "Unsubscribed successfully", "details": result}
    except Exception as e:
        logger.error(f"Failed to unsubscribe: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to unsubscribe: {str(e)}")


@router.get("/getsubscriptions")
async def list_subscriptions(request: Request):
    logger.info(f"Listing subscriptions requested from {request.client.host}")
    try:
        subs = await DB.list_subscriptions()
        logger.info(f"Retrieved {len(subs)} subscriptions")
        return {"subscriptions": subs}
    except Exception as e:
        logger.error(f"Failed to list subscriptions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to list subscriptions: {str(e)}"
        )
