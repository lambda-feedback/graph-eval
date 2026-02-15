"""
Core graph algorithms used by the evaluation function.
"""

from .connectivity import connectivity_info
from .bipartite import bipartite_info
from .cycles import cycle_info
from .coloring import is_n_colorable
from .isomorphism import isomorphism_info
from .properties import (
    is_tree,
    is_forest,
    is_dag,
    is_eulerian,
    is_semi_eulerian,
    is_regular,
    is_complete,
    degree_sequence,
    is_subgraph,
)
from .hamiltonian import has_hamiltonian_path, has_hamiltonian_cycle
from .clique import clique_number
from .planarity import is_planar

__all__ = [
    "connectivity_info",
    "bipartite_info",
    "cycle_info",
    "is_n_colorable",
    "isomorphism_info",
    "is_tree",
    "is_forest",
    "is_dag",
    "is_eulerian",
    "is_semi_eulerian",
    "is_regular",
    "is_complete",
    "degree_sequence",
    "is_subgraph",
    "has_hamiltonian_path",
    "has_hamiltonian_cycle",
    "clique_number",
    "is_planar",
]
