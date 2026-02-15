"""
Graph Structure Schemas

Core data structures for representing graphs: Nodes, Edges, and Graphs.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str = Field(..., description="Unique identifier for the node")
    label: Optional[str] = Field(None, description="Display label")

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
    directed: bool = Field(False, description="Whether the graph is directed")

    class Config:
        extra = "allow"
