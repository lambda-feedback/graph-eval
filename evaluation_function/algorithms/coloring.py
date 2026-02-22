"""
Graph Coloring — check if a graph is n-colorable.
"""

from __future__ import annotations

from typing import Optional

from evaluation_function.schemas import ColoringResult, Graph

from .utils import build_adjacency_list


def is_n_colorable(graph: Graph, n: int) -> ColoringResult:
    """
    Check whether a graph can be properly colored with at most *n* colors.

    Returns a ColoringResult with is_colorable=True and a valid coloring
    if one exists, or is_colorable=False otherwise.
    """
    adj = build_adjacency_list(graph)
    node_list = [node.id for node in graph.nodes]
    num_nodes = len(node_list)

    if num_nodes == 0:
        return ColoringResult(is_colorable=True, num_colors=n, coloring={})

    if n <= 0:
        return ColoringResult(is_colorable=False, num_colors=n, coloring=None)

    # No edges → 1 color suffices
    if not graph.edges:
        coloring = {nid: 0 for nid in node_list}
        return ColoringResult(is_colorable=True, num_colors=n, coloring=coloring)

    node_index = {nid: i for i, nid in enumerate(node_list)}
    colors = [-1] * num_nodes

    def is_safe(node_idx: int, color: int) -> bool:
        nid = node_list[node_idx]
        for neighbor in adj.get(nid, set()):
            ni = node_index.get(neighbor)
            if ni is not None and colors[ni] == color:
                return False
        return True

    def backtrack(node_idx: int) -> bool:
        if node_idx == num_nodes:
            return True
        for color in range(n):
            if is_safe(node_idx, color):
                colors[node_idx] = color
                if backtrack(node_idx + 1):
                    return True
                colors[node_idx] = -1
        return False

    if backtrack(0):
        coloring = {node_list[i]: colors[i] for i in range(num_nodes)}
        return ColoringResult(is_colorable=True, num_colors=n, coloring=coloring)

    return ColoringResult(is_colorable=False, num_colors=n, coloring=None)
