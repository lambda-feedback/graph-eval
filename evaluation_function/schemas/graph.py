"""
Graph Structure Schemas

Core data structures for representing graphs: Nodes, Edges, and Graphs.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str = Field(..., description="Unique identifier for the node")
    label: Optional[str] = Field(None, description="Display label")
    x: Optional[float] = Field(None, description="X coordinate for visual display (not used in evaluation)")
    y: Optional[float] = Field(None, description="Y coordinate for visual display (not used in evaluation)")

    class Config:
        extra = "allow"


class Edge(BaseModel):
    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    weight: Optional[float] = Field(1.0, description="Edge weight")
    label: Optional[str] = Field(None, description="Display label")
    id: Optional[str] = Field(None, description="Unique edge identifier")

    class Config:
        extra = "allow"


class Graph(BaseModel):
    nodes: list[Node] = Field(..., description="List of nodes in the graph")
    edges: list[Edge] = Field(default_factory=list, description="List of edges")
    # These flags are NOT part of the student/teacher payload schema.
    # They are set exclusively from EvaluationParams by _apply_params_to_graph()
    # at evaluation time so that algorithm functions can read them.
    directed: bool = Field(False, description="Set from EvaluationParams.directed at evaluation time — do not include in response/answer payloads")
    weighted: bool = Field(False, description="Set from EvaluationParams.weighted at evaluation time — do not include in response/answer payloads")
    multigraph: bool = Field(False, description="Set from EvaluationParams.multigraph at evaluation time — do not include in response/answer payloads")

    class Config:
        extra = "allow"
