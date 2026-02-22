"""
Result Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class ConnectivityResult(BaseModel):
    is_connected: bool = Field(..., description="Whether graph is connected")
    num_components: int = Field(1, description="Number of connected components")
    components: Optional[list[list[str]]] = Field(None, description="The connected components")
    connectivity_type: Optional[str] = Field(None, description="Type of connectivity checked")


class BipartiteResult(BaseModel):
    is_bipartite: bool = Field(..., description="Whether graph is bipartite")
    partitions: Optional[list[list[str]]] = Field(None, description="The two partitions")
    odd_cycle: Optional[list[str]] = Field(None, description="Odd cycle if not bipartite")


class CycleResult(BaseModel):
    has_cycle: bool = Field(..., description="Whether graph contains a cycle")
    cycle: Optional[list[str]] = Field(None, description="A cycle found (if any)")


class ColoringResult(BaseModel):
    is_colorable: bool = Field(..., description="Whether graph is n-colorable")
    num_colors: Optional[int] = Field(None, description="Number of colors tested")
    coloring: Optional[dict[str, int]] = Field(None, description="A valid coloring (if found)")


class IsomorphismResult(BaseModel):
    is_isomorphic: bool = Field(..., description="Whether the two graphs are isomorphic")
    node_mapping: Optional[dict[str, str]] = Field(None, description="Node mapping if isomorphic")
