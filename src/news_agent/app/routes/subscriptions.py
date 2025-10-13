from fastapi import APIRouter, HTTPException

from news_agent.agents.db.sqlachemy_db import SQLAlchemySubscriptionDB
from news_agent.app.schemas import SubscribeRequest, UnsubscribeRequest

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

DB = SQLAlchemySubscriptionDB()


@router.post("/subscribe")
async def subscribe(req: SubscribeRequest):
    try:
        await DB.add_subscription(req.email, req.topics, req.notes)
        return {"message": "Subscription added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe")
async def unsubscribe(req: UnsubscribeRequest):
    try:
        await DB.remove_subscription(req.email)
        return {"message": "Unsubscribed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_subscriptions():
    try:
        subs = await DB.list_subscriptions()
        return {"subscriptions": subs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
