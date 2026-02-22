from __future__ import annotations

from dataclasses import dataclass

from evaluation_function.schemas import Edge, Graph


@dataclass(frozen=True)
class AdjEdge:
    to: str
    weight: float
    edge: Edge


def node_ids(graph: Graph) -> list[str]:
    return [n.id for n in graph.nodes]


def build_adjacency(graph: Graph, *, undirected: bool) -> dict[str, list[AdjEdge]]:
    adj: dict[str, list[AdjEdge]] = {n.id: [] for n in graph.nodes}
    for e in graph.edges:
        w = float(e.weight if e.weight is not None else 1.0)
        adj.setdefault(e.source, []).append(AdjEdge(to=e.target, weight=w, edge=e))
        if undirected:
            adj.setdefault(e.target, []).append(AdjEdge(to=e.source, weight=w, edge=e))
    return adj


def build_reverse_adjacency(graph: Graph) -> dict[str, list[AdjEdge]]:
    """Directed reverse adjacency (for strongly connected checks)."""
    adj: dict[str, list[AdjEdge]] = {n.id: [] for n in graph.nodes}
    for e in graph.edges:
        w = float(e.weight if e.weight is not None else 1.0)
        adj.setdefault(e.target, []).append(AdjEdge(to=e.source, weight=w, edge=e))
    return adj


def build_adjacency_list(graph: Graph) -> dict[str, set[str]]:
    """Simple adjacency list (node_id -> set of neighbor ids). Undirected."""
    adj: dict[str, set[str]] = {n.id: set() for n in graph.nodes}
    for e in graph.edges:
        adj.setdefault(e.source, set()).add(e.target)
        adj.setdefault(e.target, set()).add(e.source)
    return adj
