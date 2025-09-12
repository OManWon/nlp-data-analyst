
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any

from ..services import state, mlflow_svc
from ..services.agent_svc import run_agent

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    project_id: str
    q: str
    chat_history: List[Any] = []

@router.post("/chat")
def chat(req: ChatRequest):
    """
    사용자 질의와 채팅 기록을 받아 AI 에이전트를 실행하고 결과를 반환합니다.
    """
    pid = req.project_id
    q = req.q
    chat_history = req.chat_history

    if not pid or not state.has_project(pid):
        raise HTTPException(status_code=400, detail="A valid project_id is required.")
    if not q:
        raise HTTPException(status_code=400, detail="A query is required.")

    try:
        result = run_agent(pid, q, chat_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat execution failed: {e}")

@router.get("/project/{pid}/chat/history")
def get_chat_history(pid: str):
    """프로젝트의 가장 최근 채팅 기록을 반환합니다."""
    if not state.has_project(pid):
        raise HTTPException(status_code=404, detail="Project not found")

    latest_run_id = mlflow_svc.get_latest_run_id(pid)
    if not latest_run_id:
        return []

    history = mlflow_svc.load_chat_history(latest_run_id)
    return history
