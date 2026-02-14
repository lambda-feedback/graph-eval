"""
Result Schemas

Defines the schemas for evaluation results and feedback using Pydantic.
"""

from typing import Optional, Literal, Any
from pydantic import BaseModel, Field

from .graph import Edge


# =============================================================================
# SPECIFIC RESULT SCHEMAS
# =============================================================================

class PathResult(BaseModel):
    """Result details for shortest path evaluation."""
    path: Optional[list[str]] = Field(None, description="The shortest path")
    distance: Optional[float] = Field(None, description="Path distance/weight")
    path_exists: bool = Field(True, description="Whether a path exists")
    algorithm_used: Optional[str] = Field(None, description="Algorithm used")
    all_paths: Optional[list[list[str]]] = Field(None, description="All shortest paths if multiple exist")
    supplied_path_is_valid: Optional[bool] = Field(None, description="Whether a supplied path is valid")
    supplied_path_weight: Optional[float] = Field(None, description="Total weight of a supplied path")
    supplied_path_is_shortest: Optional[bool] = Field(None, description="Whether a supplied path is a shortest path")


class ConnectivityResult(BaseModel):
    """Result details for connectivity evaluation."""
    is_connected: bool = Field(..., description="Whether graph is connected")
    num_components: int = Field(1, description="Number of connected components")
    components: Optional[list[list[str]]] = Field(None, description="The connected components")
    connectivity_type: Optional[str] = Field(None, description="Type of connectivity checked")
    largest_component_size: Optional[int] = Field(None, description="Size of largest component")


class BipartiteResult(BaseModel):
    """Result details for bipartite evaluation."""
    is_bipartite: bool = Field(..., description="Whether graph is bipartite")
    partitions: Optional[list[list[str]]] = Field(None, description="The two partitions")
    odd_cycle: Optional[list[str]] = Field(None, description="Proof if not bipartite (odd cycle)")


class GraphMatchResult(BaseModel):
    """Result details for graph matching evaluation."""
    is_match: bool = Field(..., description="Whether graphs match")
    match_type: Optional[str] = Field(None, description="Type of match performed")
    missing_nodes: Optional[list[str]] = Field(None, description="Nodes missing from response")
    extra_nodes: Optional[list[str]] = Field(None, description="Extra nodes in response")
    missing_edges: Optional[list[Edge]] = Field(None, description="Edges missing from response")
    extra_edges: Optional[list[Edge]] = Field(None, description="Extra edges in response")
    node_mapping: Optional[dict[str, str]] = Field(None, description="Node mapping for isomorphism")


class EulerianResult(BaseModel):
    """Result details for Eulerian path/circuit evaluation."""
    exists: bool = Field(..., description="Whether Eulerian path/circuit exists")
    path: Optional[list[str]] = Field(None, description="The Eulerian path/circuit")
    is_circuit: bool = Field(False, description="Whether it's a circuit (closed)")
    odd_degree_vertices: Optional[list[str]] = Field(None, description="Vertices with odd degree")


class HamiltonianResult(BaseModel):
    """Result details for Hamiltonian path/circuit evaluation."""
    exists: Optional[bool] = Field(None, description="Whether Hamiltonian path/circuit exists")
    path: Optional[list[str]] = Field(None, description="The Hamiltonian path/circuit")
    is_circuit: bool = Field(False, description="Whether it's a circuit (closed)")
    timed_out: bool = Field(False, description="Whether computation timed out")


class CycleResult(BaseModel):
    """Result details for cycle detection evaluation."""
    has_cycle: bool = Field(..., description="Whether graph contains a cycle")
    cycles: Optional[list[list[str]]] = Field(None, description="Cycles found")
    shortest_cycle: Optional[list[str]] = Field(None, description="The shortest cycle")
    girth: Optional[int] = Field(None, description="Length of shortest cycle")
    has_negative_cycle: Optional[bool] = Field(None, description="Whether negative cycle exists")
    negative_cycle: Optional[list[str]] = Field(None, description="The negative cycle")


class TreeResult(BaseModel):
    """Result details for tree evaluations."""
    is_tree: bool = Field(False, description="Whether graph is a tree")
    is_spanning_tree: Optional[bool] = Field(None, description="Whether it's a valid spanning tree")
    is_mst: Optional[bool] = Field(None, description="Whether it's a minimum spanning tree")
    total_weight: Optional[float] = Field(None, description="Total edge weight")
    edges: Optional[list[Edge]] = Field(None, description="Tree edges")
    diameter: Optional[int] = Field(None, description="Tree diameter")
    center: Optional[list[str]] = Field(None, description="Tree center vertex(es)")
    root: Optional[str] = Field(None, description="Root node if rooted tree")


class ColoringResult(BaseModel):
    """Result details for graph coloring evaluation."""
    is_valid_coloring: bool = Field(..., description="Whether coloring is valid")
    coloring: Optional[dict[str, int]] = Field(None, description="The coloring assignment")
    num_colors_used: Optional[int] = Field(None, description="Number of colors used")
    chromatic_number: Optional[int] = Field(None, description="Chromatic number (if computed)")
    conflicts: Optional[list[tuple[str, str]]] = Field(None, description="Edges with same-color endpoints")


class FlowResult(BaseModel):
    """Result details for flow network evaluation."""
    max_flow_value: Optional[float] = Field(None, description="Maximum flow value")
    flow_assignment: Optional[dict[str, float]] = Field(None, description="Flow on each edge")
    min_cut_nodes: Optional[list[str]] = Field(None, description="Nodes on source side of min cut")
    min_cut_edges: Optional[list[Edge]] = Field(None, description="Edges in the minimum cut")
    min_cut_capacity: Optional[float] = Field(None, description="Total capacity of min cut")
    is_valid_flow: Optional[bool] = Field(None, description="Whether submitted flow is valid")


class MatchingResult(BaseModel):
    """Result details for matching evaluation."""
    matching: Optional[list[tuple[str, str]]] = Field(None, description="The matching edges")
    matching_size: Optional[int] = Field(None, description="Size of matching")
    is_perfect: Optional[bool] = Field(None, description="Whether matching is perfect")
    is_maximum: Optional[bool] = Field(None, description="Whether matching is maximum")
    unmatched_vertices: Optional[list[str]] = Field(None, description="Unmatched vertices")
    total_weight: Optional[float] = Field(None, description="Total weight for weighted matching")


class ComponentResult(BaseModel):
    """Result details for component-related evaluations."""
    components: Optional[list[list[str]]] = Field(None, description="The components")
    num_components: int = Field(1, description="Number of components")
    articulation_points: Optional[list[str]] = Field(None, description="Articulation points")
    bridges: Optional[list[Edge]] = Field(None, description="Bridge edges")
    biconnected_components: Optional[list[list[str]]] = Field(None, description="Biconnected components")


class StructureResult(BaseModel):
    """Result details for graph structure evaluations."""
    degree_sequence: Optional[list[int]] = Field(None, description="Degree sequence")
    is_regular: Optional[bool] = Field(None, description="Whether graph is regular")
    regularity: Optional[int] = Field(None, description="k if k-regular")
    is_planar: Optional[bool] = Field(None, description="Whether graph is planar")
    is_complete: Optional[bool] = Field(None, description="Whether graph is complete")
    clique: Optional[list[str]] = Field(None, description="Maximum clique")
    clique_size: Optional[int] = Field(None, description="Size of maximum clique")
    independent_set: Optional[list[str]] = Field(None, description="Maximum independent set")
    independent_set_size: Optional[int] = Field(None, description="Size of maximum independent set")
    vertex_cover: Optional[list[str]] = Field(None, description="Minimum vertex cover")
    vertex_cover_size: Optional[int] = Field(None, description="Size of minimum vertex cover")


class OrderingResult(BaseModel):
    """Result details for ordering evaluations."""
    is_valid_order: bool = Field(..., description="Whether the order is valid")
    order: Optional[list[str]] = Field(None, description="A valid ordering")
    all_valid_orderings: Optional[list[list[str]]] = Field(None, description="All valid orderings")
    traversal_tree: Optional[dict[str, list[str]]] = Field(None, description="Traversal tree structure")


# =============================================================================
# FEEDBACK SCHEMA
# =============================================================================

class FeedbackItem(BaseModel):
    """A single feedback item."""
    type: Literal["success", "error", "warning", "info", "hint"] = Field(
        ..., description="Type of feedback"
    )
    message: str = Field(..., description="Feedback message")
    details: Optional[str] = Field(None, description="Additional details")
    location: Optional[str] = Field(None, description="Reference to specific node/edge")


class ComputationStep(BaseModel):
    """A step in the computation (for detailed feedback)."""
    step_number: int = Field(..., description="Step number")
    description: str = Field(..., description="Description of this step")
    state: Optional[dict[str, Any]] = Field(None, description="Current state at this step")
    highlight_nodes: Optional[list[str]] = Field(None, description="Nodes to highlight")
    highlight_edges: Optional[list[Edge]] = Field(None, description="Edges to highlight")


# =============================================================================
# MAIN EVALUATION RESULT SCHEMA
# =============================================================================

class EvaluationDetails(BaseModel):
    """
    Detailed evaluation results.
    
    Contains type-specific results and feedback information.
    """
    # Type-specific results
    path_result: Optional[PathResult] = None
    connectivity_result: Optional[ConnectivityResult] = None
    bipartite_result: Optional[BipartiteResult] = None
    graph_match_result: Optional[GraphMatchResult] = None
    eulerian_result: Optional[EulerianResult] = None
    hamiltonian_result: Optional[HamiltonianResult] = None
    cycle_result: Optional[CycleResult] = None
    tree_result: Optional[TreeResult] = None
    coloring_result: Optional[ColoringResult] = None
    flow_result: Optional[FlowResult] = None
    matching_result: Optional[MatchingResult] = None
    component_result: Optional[ComponentResult] = None
    structure_result: Optional[StructureResult] = None
    ordering_result: Optional[OrderingResult] = None
    
    # Computed values (for display/verification)
    computed_answer: Optional[dict[str, Any]] = Field(None, description="The computed correct answer")
    expected_answer: Optional[dict[str, Any]] = Field(None, description="The expected answer")
    
    # Feedback
    feedback_items: list[FeedbackItem] = Field(default_factory=list, description="Feedback items")
    computation_steps: list[ComputationStep] = Field(default_factory=list, description="Step-by-step computation")
    hints: list[str] = Field(default_factory=list, description="Hints for incorrect answers")
    


# =============================================================================
# VISUALIZATION DATA
# =============================================================================

class VisualizationData(BaseModel):
    """
    Data for visualizing the result in the UI.
    """
    highlight_nodes: list[str] = Field(default_factory=list, description="Nodes to highlight")
    highlight_edges: list[Edge] = Field(default_factory=list, description="Edges to highlight")
    node_colors: dict[str, str] = Field(default_factory=dict, description="Color assignments for nodes")
    edge_colors: dict[str, str] = Field(default_factory=dict, description="Color assignments for edges")
    node_labels: dict[str, str] = Field(default_factory=dict, description="Additional labels for nodes")
    edge_labels: dict[str, str] = Field(default_factory=dict, description="Additional labels for edges")
    animation_steps: list[dict[str, Any]] = Field(default_factory=list, description="Animation steps")
    partitions: Optional[list[list[str]]] = Field(None, description="For bipartite visualization")
    tree_layout: Optional[dict[str, tuple[float, float]]] = Field(None, description="Computed tree positions")


# =============================================================================
# COMPLETE RESULT (extends lf_toolkit Result)
# =============================================================================

class EvaluationResult(BaseModel):
    """
    Complete evaluation result schema.
    
    This wraps the lf_toolkit Result with graph-specific details.
    """
    is_correct: bool = Field(..., description="Whether the answer is correct")
    feedback: Optional[str] = Field(None, description="Main feedback message")
    
    # Extended graph evaluation data
    evaluation_details: Optional[EvaluationDetails] = Field(
        None, description="Detailed evaluation results"
    )
    visualization: Optional[VisualizationData] = Field(
        None, description="Visualization data for the UI"
    )
    
    # Warnings and errors
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[str] = Field(default_factory=list, description="Error messages")
