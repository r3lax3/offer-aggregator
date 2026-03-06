from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MessageSource(StrEnum):
    TELEGRAM = "telegram"
    REDDIT = "reddit"


class RawMessage(BaseModel):
    source: MessageSource
    source_id: str
    chat_id: str
    chat_title: str
    author: str = ""
    text: str
    url: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: list[str] = Field(default_factory=list)


class FilteredMessage(BaseModel):
    raw: RawMessage
    confidence: str = ""
    matched_keywords: list[str] = Field(default_factory=list)
