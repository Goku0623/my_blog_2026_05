from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AssistantHistoryMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, max_length=4000, description="消息内容")


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="用户输入")
    session_id: Optional[str] = Field(default=None, max_length=128, description="会话 ID")
    history: List[AssistantHistoryMessage] = Field(default_factory=list, description="历史消息")


class AssistantChatResponse(BaseModel):
    reply: str = Field(..., description="助手回复")
    session_id: Optional[str] = Field(default=None, description="会话 ID")
