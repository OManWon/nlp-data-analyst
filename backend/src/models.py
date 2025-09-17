from pydantic import BaseModel
from typing import List, Any

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
