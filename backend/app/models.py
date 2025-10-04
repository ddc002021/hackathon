from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RepoUploadRequest(BaseModel):
    github_url: Optional[str] = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    intent: Optional[Dict[str, Any]] = None  # Made optional for backward compatibility
    highlighted_nodes: List[str]
    query_type: Optional[str] = None  # NEW: Type of graph query (path, dependency, gap, etc.)
    graph_evidence: Optional[Dict[str, Any]] = None  # NEW: Raw graph analysis results
    paths: Optional[List[Dict[str, Any]]] = None  # NEW: Paths found in graph

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]

class FeatureDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    files: List[str]
    functions: List[Dict[str, Any]]

