"""
Evaluation Type Definitions

Defines the supported graph theory evaluation types.
"""

from typing import Literal


EvaluationType = Literal[
    "bipartite",
    "graph_coloring",
    "cycle_detection",
    "connectivity",
    "isomorphism",
]
