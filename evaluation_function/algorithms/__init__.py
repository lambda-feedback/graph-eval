"""
Graph Theory Algorithms

This package contains implementations of various graph algorithms.

Modules:
- utils: Common helper functions and data structures
- coloring: Graph coloring algorithms (greedy, DSatur, chromatic number)
- mst: Minimum spanning tree algorithms (Kruskal, Prim, verification)
- path: Eulerian and Hamiltonian path/circuit algorithms
"""

from .utils import (
    # Union-Find data structure
    UnionFind,
    
    # Adjacency builders
    build_adjacency_list,
    build_adjacency_list_weighted,
    build_adjacency_multiset,
    build_edge_set,
    
    # Degree calculations
    get_degree,
    get_in_out_degree,
    
    # Connectivity
    is_connected,
    is_weakly_connected,
    count_components,
    
    # Edge utilities
    get_edge_weight,
)

from .coloring import (
    # Verification
    verify_vertex_coloring,
    verify_edge_coloring,
    detect_coloring_conflicts,
    detect_edge_coloring_conflicts,
    
    # Coloring algorithms
    greedy_coloring,
    dsatur_coloring,
    greedy_edge_coloring,
    
    # Chromatic number
    compute_chromatic_number,
    compute_chromatic_index,
    
    # Helper functions (coloring-specific)
    build_line_graph_adjacency,
)

from .mst import (
    # MST algorithms
    kruskal_mst,
    prim_mst,
    compute_mst,
    
    # MST verification
    verify_spanning_tree,
    verify_mst,
    verify_mst_edges,
    
    # Disconnected graph handling
    compute_minimum_spanning_forest,
    
    # Visualization support
    get_mst_visualization,
    get_mst_animation_steps,
    
    # High-level API
    find_mst,
    evaluate_mst_submission,
    
    # MST-specific helper (wrapper)
    is_graph_connected,
)

from .path import (
    # Eulerian existence checks
    check_eulerian_undirected,
    check_eulerian_directed,
    check_eulerian_existence,
    
    # Eulerian path/circuit finding
    find_eulerian_path_undirected,
    find_eulerian_path_directed,
    find_eulerian_path,
    find_eulerian_circuit,
    
    # Eulerian verification
    verify_eulerian_path,
    
    # Hamiltonian verification
    verify_hamiltonian_path,
    
    # Hamiltonian existence
    find_hamiltonian_path_backtrack,
    check_hamiltonian_existence,
    
    # High-level API
    evaluate_eulerian_path,
    evaluate_hamiltonian_path,
    
    # Feedback
    get_eulerian_feedback,
    get_hamiltonian_feedback,
    
    # Path-specific wrappers
    is_connected_undirected,
    is_weakly_connected_directed,
)

__all__ = [
    # Utils - Union-Find
    "UnionFind",
    
    # Utils - Adjacency builders
    "build_adjacency_list",
    "build_adjacency_list_weighted",
    "build_adjacency_multiset",
    "build_edge_set",
    
    # Utils - Degree calculations
    "get_degree",
    "get_in_out_degree",
    
    # Utils - Connectivity
    "is_connected",
    "is_weakly_connected",
    "count_components",
    
    # Utils - Edge utilities
    "get_edge_weight",
    
    # Coloring - Verification
    "verify_vertex_coloring",
    "verify_edge_coloring",
    "detect_coloring_conflicts",
    "detect_edge_coloring_conflicts",
    
    # Coloring algorithms
    "greedy_coloring",
    "dsatur_coloring",
    "greedy_edge_coloring",
    
    # Chromatic number
    "compute_chromatic_number",
    "compute_chromatic_index",
    
    # Coloring - Helper functions
    "build_line_graph_adjacency",
    
    # MST algorithms
    "kruskal_mst",
    "prim_mst",
    "compute_mst",
    
    # MST verification
    "verify_spanning_tree",
    "verify_mst",
    "verify_mst_edges",
    
    # MST - Disconnected graph handling
    "compute_minimum_spanning_forest",
    
    # MST - Visualization support
    "get_mst_visualization",
    "get_mst_animation_steps",
    
    # MST - High-level API
    "find_mst",
    "evaluate_mst_submission",
    
    # MST - Wrapper
    "is_graph_connected",
    
    # Path - Eulerian existence checks
    "check_eulerian_undirected",
    "check_eulerian_directed",
    "check_eulerian_existence",
    
    # Path - Eulerian path/circuit finding
    "find_eulerian_path_undirected",
    "find_eulerian_path_directed",
    "find_eulerian_path",
    "find_eulerian_circuit",
    
    # Path - Eulerian verification
    "verify_eulerian_path",
    
    # Path - Hamiltonian verification
    "verify_hamiltonian_path",
    
    # Path - Hamiltonian existence
    "find_hamiltonian_path_backtrack",
    "check_hamiltonian_existence",
    
    # Path - High-level API
    "evaluate_eulerian_path",
    "evaluate_hamiltonian_path",
    
    # Path - Feedback
    "get_eulerian_feedback",
    "get_hamiltonian_feedback",
    
    # Path - Wrappers
    "is_connected_undirected",
    "is_weakly_connected_directed",
]
