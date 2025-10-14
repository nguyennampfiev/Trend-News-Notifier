from typing import List, Optional

from pydantic import BaseModel, EmailStr


class MessageOutput(BaseModel):
    response: str


class NewsItem(BaseModel):
    topic: str
    summary: str
    link: str


class NewsOutput(BaseModel):
    news: List[NewsItem]


class CheckExistence(BaseModel):
    exists: bool


class AskRequest(BaseModel):
    message: str
    topics: list[str] = []


class ChatOutput(BaseModel):
    response: str


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
