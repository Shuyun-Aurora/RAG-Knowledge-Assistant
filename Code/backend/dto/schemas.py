from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # 明确标记为可选


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


class DeleteDocumentResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    warning: Optional[str] = None
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    file_id: str
    filename: str
    course: str
    upload_time: Optional[str] = None
    size: Optional[int] = None
    status: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int

class StatisticsResponse(BaseModel):
    total_vectors: int
    total_files: int
    vector_sources: List[str]
    error: Optional[str] = None


class Node(BaseModel):
    id: int
    labels: List[str]
    properties: Dict[str, Any]


class Relationship(BaseModel):
    id: int
    type: str
    source: int
    target: int
    properties: Dict[str, Any]


class Graph(BaseModel):
    nodes: List[Node]
    relationships: List[Relationship]


class KnowledgeGraphResponse(BaseModel):
    knowledge_graph: Graph


class SearchKnowledgeGraphResponse(BaseModel):
    result: Graph


class NodeNeighborsResponse(BaseModel):
    neighbors: Graph


class ChatHistorySummary(BaseModel):
    session_id: str
    first_question: str
    created_at: datetime
    updated_at: datetime
    course_name: str | None = None
    message_count: int


class ChatHistorySummaryResponse(BaseModel):
    summaries: List[ChatHistorySummary]
    total_count: int


class AgentStyle(str, Enum):
    DEFAULT = "default"
    STRICT_TUTOR = "strict_tutor"
    FRIENDLY_PEER = "friendly_peer"

class AgentStyleConfig(BaseModel):
    style: AgentStyle
    name: str
    description: str
    system_prompt: str
    personality_traits: List[str]


class AgentStylesResponse(BaseModel):
    """获取所有可用agent风格的响应"""
    styles: List[AgentStyleConfig]
