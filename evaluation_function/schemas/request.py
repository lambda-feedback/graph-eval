"""
Request/Response Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field

from .graph import Graph


class Response(BaseModel):
    graph: Optional[Graph] = Field(None, description="The student's graph")
    is_connected: Optional[bool] = None
    is_bipartite: Optional[bool] = None
    has_cycle: Optional[bool] = None
    is_colorable: Optional[bool] = None
    is_isomorphic: Optional[bool] = None
    coloring: Optional[dict[str, int]] = Field(None, description="Node coloring (node_id -> color)")

    class Config:
        extra = "allow"


class Answer(BaseModel):
    graph: Optional[Graph] = Field(None, description="The expected/correct graph")
    is_connected: Optional[bool] = None
    is_bipartite: Optional[bool] = None
    has_cycle: Optional[bool] = None
    is_colorable: Optional[bool] = None
    is_isomorphic: Optional[bool] = None
    num_colors: Optional[int] = Field(None, description="Number of colors for k-coloring")

    class Config:
        extra = "allow"
