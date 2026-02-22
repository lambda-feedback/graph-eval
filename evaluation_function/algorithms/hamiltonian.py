"""Hamiltonian path and cycle detection via backtracking."""

from __future__ import annotations

from evaluation_function.schemas import Graph
from .utils import node_ids


def _adj(graph: Graph) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {n.id: set() for n in graph.nodes}
    for e in graph.edges:
        adj[e.source].add(e.target)
        if not graph.directed:
            adj[e.target].add(e.source)
    return adj


def has_hamiltonian_path(graph: Graph) -> bool:
    nodes = node_ids(graph)
    n = len(nodes)
    if n <= 1:
        return n == 1
    adj = _adj(graph)
    visited: set[str] = set()

    def bt(u: str, count: int) -> bool:
        if count == n:
            return True
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                if bt(v, count + 1):
                    return True
                visited.remove(v)
        return False

    for s in nodes:
        visited = {s}
        if bt(s, 1):
            return True
    return False


def has_hamiltonian_cycle(graph: Graph) -> bool:
    nodes = node_ids(graph)
    n = len(nodes)
    if n < 3:
        return False
    adj = _adj(graph)
    start = nodes[0]
    visited: set[str] = {start}

    def bt(u: str, count: int) -> bool:
        if count == n:
            return start in adj[u]
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                if bt(v, count + 1):
                    return True
                visited.remove(v)
        return False

    return bt(start, 1)
