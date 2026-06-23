from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatAskRequest(BaseModel):
    session_id: int | None = None
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    citations: str | None
    created_at: datetime


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime


class ChatAskResponse(BaseModel):
    session_id: int
    assistant_message: ChatMessageOut
