from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


class ToolCallTrace(BaseModel):
    tool: str
    arguments: dict
    result: dict


class ChatResponse(BaseModel):
    type: str                      # "answer" | "clarification" | "unsupported"
    message: str
    tool_calls: list[ToolCallTrace] = []
