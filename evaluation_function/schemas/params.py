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


class MaxFlowParams(BaseModel):
    pass


class BipartiteMatchingParams(BaseModel):
    pass


class ComponentParams(BaseModel):
    pass


class ArticulationParams(BaseModel):
    pass


class DegreeSequenceParams(BaseModel):
    pass


class CliqueParams(BaseModel):
    pass


class IndependentSetParams(BaseModel):
    pass


class VertexCoverParams(BaseModel):
    pass


class TopologicalSortParams(BaseModel):
    pass


class TraversalParams(BaseModel):
    pass


class EvaluationParams(BaseModel):
    evaluation_type: EvaluationType = Field(..., description="The type of evaluation to perform")

    # Graph structure flags — sourced from params, not from the response/answer graph payload
    directed: bool = Field(False, description="Whether the graph is directed")
    weighted: bool = Field(False, description="Whether the graph is weighted")
    multigraph: bool = Field(False, description="Whether the graph allows multiple edges")

    connectivity: Optional[ConnectivityParams] = None
    bipartite: Optional[BipartiteParams] = None
    graph_coloring: Optional[GraphColoringParams] = None
    cycle_detection: Optional[CycleDetectionParams] = None
    isomorphism: Optional[IsomorphismParams] = None
    
    # Flow params
    max_flow: Optional[MaxFlowParams] = None
    bipartite_matching: Optional[BipartiteMatchingParams] = None
    
    # Component params
    components: Optional[ComponentParams] = None
    articulation: Optional[ArticulationParams] = None
    
    # Structure params
    degree_sequence: Optional[DegreeSequenceParams] = None
    clique: Optional[CliqueParams] = None
    independent_set: Optional[IndependentSetParams] = None
    vertex_cover: Optional[VertexCoverParams] = None
    
    # Ordering params
    topological_sort: Optional[TopologicalSortParams] = None
    traversal: Optional[TraversalParams] = None
    
    # Global params
    partial_credit: bool = Field(
        False,
        description="Whether to award partial credit"
    )
    feedback_level: Literal["minimal", "standard", "detailed"] = Field(
        "standard",
        description="Level of detail in feedback"
    )
    timeout: float = Field(
        30.0,
        description="Global timeout for computation in seconds"
    )
    tolerance: float = Field(
        1e-9,
        description="Numerical tolerance for comparisons"
    )

    class Config:
        extra = "allow"