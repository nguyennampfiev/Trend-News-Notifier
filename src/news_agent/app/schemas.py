from typing import List, Optional

from pydantic import BaseModel, EmailStr


class QueryRequest(BaseModel):
    query: str


class Chat(BaseModel):
    message: str


class SubscribeRequest(BaseModel):
    email: EmailStr
    topics: List[str]
    notes: Optional[str] = None


class UnsubscribeRequest(BaseModel):
    email: EmailStr
