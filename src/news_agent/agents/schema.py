from typing import List

from pydantic import BaseModel


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
