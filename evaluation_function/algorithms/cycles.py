from __future__ import annotations

from collections import deque
from typing import Optional

from evaluation_function.schemas import CycleResult, Graph

from .utils import build_adjacency, node_ids


def _close_cycle(cycle: list[str]) -> list[str]:
    if not cycle:
        return cycle
    return cycle if cycle[0] == cycle[-1] else (cycle + [cycle[0]])


def _canonical_rotation(nodes: list[str]) -> tuple[str, ...]:
    """Canonical rotation of a cyclic sequence (no repeated last node)."""
    if not nodes:
        return tuple()
    n = len(nodes)
    best: Optional[tuple[str, ...]] = None
    for i in range(n):
        rot = tuple(nodes[i:] + nodes[:i])
        if best is None or rot < best:
            best = rot
    return best or tuple(nodes)


def _canonical_cycle(cycle: list[str], *, undirected: bool) -> tuple[str, ...]:
    """
    Canonicalize a cycle for deduping.

    Input may be closed (start == end) or open; output is a closed tuple.
    """
    c = cycle[:]
    if len(c) >= 2 and c[0] == c[-1]:
        c = c[:-1]
    if not c:
        return tuple()
    if len(c) == 1:
        return (c[0], c[0])

    fwd = _canonical_rotation(c)
    if not undirected:
        return fwd + (fwd[0],)

    rev = _canonical_rotation(list(reversed(c)))
    best = min(fwd, rev)
    return best + (best[0],)


def _reconstruct_cycle_from_tree_edge(u: str, v: str, parent: dict[str, Optional[str]]) -> list[str]:
    """
    Reconstruct a cycle in an undirected BFS/DFS tree given a non-tree edge (u, v).
    """
    anc_u: set[str] = set()
    x = u
    while x is not None:
        anc_u.add(x)
        x = parent.get(x)

    # walk v upward to LCA
    lca = v
    while lca not in anc_u:
        nxt = parent.get(lca)
        if nxt is None:
            break
        lca = nxt

    path_u: list[str] = []
    x = u
    while x is not None and x != lca:
        path_u.append(x)
        x = parent.get(x)
    path_u.append(lca)

    path_v: list[str] = []
    x = v
    while x is not None and x != lca:
        path_v.append(x)
        x = parent.get(x)
    path_v.append(lca)

    # u -> ... -> lca -> ... -> v -> u (via edge v-u)
    cycle = path_u + list(reversed(path_v))[1:] + [u]
    return cycle


def _find_any_cycle_directed(graph: Graph) -> Optional[list[str]]:
    adj = build_adjacency(graph, undirected=False)
    color: dict[str, int] = {}  # 0 unvisited, 1 in-stack, 2 done
    parent: dict[str, str] = {}

    for start in node_ids(graph):
        if color.get(start, 0) != 0:
            continue

        stack: list[tuple[str, int]] = [(start, 0)]
        color[start] = 1

        while stack:
            u, idx = stack[-1]
            neigh = adj.get(u, [])
            if idx >= len(neigh):
                color[u] = 2
                stack.pop()
                continue

            v = neigh[idx].to
            stack[-1] = (u, idx + 1)

            cv = color.get(v, 0)
            if cv == 0:
                parent[v] = u
                color[v] = 1
                stack.append((v, 0))
            elif cv == 1:
                # back-edge u -> v; reconstruct v ... u -> v
                cur = u
                tmp = [cur]
                while cur != v and cur in parent:
                    cur = parent[cur]
                    tmp.append(cur)
                if tmp[-1] != v:
                    # Should be on stack; but if not, skip reconstruction.
                    return [v, u, v]
                tmp.reverse()  # v ... u
                return tmp + [v]

    return None


def _find_any_cycle_undirected(graph: Graph) -> Optional[list[str]]:
    adj = build_adjacency(graph, undirected=True)
    seen: set[str] = set()
    parent: dict[str, Optional[str]] = {}

    for start in node_ids(graph):
        if start in seen:
            continue
        parent[start] = None
        stack = [start]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            for ae in adj.get(u, []):
                v = ae.to
                if v not in seen:
                    parent[v] = u
                    stack.append(v)
                elif parent.get(u) != v:
                    return _reconstruct_cycle_from_tree_edge(u, v, parent)
    return None


def _all_simple_cycles_bruteforce(
    graph: Graph,
    *,
    min_length: int,
    max_length: Optional[int],
    max_cycles: int,
    max_nodes: int,
) -> list[list[str]]:
    ids = sorted(node_ids(graph))
    if len(ids) > max_nodes:
        return []

    directed = bool(graph.directed)
    adj = build_adjacency(graph, undirected=not directed)
    index = {n: i for i, n in enumerate(ids)}
    undirected = not directed

    seen_cycles: set[tuple[str, ...]] = set()
    out: list[list[str]] = []

    def add_cycle(cycle: list[str]) -> None:
        if len(out) >= max_cycles:
            return
        key = _canonical_cycle(cycle, undirected=undirected)
        if not key:
            return
        if key in seen_cycles:
            return
        # enforce length bounds using number of distinct vertices in the cycle
        k = len(key) - 1  # edges/vertices count in simple cycle
        if k < min_length:
            return
        if max_length is not None and k > max_length:
            return
        seen_cycles.add(key)
        out.append(list(key))

    for start in ids:
        if len(out) >= max_cycles:
            break
        start_i = index[start]
        path = [start]
        in_path = {start}

        def dfs(u: str, prev: Optional[str]) -> None:
            if len(out) >= max_cycles:
                return

            # Prune on path length (distinct vertices)
            if max_length is not None and len(path) > max_length:
                return

            for ae in adj.get(u, []):
                v = ae.to
                if index.get(v, -1) < start_i:
                    continue  # ensure start is the minimum-id vertex in cycle
                if not directed and prev is not None and v == prev:
                    continue  # don't immediately traverse back on undirected edge
                if v == start:
                    if len(path) >= 1:
                        add_cycle(path + [start])
                    continue
                if v in in_path:
                    continue
                in_path.add(v)
                path.append(v)
                dfs(v, u)
                path.pop()
                in_path.remove(v)

        dfs(start, None)

    out.sort(key=lambda c: (len(c), c))
    return out


def _girth_and_shortest_cycle(graph: Graph) -> tuple[Optional[int], Optional[list[str]]]:
    ids = node_ids(graph)
    if len(ids) == 0:
        return None, None

    directed = bool(graph.directed)
    adj = build_adjacency(graph, undirected=not directed)

    best_len: Optional[int] = None
    best_cycle: Optional[list[str]] = None

    if directed:
        for start in ids:
            dist: dict[str, int] = {start: 0}
            parent: dict[str, Optional[str]] = {start: None}
            q = deque([start])
            while q:
                u = q.popleft()
                du = dist[u]
                if best_len is not None and du + 1 >= best_len:
                    continue
                for ae in adj.get(u, []):
                    v = ae.to
                    if v == start:
                        cand = du + 1
                        if best_len is None or cand < best_len:
                            # reconstruct start -> ... -> u then back to start
                            path: list[str] = []
                            x: Optional[str] = u
                            while x is not None:
                                path.append(x)
                                x = parent.get(x)
                            path.reverse()
                            best_len = cand
                            best_cycle = path + [start]
                        continue
                    if v not in dist:
                        dist[v] = du + 1
                        parent[v] = u
                        q.append(v)
        return best_len, best_cycle

    # Undirected girth using BFS from each vertex
    for start in ids:
        dist: dict[str, int] = {start: 0}
        parent: dict[str, Optional[str]] = {start: None}
        q = deque([start])
        while q:
            u = q.popleft()
            du = dist[u]
            if best_len is not None and du * 2 + 1 >= best_len:
                continue
            for ae in adj.get(u, []):
                v = ae.to
                if v not in dist:
                    dist[v] = du + 1
                    parent[v] = u
                    q.append(v)
                elif parent.get(u) != v:
                    cand = dist[u] + dist[v] + 1
                    if best_len is None or cand < best_len:
                        best_len = cand
                        best_cycle = _reconstruct_cycle_from_tree_edge(u, v, parent)

    return best_len, best_cycle


def _detect_negative_cycle_bellman_ford(
    graph: Graph, *, source_node: Optional[str] = None
) -> tuple[bool, Optional[list[str]]]:
    """
    Detect any negative-weight cycle using Bellman-Ford.

    If source_node is None, uses a "super source" approach (dist=0 for all nodes)
    to detect negative cycles anywhere in the graph.
    """
    ids = node_ids(graph)
    if not ids:
        return False, None

    directed = bool(graph.directed)
    edges: list[tuple[str, str, float]] = []
    for e in graph.edges:
        w = float(e.weight if e.weight is not None else 1.0)
        edges.append((e.source, e.target, w))
        if not directed:
            edges.append((e.target, e.source, w))

    if source_node is not None and source_node not in set(ids):
        return False, None

    if source_node is None:
        dist = {v: 0.0 for v in ids}
    else:
        dist = {source_node: 0.0}

    pred: dict[str, str] = {}
    x: Optional[str] = None

    # Relax |V| times; if we can relax on the |V|-th iteration, there's a negative cycle.
    for _ in range(len(ids)):
        x = None
        for u, v, w in edges:
            if u not in dist:
                continue
            nd = dist[u] + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                pred[v] = u
                x = v

    if x is None:
        return False, None

    # Move x into the cycle by following predecessors |V| times
    y = x
    for _ in range(len(ids)):
        y = pred.get(y, y)

    # Collect the cycle by walking until we repeat y
    cycle = [y]
    cur = pred.get(y)
    while cur is not None and cur != y and cur not in cycle:
        cycle.append(cur)
        cur = pred.get(cur)

    if not cycle:
        return True, None

    # Make it a forward cycle order
    cycle.reverse()
    cycle = _close_cycle(cycle)
    return True, cycle


def cycle_info(
    graph: Graph,
    *,
    find_all: bool = False,
    min_length: int = 3,
    max_length: Optional[int] = None,
    max_cycles: int = 1000,
    max_nodes: int = 15,
    return_cycles: bool = True,
    return_shortest_cycle: bool = True,
    return_girth: bool = True,
    detect_negative_cycle: bool = False,
    return_negative_cycle: bool = True,
    negative_cycle_source_node: Optional[str] = None,
) -> CycleResult:
    """
    Compute cycle-related information for a graph.

    - Cycle existence uses DFS (O(V+E)).
    - Shortest cycle (girth) uses BFS (O(VE)) on unweighted edges.
    - All cycles uses brute force with safeguards (intended for small graphs).
    - Negative cycle uses Bellman-Ford (O(VE)).
    """
    directed = bool(graph.directed)

    # Fast existence check first
    any_cycle = (
        _find_any_cycle_directed(graph) if directed else _find_any_cycle_undirected(graph)
    )
    has_cycle = any_cycle is not None

    cycles: Optional[list[list[str]]] = None
    if find_all and return_cycles:
        cycles = _all_simple_cycles_bruteforce(
            graph,
            min_length=max(1, int(min_length)),
            max_length=max_length,
            max_cycles=max(1, int(max_cycles)),
            max_nodes=max(1, int(max_nodes)),
        )
    elif return_cycles and any_cycle is not None:
        cycles = [_close_cycle(any_cycle)]

    girth: Optional[int] = None
    shortest_cycle: Optional[list[str]] = None
    if return_girth or return_shortest_cycle:
        g_len, g_cycle = _girth_and_shortest_cycle(graph)
        girth = g_len if return_girth else None
        shortest_cycle = _close_cycle(g_cycle) if (return_shortest_cycle and g_cycle) else None

    has_negative_cycle: Optional[bool] = None
    negative_cycle: Optional[list[str]] = None
    if detect_negative_cycle:
        has_negative_cycle, neg = _detect_negative_cycle_bellman_ford(
            graph, source_node=negative_cycle_source_node
        )
        negative_cycle = _close_cycle(neg) if (return_negative_cycle and neg) else None

    return CycleResult(
        has_cycle=has_cycle,
        cycles=cycles,
        shortest_cycle=shortest_cycle,
        girth=girth,
        has_negative_cycle=has_negative_cycle,
        negative_cycle=negative_cycle,
    )

