"""Planarity check using edge bounds and K5 / K3,3 minor detection."""

from __future__ import annotations

from collections import deque
from itertools import combinations

from evaluation_function.schemas import Graph
from .utils import node_ids


def _simple_adj(graph: Graph) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {n.id: set() for n in graph.nodes}
    for e in graph.edges:
        adj[e.source].add(e.target)
        adj[e.target].add(e.source)
    return adj


def _bfs_order(adj: dict[str, set[str]], nodes: list[str]) -> list[str]:
    order: list[str] = []
    visited: set[str] = set()
    for start in nodes:
        if start in visited:
            continue
        q = deque([start])
        visited.add(start)
        while q:
            u = q.popleft()
            order.append(u)
            for v in sorted(adj.get(u, set())):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
    return order


def _has_complete_minor(adj: dict[str, set[str]], order: list[str], k: int) -> bool:
    """Check if graph has K_k as a minor via vertex-partition backtracking."""
    n = len(order)
    if n < k:
        return False

    groups: list[set[str]] = [set() for _ in range(k)]

    def backtrack(idx: int) -> bool:
        if idx == n:
            if any(not g for g in groups):
                return False
            for i in range(k):
                for j in range(i + 1, k):
                    if not any(nb in groups[j] for u in groups[i] for nb in adj[u]):
                        return False
            return True

        node = order[idx]
        nbs = adj.get(node, set())
        tried_empty = False

        for g_idx in range(k):
            if not groups[g_idx]:
                if tried_empty:
                    continue
                tried_empty = True
            elif not (nbs & groups[g_idx]):
                continue

            groups[g_idx].add(node)
            if backtrack(idx + 1):
                return True
            groups[g_idx].remove(node)

        return False

    return backtrack(0)


def _has_bipartite_minor(
    adj: dict[str, set[str]], order: list[str], a: int, b: int
) -> bool:
    """Check if graph has K_{a,b} as a minor."""
    k = a + b
    n = len(order)
    if n < k:
        return False

    groups: list[set[str]] = [set() for _ in range(k)]

    def _check_any_bipartition() -> bool:
        """Try all ways to split k groups into left(a) / right(b)."""
        for left in combinations(range(k), a):
            left_set = set(left)
            right = [i for i in range(k) if i not in left_set]
            ok = True
            for i in left:
                for j in right:
                    if not any(nb in groups[j] for u in groups[i] for nb in adj[u]):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return True
        return False

    def backtrack(idx: int) -> bool:
        if idx == n:
            if any(not g for g in groups):
                return False
            return _check_any_bipartition()

        node = order[idx]
        nbs = adj.get(node, set())
        tried_empty = False

        for g_idx in range(k):
            if not groups[g_idx]:
                if tried_empty:
                    continue
                tried_empty = True
            elif not (nbs & groups[g_idx]):
                continue

            groups[g_idx].add(node)
            if backtrack(idx + 1):
                return True
            groups[g_idx].remove(node)

        return False

    return backtrack(0)


_MAX_MINOR_NODES = 15


def is_planar(graph: Graph) -> bool:
    """Check if a graph is planar.

    Uses Euler-formula edge bounds for fast rejection, then
    K5 / K3,3 minor detection (backtracking) for small graphs.
    """
    nodes = node_ids(graph)
    n = len(nodes)
    m = len(graph.edges)

    if n <= 4:
        return True
    if m > 3 * n - 6:
        return False

    adj = _simple_adj(graph)
    order = _bfs_order(adj, nodes)

    if n <= _MAX_MINOR_NODES:
        if _has_complete_minor(adj, order, 5):
            return False
        if _has_bipartite_minor(adj, order, 3, 3):
            return False

    return True
