from __future__ import annotations

from typing import Optional

from evaluation_function.schemas import CycleResult, Graph

from .utils import build_adjacency, node_ids


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
                cur = u
                tmp = [cur]
                while cur != v and cur in parent:
                    cur = parent[cur]
                    tmp.append(cur)
                if tmp[-1] != v:
                    return [v, u, v]
                tmp.reverse()
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
                    # Found a cycle — reconstruct it
                    anc_u: set[str] = set()
                    x: Optional[str] = u
                    while x is not None:
                        anc_u.add(x)
                        x = parent.get(x)

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

                    cycle = path_u + list(reversed(path_v))[1:] + [u]
                    return cycle
    return None


def cycle_info(graph: Graph) -> CycleResult:
    """Check whether a graph contains any cycle."""
    directed = bool(graph.directed)
    any_cycle = (
        _find_any_cycle_directed(graph) if directed else _find_any_cycle_undirected(graph)
    )
    return CycleResult(
        has_cycle=any_cycle is not None,
        cycle=any_cycle,
    )
