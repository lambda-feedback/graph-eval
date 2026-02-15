"""
Evaluation Parameter Schemas
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field

from .evaluation_types import EvaluationType


class ConnectivityParams(BaseModel):
    check_type: Literal["connected", "strongly_connected", "weakly_connected"] = Field(
        "connected",
        description="Type of connectivity check",
    )


class BipartiteParams(BaseModel):
    return_partitions: bool = Field(False, description="Whether to return the two partitions")
    return_odd_cycle: bool = Field(False, description="Whether to return an odd cycle if not bipartite")


class GraphColoringParams(BaseModel):
    num_colors: Optional[int] = Field(None, description="Number of colors (k for k-coloring)")


class CycleDetectionParams(BaseModel):
    pass


class IsomorphismParams(BaseModel):
    pass


class EvaluationParams(BaseModel):
    evaluation_type: EvaluationType = Field(..., description="The type of evaluation to perform")

    connectivity: Optional[ConnectivityParams] = None
    bipartite: Optional[BipartiteParams] = None
    graph_coloring: Optional[GraphColoringParams] = None
    cycle_detection: Optional[CycleDetectionParams] = None
    isomorphism: Optional[IsomorphismParams] = None

    class Config:
        extra = "allow"
