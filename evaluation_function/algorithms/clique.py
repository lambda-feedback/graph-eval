"""Maximum clique / clique number via backtracking."""

from __future__ import annotations

from evaluation_function.schemas import Graph
from .utils import node_ids


def clique_number(graph: Graph) -> int:
    """Return the size of the largest clique in the graph."""
    nodes = node_ids(graph)
    n = len(nodes)
    if n == 0:
        return 0

    adj: dict[str, set[str]] = {nid: set() for nid in nodes}
    for e in graph.edges:
        adj[e.source].add(e.target)
        adj[e.target].add(e.source)

    best = 1

    def bt(clique: list[str], candidates: list[str]) -> None:
        nonlocal best
        if len(clique) + len(candidates) <= best:
            return  # pruning
        if not candidates:
            if len(clique) > best:
                best = len(clique)
            return
        for i, v in enumerate(candidates):
            new_cand = [u for u in candidates[i + 1:] if u in adj[v]]
            bt(clique + [v], new_cand)

    bt([], nodes)
    return best
