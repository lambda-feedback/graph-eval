"""
Evaluation Type Definitions

Defines the supported graph theory evaluation types.
"""

from typing import Literal


EvaluationType = Literal[
    "connectivity",
    "bipartite",
    "cycle_detection",
    "graph_coloring",
    "isomorphism",
    "planarity",
    "tree",
    "forest",
    "dag",
    "eulerian",
    "semi_eulerian",
    "regular",
    "complete",
    "degree_sequence",
    "subgraph",
    "hamiltonian_path",
    "hamiltonian_cycle",
    "clique_number",
]
