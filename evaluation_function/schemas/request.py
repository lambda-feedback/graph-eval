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
    is_planar: Optional[bool] = None
    is_tree: Optional[bool] = None
    is_forest: Optional[bool] = None
    is_dag: Optional[bool] = None
    is_eulerian: Optional[bool] = None
    is_semi_eulerian: Optional[bool] = None
    is_regular: Optional[bool] = None
    is_complete: Optional[bool] = None
    degree_sequence: Optional[list[int]] = Field(None, description="Degree sequence (descending)")
    has_hamiltonian_path: Optional[bool] = None
    has_hamiltonian_cycle: Optional[bool] = None
    clique_number: Optional[int] = None

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
    is_planar: Optional[bool] = None
    is_tree: Optional[bool] = None
    is_forest: Optional[bool] = None
    is_dag: Optional[bool] = None
    is_eulerian: Optional[bool] = None
    is_semi_eulerian: Optional[bool] = None
    is_regular: Optional[bool] = None
    is_complete: Optional[bool] = None
    degree_sequence: Optional[list[int]] = Field(None, description="Degree sequence (descending)")
    has_hamiltonian_path: Optional[bool] = None
    has_hamiltonian_cycle: Optional[bool] = None
    clique_number: Optional[int] = None

    class Config:
        extra = "allow"
