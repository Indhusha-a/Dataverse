from fastapi import APIRouter

from app.router import handle_question
from app.schemas import ChatRequest, ChatResponse, ToolCallTrace

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = [{"role": h.role, "content": h.content} for h in req.history]
    result = handle_question(req.question, history)
    return ChatResponse(
        type=result["type"],
        message=result["message"],
        tool_calls=[ToolCallTrace(**tc) for tc in result.get("tool_calls", [])],
    )
