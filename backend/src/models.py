from pydantic import BaseModel
from typing import List, Dict, Any


class ProjectMetaData(BaseModel):
    project_id: str
    project_name: str
    created_at: str


class ProjectData(BaseModel):
    project_id: str
    project_name: str
    created_at: str
    chat_history: List[Dict]
    dataframe_snapshot: Dict  # 데이터프레임의 상태 스냅샷
    plots: List[Dict]


class Node(BaseModel):
    id: str
    label: str


class Edge(BaseModel):
    source: str
    target: str
    label: str


class DataFramePreview(BaseModel):
    columns: List[str]
    data: List[List[Any]]


class AgentThought(BaseModel):
    tool: str
    tool_input: str
    log: str


class AgentResponse(BaseModel):
    thoughts: List[AgentThought]
    final_answer: str


class ProjectStateResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    active_node_id: str | None
