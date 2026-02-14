"""
Evaluation Parameter Schemas

Defines the parameter schemas for each evaluation type using Pydantic.
"""

from typing import Optional, Literal, Union
from pydantic import BaseModel, Field

from .evaluation_types import EvaluationType


# =============================================================================
# CORE EVALUATION PARAMETERS
# =============================================================================

class ConnectivityParams(BaseModel):
    """
    Parameters for connectivity evaluation.
    """
    check_type: Literal["connected", "strongly_connected", "weakly_connected"] = Field(
        "connected",
        description="Type of connectivity check"
    )
    return_components: bool = Field(
        False,
        description="Whether to return connected components"
    )


class ShortestPathParams(BaseModel):
    """
    Parameters for shortest path evaluation.
    """
    source_node: str = Field(..., description="ID of the starting node")
    target_node: str = Field(..., description="ID of the ending node")
    algorithm: Literal["bfs", "dijkstra", "bellman_ford", "floyd_warshall", "auto"] = Field(
        "auto",
        description="Preferred algorithm (auto-selected if not specified)"
    )
    return_path: bool = Field(True, description="Whether to return the actual path")
    return_distance: bool = Field(True, description="Whether to return the distance")
    all_paths: bool = Field(False, description="Whether to return all shortest paths")


class BipartiteParams(BaseModel):
    """
    Parameters for bipartite evaluation.
    """
    return_partitions: bool = Field(
        False,
        description="Whether to return the two partitions if bipartite"
    )
    return_odd_cycle: bool = Field(
        False,
        description="Whether to return an odd cycle if not bipartite"
    )
    verify_partitions: Optional[list[list[str]]] = Field(
        None,
        description="Specific partitions to verify"
    )


class GraphMatchParams(BaseModel):
    """
    Parameters for graph matching evaluation.
    """
    match_type: Literal["exact", "isomorphic", "subgraph"] = Field(
        "exact",
        description="Type of matching to perform"
    )
    ignore_labels: bool = Field(
        False,
        description="Whether to ignore node/edge labels in comparison"
    )
    ignore_weights: bool = Field(
        False,
        description="Whether to ignore edge weights in comparison"
    )
    tolerance: float = Field(
        1e-9,
        description="Numerical tolerance for weight comparison"
    )
    check_direction: bool = Field(
        True,
        description="Whether to check edge direction (for directed graphs)"
    )


# =============================================================================
# PATH EVALUATION PARAMETERS
# =============================================================================

class EulerianParams(BaseModel):
    """
    Parameters for Eulerian path/circuit evaluation.
    """
    check_existence: bool = Field(
        False,
        description="Only check if path/circuit exists (don't find it)"
    )
    start_node: Optional[str] = Field(
        None,
        description="Required starting node"
    )
    end_node: Optional[str] = Field(
        None,
        description="Required ending node (for path)"
    )
    return_path: bool = Field(
        True,
        description="Whether to return the actual path"
    )


class HamiltonianParams(BaseModel):
    """
    Parameters for Hamiltonian path/circuit evaluation.
    """
    check_existence: bool = Field(
        False,
        description="Only check if path/circuit exists"
    )
    start_node: Optional[str] = Field(
        None,
        description="Required starting node"
    )
    end_node: Optional[str] = Field(
        None,
        description="Required ending node (for path)"
    )
    return_path: bool = Field(
        True,
        description="Whether to return the actual path"
    )
    timeout: float = Field(
        5.0,
        description="Maximum computation time in seconds (NP-complete problem)"
    )


# =============================================================================
# CYCLE EVALUATION PARAMETERS
# =============================================================================

class CycleDetectionParams(BaseModel):
    """
    Parameters for cycle detection evaluation.
    """
    find_all: bool = Field(
        False,
        description="Whether to find all cycles or just detect presence"
    )
    max_nodes: int = Field(
        15,
        description="Maximum number of nodes allowed when enumerating all cycles (safety guard)"
    )
    max_cycles: int = Field(
        1000,
        description="Maximum number of cycles to return when enumerating all cycles (safety guard)"
    )
    max_length: Optional[int] = Field(
        None,
        description="Maximum cycle length to consider"
    )
    min_length: int = Field(
        3,
        description="Minimum cycle length to consider"
    )
    return_cycles: bool = Field(
        True,
        description="Whether to return the actual cycles found"
    )


class NegativeCycleParams(BaseModel):
    """
    Parameters for negative cycle detection.
    """
    return_cycle: bool = Field(
        True,
        description="Whether to return the negative cycle if found"
    )
    source_node: Optional[str] = Field(
        None,
        description="Starting node for detection"
    )


# =============================================================================
# TREE EVALUATION PARAMETERS
# =============================================================================

class SpanningTreeParams(BaseModel):
    """
    Parameters for spanning tree evaluation.
    """
    check_mst: bool = Field(
        False,
        description="Whether to check if it's a minimum spanning tree"
    )
    expected_weight: Optional[float] = Field(
        None,
        description="Expected total weight of the MST"
    )
    weight_tolerance: float = Field(
        1e-9,
        description="Tolerance for weight comparison"
    )
    algorithm: Literal["kruskal", "prim", "auto"] = Field(
        "auto",
        description="Algorithm to use for MST computation"
    )


class TreeParams(BaseModel):
    """
    Parameters for tree-related evaluations.
    """
    root_node: Optional[str] = Field(
        None,
        description="Specified root node for rooted tree operations"
    )
    return_structure: bool = Field(
        False,
        description="Whether to return tree structure info"
    )


# =============================================================================
# COLORING EVALUATION PARAMETERS
# =============================================================================

class GraphColoringParams(BaseModel):
    """
    Parameters for graph coloring evaluation.
    """
    num_colors: Optional[int] = Field(
        None,
        description="Number of colors allowed (k for k-coloring)"
    )
    verify_coloring: Optional[dict[str, int]] = Field(
        None,
        description="Specific coloring to verify (node_id -> color)"
    )
    find_optimal: bool = Field(
        False,
        description="Whether to find the chromatic number"
    )
    algorithm: Literal["greedy", "dsatur", "backtracking", "auto"] = Field(
        "auto",
        description="Coloring algorithm to use"
    )


# =============================================================================
# FLOW EVALUATION PARAMETERS
# =============================================================================

class MaxFlowParams(BaseModel):
    """
    Parameters for maximum flow evaluation.
    """
    source_node: str = Field(..., description="Source node ID")
    sink_node: str = Field(..., description="Sink node ID")
    algorithm: Literal["ford_fulkerson", "edmonds_karp", "dinic", "auto"] = Field(
        "auto",
        description="Flow algorithm to use"
    )
    return_flow_assignment: bool = Field(
        False,
        description="Whether to return flow on each edge"
    )
    return_min_cut: bool = Field(
        False,
        description="Whether to also return the minimum cut"
    )


class BipartiteMatchingParams(BaseModel):
    """
    Parameters for bipartite matching evaluation.
    """
    left_partition: Optional[list[str]] = Field(
        None,
        description="Nodes in left partition (auto-detect if not provided)"
    )
    right_partition: Optional[list[str]] = Field(
        None,
        description="Nodes in right partition"
    )
    weighted: bool = Field(
        False,
        description="Whether to find maximum weight matching"
    )
    perfect: bool = Field(
        False,
        description="Whether to check for perfect matching"
    )
    return_matching: bool = Field(
        True,
        description="Whether to return the matching edges"
    )


# =============================================================================
# COMPONENT EVALUATION PARAMETERS
# =============================================================================

class ComponentParams(BaseModel):
    """
    Parameters for component-related evaluations.
    """
    return_components: bool = Field(
        True,
        description="Whether to return the actual components"
    )
    min_size: int = Field(
        1,
        description="Minimum component size to report"
    )


class ArticulationParams(BaseModel):
    """
    Parameters for articulation points and bridges evaluation.
    """
    return_points: bool = Field(
        True,
        description="Whether to return articulation points"
    )
    return_bridges: bool = Field(
        True,
        description="Whether to return bridges"
    )
    return_biconnected: bool = Field(
        False,
        description="Whether to return biconnected components"
    )


# =============================================================================
# STRUCTURE EVALUATION PARAMETERS
# =============================================================================

class DegreeSequenceParams(BaseModel):
    """
    Parameters for degree sequence evaluation.
    """
    expected_sequence: Optional[list[int]] = Field(
        None,
        description="Expected degree sequence (sorted)"
    )
    allow_permutation: bool = Field(
        True,
        description="Whether sequence can be in any order"
    )
    check_graphical: bool = Field(
        False,
        description="Whether to check if sequence is graphical"
    )


class CliqueParams(BaseModel):
    """
    Parameters for clique evaluation.
    """
    min_size: int = Field(
        3,
        description="Minimum clique size to find"
    )
    max_clique: bool = Field(
        True,
        description="Whether to find maximum clique"
    )
    all_cliques: bool = Field(
        False,
        description="Whether to find all maximal cliques"
    )
    verify_clique: Optional[list[str]] = Field(
        None,
        description="Specific vertex set to verify as clique"
    )
    timeout: float = Field(
        5.0,
        description="Maximum computation time (NP-complete)"
    )


class IndependentSetParams(BaseModel):
    """
    Parameters for independent set evaluation.
    """
    min_size: int = Field(
        1,
        description="Minimum set size to find"
    )
    max_set: bool = Field(
        True,
        description="Whether to find maximum independent set"
    )
    verify_set: Optional[list[str]] = Field(
        None,
        description="Specific vertex set to verify as independent"
    )
    timeout: float = Field(
        5.0,
        description="Maximum computation time (NP-complete)"
    )


class VertexCoverParams(BaseModel):
    """
    Parameters for vertex cover evaluation.
    """
    max_size: Optional[int] = Field(
        None,
        description="Maximum cover size allowed"
    )
    min_cover: bool = Field(
        True,
        description="Whether to find minimum vertex cover"
    )
    verify_cover: Optional[list[str]] = Field(
        None,
        description="Specific vertex set to verify as cover"
    )
    approximation: bool = Field(
        False,
        description="Use 2-approximation algorithm"
    )
    timeout: float = Field(
        5.0,
        description="Maximum computation time (NP-complete)"
    )


# =============================================================================
# ORDERING EVALUATION PARAMETERS
# =============================================================================

class TopologicalSortParams(BaseModel):
    """
    Parameters for topological sort evaluation.
    """
    verify_order: Optional[list[str]] = Field(
        None,
        description="Specific ordering to verify"
    )
    return_order: bool = Field(
        True,
        description="Whether to return a valid ordering"
    )
    all_orderings: bool = Field(
        False,
        description="Whether to return all valid orderings (warning: exponential)"
    )


class TraversalParams(BaseModel):
    """
    Parameters for DFS/BFS traversal evaluation.
    """
    start_node: str = Field(..., description="Starting node for traversal")
    verify_order: Optional[list[str]] = Field(
        None,
        description="Specific order to verify"
    )
    return_order: bool = Field(
        True,
        description="Whether to return the traversal order"
    )
    return_tree: bool = Field(
        False,
        description="Whether to return the traversal tree/forest"
    )


# =============================================================================
# MAIN EVALUATION PARAMS (COMBINED)
# =============================================================================

class EvaluationParams(BaseModel):
    """
    Combined parameters schema for the evaluation function.
    
    This is the `params` argument passed to evaluation_function().
    """
    # Required - type of evaluation
    evaluation_type: EvaluationType = Field(..., description="The type of evaluation to perform")
    
    # Core evaluation params
    connectivity: Optional[ConnectivityParams] = None
    shortest_path: Optional[ShortestPathParams] = None
    bipartite: Optional[BipartiteParams] = None
    graph_match: Optional[GraphMatchParams] = None
    
    # Path params
    eulerian: Optional[EulerianParams] = None
    hamiltonian: Optional[HamiltonianParams] = None
    
    # Cycle params
    cycle_detection: Optional[CycleDetectionParams] = None
    negative_cycle: Optional[NegativeCycleParams] = None
    
    # Tree params
    spanning_tree: Optional[SpanningTreeParams] = None
    tree: Optional[TreeParams] = None
    
    # Coloring params
    graph_coloring: Optional[GraphColoringParams] = None
    
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

    class Config:
        extra = "allow"
