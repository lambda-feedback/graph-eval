"""
Eulerian and Hamiltonian Path/Circuit Algorithms

This module implements path algorithms:
- Eulerian path/circuit existence check (degree conditions)
- Eulerian path/circuit finder (Hierholzer's algorithm)
- Hamiltonian path/circuit verification
- Hamiltonian existence check with timeout (backtracking)

Supports both directed and undirected graphs.

All algorithms work with the Graph schema defined in schemas.graph.
"""

from typing import Optional
from collections import defaultdict, deque
import time

from ..schemas.graph import Graph, Node, Edge
from ..schemas.result import EulerianResult, HamiltonianResult
from .utils import (
    build_adjacency_list,
    build_adjacency_multiset,
    get_in_out_degree,
    is_connected,
    is_weakly_connected,
)


# =============================================================================
# CONNECTIVITY WRAPPERS (Path-specific behavior)
# =============================================================================

def is_connected_undirected(graph: Graph) -> bool:
    """
    Check if an undirected graph is connected.
    Ignores isolated vertices for Eulerian path purposes.
    
    Args:
        graph: The Graph object
        
    Returns:
        True if all non-isolated vertices are connected
    """
    return is_connected(graph, include_isolated=False)


def is_weakly_connected_directed(graph: Graph) -> bool:
    """
    Check if a directed graph is weakly connected.
    (Connected when treating edges as undirected)
    
    Args:
        graph: The Graph object
        
    Returns:
        True if weakly connected
    """
    return is_weakly_connected(graph)


def get_degree(adj: dict[str, set[str]], node: str) -> int:
    """Get the degree of a node in an undirected graph."""
    return len(adj.get(node, set()))


# =============================================================================
# EULERIAN PATH/CIRCUIT - EXISTENCE CHECK
# =============================================================================

def check_eulerian_undirected(graph: Graph) -> tuple[bool, bool, list[str], str]:
    """
    Check if an undirected graph has an Eulerian path or circuit.
    
    For undirected graphs:
    - Eulerian circuit exists iff all vertices have even degree and graph is connected
    - Eulerian path exists iff exactly 0 or 2 vertices have odd degree and graph is connected
    
    Args:
        graph: The Graph object (undirected)
        
    Returns:
        Tuple of (has_path, has_circuit, odd_degree_vertices, reason_if_no_path)
    """
    if not graph.edges:
        # Empty graph has trivial Eulerian circuit
        return True, True, [], ""
    
    # Check connectivity
    if not is_connected_undirected(graph):
        return False, False, [], "Graph is not connected. All vertices with edges must be in the same connected component."
    
    # Calculate degrees properly (counting edge multiplicities for multigraphs)
    degree: dict[str, int] = defaultdict(int)
    for node in graph.nodes:
        degree[node.id] = 0
    
    for edge in graph.edges:
        if edge.source == edge.target:
            # Self-loop contributes 2 to degree
            degree[edge.source] += 2
        else:
            degree[edge.source] += 1
            degree[edge.target] += 1
    
    # Count vertices with odd degree
    odd_degree_vertices = []
    for node_id, deg in degree.items():
        if deg % 2 == 1:
            odd_degree_vertices.append(node_id)
    
    num_odd = len(odd_degree_vertices)
    
    if num_odd == 0:
        return True, True, [], ""
    elif num_odd == 2:
        return True, False, odd_degree_vertices, f"Graph has Eulerian path (not circuit) because vertices {odd_degree_vertices[0]} and {odd_degree_vertices[1]} have odd degree."
    else:
        return False, False, odd_degree_vertices, f"Graph has {num_odd} vertices with odd degree ({', '.join(odd_degree_vertices[:5])}{'...' if num_odd > 5 else ''}). Eulerian path requires exactly 0 or 2 vertices with odd degree."


def check_eulerian_directed(graph: Graph) -> tuple[bool, bool, list[str], list[str], str]:
    """
    Check if a directed graph has an Eulerian path or circuit.
    
    For directed graphs:
    - Eulerian circuit exists iff in-degree = out-degree for all vertices
    - Eulerian path exists iff at most one vertex has out-degree - in-degree = 1 (start)
      and at most one vertex has in-degree - out-degree = 1 (end),
      all other vertices have in-degree = out-degree
    
    Args:
        graph: The Graph object (directed)
        
    Returns:
        Tuple of (has_path, has_circuit, start_candidates, end_candidates, reason_if_no_path)
    """
    if not graph.edges:
        return True, True, [], [], ""
    
    # Check weak connectivity
    if not is_weakly_connected_directed(graph):
        return False, False, [], [], "Graph is not weakly connected. All vertices with edges must be reachable."
    
    in_degree, out_degree = get_in_out_degree(graph)
    
    start_candidates = []  # out - in = 1
    end_candidates = []    # in - out = 1
    unbalanced = []        # |in - out| > 1
    
    for node_id in in_degree:
        diff = out_degree[node_id] - in_degree[node_id]
        if diff == 1:
            start_candidates.append(node_id)
        elif diff == -1:
            end_candidates.append(node_id)
        elif diff != 0:
            unbalanced.append((node_id, diff))
    
    if unbalanced:
        node, diff = unbalanced[0]
        return False, False, [], [], f"Vertex {node} has degree imbalance of {diff} (out - in). All vertices must have equal in/out degree for circuit, or exactly one start (+1) and one end (-1) for path."
    
    if len(start_candidates) == 0 and len(end_candidates) == 0:
        return True, True, [], [], ""
    elif len(start_candidates) == 1 and len(end_candidates) == 1:
        return True, False, start_candidates, end_candidates, f"Graph has Eulerian path from {start_candidates[0]} to {end_candidates[0]}, but not a circuit."
    else:
        return False, False, start_candidates, end_candidates, f"Invalid degree configuration: {len(start_candidates)} potential start(s), {len(end_candidates)} potential end(s). Need exactly 0 and 0, or 1 and 1."


def check_eulerian_existence(
    graph: Graph,
    check_circuit: bool = False
) -> EulerianResult:
    """
    Check if an Eulerian path or circuit exists in the graph.
    
    Args:
        graph: The Graph object
        check_circuit: If True, specifically check for circuit; otherwise check for path
        
    Returns:
        EulerianResult with existence information and feedback
    """
    if graph.directed:
        has_path, has_circuit, starts, ends, reason = check_eulerian_directed(graph)
        
        if check_circuit:
            if has_circuit:
                return EulerianResult(
                    exists=True,
                    is_circuit=True,
                    odd_degree_vertices=None
                )
            else:
                return EulerianResult(
                    exists=False,
                    is_circuit=True,
                    odd_degree_vertices=starts + ends if starts or ends else None
                )
        else:
            if has_path:
                return EulerianResult(
                    exists=True,
                    is_circuit=has_circuit,
                    odd_degree_vertices=None
                )
            else:
                return EulerianResult(
                    exists=False,
                    is_circuit=False,
                    odd_degree_vertices=starts + ends if starts or ends else None
                )
    else:
        has_path, has_circuit, odd_vertices, reason = check_eulerian_undirected(graph)
        
        if check_circuit:
            return EulerianResult(
                exists=has_circuit,
                is_circuit=True,
                odd_degree_vertices=odd_vertices if odd_vertices else None
            )
        else:
            return EulerianResult(
                exists=has_path,
                is_circuit=has_circuit,
                odd_degree_vertices=odd_vertices if odd_vertices else None
            )


# =============================================================================
# EULERIAN PATH/CIRCUIT - HIERHOLZER'S ALGORITHM
# =============================================================================

def find_eulerian_path_undirected(
    graph: Graph,
    start_node: Optional[str] = None
) -> Optional[list[str]]:
    """
    Find an Eulerian path in an undirected graph using Hierholzer's algorithm.
    
    Args:
        graph: The Graph object (undirected)
        start_node: Optional starting node
        
    Returns:
        List of node IDs forming the Eulerian path, or None if no path exists
    """
    has_path, has_circuit, odd_vertices, _ = check_eulerian_undirected(graph)
    
    if not has_path:
        return None
    
    if not graph.edges:
        # Empty graph
        if graph.nodes:
            return [graph.nodes[0].id]
        return []
    
    # Build adjacency with edge counts (for multigraph support)
    adj: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for node in graph.nodes:
        adj[node.id]  # Initialize
    for edge in graph.edges:
        adj[edge.source][edge.target] += 1
        adj[edge.target][edge.source] += 1
    
    # Determine starting node
    if start_node:
        if start_node not in adj:
            return None
        start = start_node
    elif odd_vertices:
        start = odd_vertices[0]
    else:
        # Find first node with edges
        start = None
        for node_id in adj:
            if adj[node_id]:
                start = node_id
                break
        if start is None:
            return [graph.nodes[0].id] if graph.nodes else []
    
    # Hierholzer's algorithm
    stack = [start]
    path = []
    
    while stack:
        v = stack[-1]
        if adj[v]:
            # Pick an edge
            u = next(iter(adj[v]))
            adj[v][u] -= 1
            if adj[v][u] == 0:
                del adj[v][u]
            adj[u][v] -= 1
            if adj[u][v] == 0:
                del adj[u][v]
            stack.append(u)
        else:
            path.append(stack.pop())
    
    path.reverse()
    return path


def find_eulerian_path_directed(
    graph: Graph,
    start_node: Optional[str] = None
) -> Optional[list[str]]:
    """
    Find an Eulerian path in a directed graph using Hierholzer's algorithm.
    
    Args:
        graph: The Graph object (directed)
        start_node: Optional starting node
        
    Returns:
        List of node IDs forming the Eulerian path, or None if no path exists
    """
    has_path, has_circuit, starts, ends, _ = check_eulerian_directed(graph)
    
    if not has_path:
        return None
    
    if not graph.edges:
        if graph.nodes:
            return [graph.nodes[0].id]
        return []
    
    # Build adjacency with edge counts
    adj: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for node in graph.nodes:
        adj[node.id]
    for edge in graph.edges:
        adj[edge.source][edge.target] += 1
    
    # Determine starting node
    if start_node:
        if start_node not in adj:
            return None
        start = start_node
    elif starts:
        start = starts[0]
    else:
        # Find first node with outgoing edges
        start = None
        for node_id in adj:
            if adj[node_id]:
                start = node_id
                break
        if start is None:
            return [graph.nodes[0].id] if graph.nodes else []
    
    # Hierholzer's algorithm for directed graph
    stack = [start]
    path = []
    
    while stack:
        v = stack[-1]
        if adj[v]:
            u = next(iter(adj[v]))
            adj[v][u] -= 1
            if adj[v][u] == 0:
                del adj[v][u]
            stack.append(u)
        else:
            path.append(stack.pop())
    
    path.reverse()
    return path


def find_eulerian_path(
    graph: Graph,
    start_node: Optional[str] = None,
    end_node: Optional[str] = None
) -> EulerianResult:
    """
    Find an Eulerian path or circuit in the graph.
    
    Args:
        graph: The Graph object
        start_node: Optional required starting node
        end_node: Optional required ending node (for path)
        
    Returns:
        EulerianResult with the path (if found) and status
    """
    if graph.directed:
        path = find_eulerian_path_directed(graph, start_node)
    else:
        path = find_eulerian_path_undirected(graph, start_node)
    
    if path is None:
        # Get existence info for feedback
        result = check_eulerian_existence(graph, check_circuit=False)
        return result
    
    # Verify end node constraint if specified
    if end_node and path and path[-1] != end_node:
        return EulerianResult(
            exists=True,
            path=None,
            is_circuit=path[0] == path[-1] if len(path) > 1 else True,
            odd_degree_vertices=None
        )
    
    is_circuit = len(path) > 1 and path[0] == path[-1]
    
    return EulerianResult(
        exists=True,
        path=path,
        is_circuit=is_circuit,
        odd_degree_vertices=None
    )


def find_eulerian_circuit(
    graph: Graph,
    start_node: Optional[str] = None
) -> EulerianResult:
    """
    Find an Eulerian circuit in the graph.
    
    Args:
        graph: The Graph object
        start_node: Optional starting node (circuit will return here)
        
    Returns:
        EulerianResult with the circuit (if found) and status
    """
    # First check if circuit exists
    if graph.directed:
        has_path, has_circuit, starts, ends, reason = check_eulerian_directed(graph)
    else:
        has_path, has_circuit, odd_vertices, reason = check_eulerian_undirected(graph)
    
    if not has_circuit:
        if graph.directed:
            return EulerianResult(
                exists=False,
                is_circuit=True,
                odd_degree_vertices=starts + ends if starts or ends else None
            )
        else:
            return EulerianResult(
                exists=False,
                is_circuit=True,
                odd_degree_vertices=odd_vertices if odd_vertices else None
            )
    
    # Find the circuit
    result = find_eulerian_path(graph, start_node)
    if result.path:
        result.is_circuit = True
    return result


# =============================================================================
# EULERIAN PATH VERIFICATION
# =============================================================================

def verify_eulerian_path(
    graph: Graph,
    path: list[str],
    must_be_circuit: bool = False
) -> tuple[bool, str]:
    """
    Verify if a given path is a valid Eulerian path/circuit.
    
    Args:
        graph: The Graph object
        path: List of node IDs representing the path
        must_be_circuit: If True, verify it's a circuit (starts and ends at same node)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        if not graph.edges:
            return True, ""
        return False, "Empty path but graph has edges"
    
    if must_be_circuit and len(path) > 1 and path[0] != path[-1]:
        return False, f"Path is not a circuit: starts at {path[0]} but ends at {path[-1]}"
    
    # Build edge multiset
    edge_count: dict[tuple[str, str], int] = defaultdict(int)
    for edge in graph.edges:
        if graph.directed:
            edge_count[(edge.source, edge.target)] += 1
        else:
            # For undirected, normalize edge representation
            key = tuple(sorted([edge.source, edge.target]))
            edge_count[key] += 1
    
    # Check path uses each edge exactly once
    used_edges: dict[tuple[str, str], int] = defaultdict(int)
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        
        if graph.directed:
            key = (u, v)
        else:
            key = tuple(sorted([u, v]))
        
        used_edges[key] += 1
        
        if used_edges[key] > edge_count.get(key, 0):
            if graph.directed:
                return False, f"Edge ({u} -> {v}) used more times than it exists"
            else:
                return False, f"Edge ({u} -- {v}) used more times than it exists"
    
    # Check all edges are used
    for edge_key, count in edge_count.items():
        if used_edges.get(edge_key, 0) != count:
            if graph.directed:
                return False, f"Edge ({edge_key[0]} -> {edge_key[1]}) not used (or used wrong number of times)"
            else:
                return False, f"Edge ({edge_key[0]} -- {edge_key[1]}) not used (or used wrong number of times)"
    
    return True, ""


# =============================================================================
# HAMILTONIAN PATH/CIRCUIT - VERIFICATION
# =============================================================================

def verify_hamiltonian_path(
    graph: Graph,
    path: list[str],
    must_be_circuit: bool = False
) -> tuple[bool, str]:
    """
    Verify if a given path is a valid Hamiltonian path/circuit.
    
    A Hamiltonian path visits every vertex exactly once.
    A Hamiltonian circuit is a Hamiltonian path that returns to the start.
    
    Args:
        graph: The Graph object
        path: List of node IDs representing the path
        must_be_circuit: If True, verify it's a circuit
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        if not graph.nodes:
            return True, ""
        return False, "Empty path but graph has vertices"
    
    node_set = {node.id for node in graph.nodes}
    
    # For circuit, the path may include the start vertex at the end
    path_to_check = path
    if must_be_circuit and len(path) > 1 and path[0] == path[-1]:
        path_to_check = path[:-1]  # Remove the repeated end vertex for checking
    
    # Check all vertices are visited
    visited = set(path_to_check)
    
    if visited != node_set:
        missing = node_set - visited
        extra = visited - node_set
        if missing:
            return False, f"Path doesn't visit all vertices. Missing: {', '.join(list(missing)[:5])}"
        if extra:
            return False, f"Path contains vertices not in graph: {', '.join(list(extra)[:5])}"
    
    # Check no repeated vertices (except circuit end)
    if len(path_to_check) != len(set(path_to_check)):
        seen = set()
        for v in path_to_check:
            if v in seen:
                return False, f"Vertex {v} is visited more than once"
            seen.add(v)
    
    # Build adjacency for edge checking
    adj = build_adjacency_list(graph)
    
    # Check each consecutive pair has an edge
    full_path = path if must_be_circuit else path
    for i in range(len(full_path) - 1):
        u, v = full_path[i], full_path[i + 1]
        
        if graph.directed:
            # For directed, check directed edge exists
            edge_exists = False
            for edge in graph.edges:
                if edge.source == u and edge.target == v:
                    edge_exists = True
                    break
            if not edge_exists:
                return False, f"No edge from {u} to {v} in directed graph"
        else:
            # For undirected, check adjacency
            if v not in adj.get(u, set()):
                return False, f"No edge between {u} and {v}"
    
    # Check circuit condition
    if must_be_circuit:
        if len(path) <= 1:
            return False, "Circuit requires at least 2 vertices"
        if path[0] != path[-1]:
            # Check if there's an edge from last to first
            u, v = path[-1], path[0]
            if graph.directed:
                edge_exists = any(e.source == u and e.target == v for e in graph.edges)
            else:
                edge_exists = v in adj.get(u, set())
            if not edge_exists:
                return False, f"No edge from {u} back to {v} to complete the circuit"
    
    return True, ""


# =============================================================================
# HAMILTONIAN PATH/CIRCUIT - EXISTENCE CHECK (BACKTRACKING)
# =============================================================================

def find_hamiltonian_path_backtrack(
    graph: Graph,
    start_node: Optional[str] = None,
    end_node: Optional[str] = None,
    find_circuit: bool = False,
    timeout: float = 5.0
) -> tuple[Optional[list[str]], bool]:
    """
    Find a Hamiltonian path/circuit using backtracking with timeout.
    
    WARNING: This is NP-complete. Only practical for small graphs (≤10-12 nodes).
    
    Args:
        graph: The Graph object
        start_node: Optional required starting node
        end_node: Optional required ending node (for path)
        find_circuit: If True, find a circuit instead of path
        timeout: Maximum computation time in seconds
        
    Returns:
        Tuple of (path if found, timed_out flag)
    """
    if not graph.nodes:
        return [], False
    
    if len(graph.nodes) == 1:
        if find_circuit:
            # Single node circuit needs self-loop
            node_id = graph.nodes[0].id
            has_self_loop = any(e.source == node_id and e.target == node_id for e in graph.edges)
            if has_self_loop:
                return [node_id, node_id], False
            return None, False
        return [graph.nodes[0].id], False
    
    adj = build_adjacency_list(graph)
    node_ids = [node.id for node in graph.nodes]
    n = len(node_ids)
    
    start_time = time.time()
    timed_out = False
    
    def backtrack(path: list[str], visited: set[str]) -> Optional[list[str]]:
        nonlocal timed_out
        
        # Check timeout
        if time.time() - start_time > timeout:
            timed_out = True
            return None
        
        current = path[-1]
        
        # Check if we've visited all nodes
        if len(path) == n:
            if find_circuit:
                # Need edge back to start
                start = path[0]
                if graph.directed:
                    has_return = any(e.source == current and e.target == start for e in graph.edges)
                else:
                    has_return = start in adj.get(current, set())
                if has_return:
                    return path + [start]
                return None
            else:
                # Check end_node constraint
                if end_node and current != end_node:
                    return None
                return path
        
        # Try each unvisited neighbor
        for neighbor in adj.get(current, set()):
            if neighbor not in visited:
                # For directed graphs, verify edge direction
                if graph.directed:
                    edge_exists = any(e.source == current and e.target == neighbor for e in graph.edges)
                    if not edge_exists:
                        continue
                
                visited.add(neighbor)
                path.append(neighbor)
                
                result = backtrack(path, visited)
                if result is not None:
                    return result
                
                path.pop()
                visited.remove(neighbor)
        
        return None
    
    # Try starting from specified node or all nodes
    if start_node:
        if start_node not in adj:
            return None, False
        start_nodes = [start_node]
    else:
        start_nodes = node_ids
    
    for start in start_nodes:
        if timed_out:
            break
        result = backtrack([start], {start})
        if result is not None:
            return result, False
    
    return None, timed_out


def check_hamiltonian_existence(
    graph: Graph,
    find_circuit: bool = False,
    start_node: Optional[str] = None,
    end_node: Optional[str] = None,
    timeout: float = 5.0
) -> HamiltonianResult:
    """
    Check if a Hamiltonian path or circuit exists.
    
    Note: This is NP-complete. Results are reliable only for small graphs.
    For larger graphs, a timeout may occur, and the result will be inconclusive.
    
    Args:
        graph: The Graph object
        find_circuit: If True, check for circuit instead of path
        start_node: Optional required starting node
        end_node: Optional required ending node
        timeout: Maximum computation time in seconds
        
    Returns:
        HamiltonianResult with existence info
    """
    # Quick check: graph must have at least n-1 edges for path
    n = len(graph.nodes)
    if n > 1:
        min_edges = n if find_circuit else n - 1
        if len(graph.edges) < min_edges:
            return HamiltonianResult(
                exists=False,
                is_circuit=find_circuit,
                timed_out=False
            )
    
    path, timed_out = find_hamiltonian_path_backtrack(
        graph, start_node, end_node, find_circuit, timeout
    )
    
    if timed_out:
        return HamiltonianResult(
            exists=None,  # Inconclusive
            path=None,
            is_circuit=find_circuit,
            timed_out=True
        )
    
    return HamiltonianResult(
        exists=path is not None,
        path=path,
        is_circuit=find_circuit,
        timed_out=False
    )


# =============================================================================
# HIGH-LEVEL API FUNCTIONS
# =============================================================================

def evaluate_eulerian_path(
    graph: Graph,
    submitted_path: Optional[list[str]] = None,
    check_circuit: bool = False,
    start_node: Optional[str] = None,
    end_node: Optional[str] = None,
    check_existence_only: bool = False
) -> EulerianResult:
    """
    Evaluate an Eulerian path/circuit submission or find one.
    
    Args:
        graph: The Graph object
        submitted_path: Student's submitted path (if any)
        check_circuit: Whether to check for circuit specifically
        start_node: Required starting node (if any)
        end_node: Required ending node (if any)
        check_existence_only: If True, only check existence without finding path
        
    Returns:
        EulerianResult with evaluation details
    """
    # If path submitted, verify it
    if submitted_path is not None:
        is_valid, error = verify_eulerian_path(graph, submitted_path, check_circuit)
        
        # Also check start/end constraints
        if is_valid and start_node and submitted_path and submitted_path[0] != start_node:
            is_valid = False
            error = f"Path must start at {start_node}, but starts at {submitted_path[0]}"
        if is_valid and end_node and submitted_path and submitted_path[-1] != end_node:
            is_valid = False
            error = f"Path must end at {end_node}, but ends at {submitted_path[-1]}"
        
        if is_valid:
            is_circuit = len(submitted_path) > 1 and submitted_path[0] == submitted_path[-1]
            return EulerianResult(
                exists=True,
                path=submitted_path,
                is_circuit=is_circuit,
                odd_degree_vertices=None
            )
        else:
            # Get the correct answer for feedback
            result = check_eulerian_existence(graph, check_circuit)
            result.path = None  # Don't reveal answer
            return result
    
    # Check existence or find path
    if check_existence_only:
        return check_eulerian_existence(graph, check_circuit)
    
    if check_circuit:
        return find_eulerian_circuit(graph, start_node)
    else:
        return find_eulerian_path(graph, start_node, end_node)


def evaluate_hamiltonian_path(
    graph: Graph,
    submitted_path: Optional[list[str]] = None,
    check_circuit: bool = False,
    start_node: Optional[str] = None,
    end_node: Optional[str] = None,
    check_existence_only: bool = False,
    timeout: float = 5.0
) -> HamiltonianResult:
    """
    Evaluate a Hamiltonian path/circuit submission or find one.
    
    Args:
        graph: The Graph object
        submitted_path: Student's submitted path (if any)
        check_circuit: Whether to check for circuit specifically
        start_node: Required starting node (if any)
        end_node: Required ending node (if any)
        check_existence_only: If True, only check existence
        timeout: Max time for existence check (seconds)
        
    Returns:
        HamiltonianResult with evaluation details
    """
    # If path submitted, verify it
    if submitted_path is not None:
        is_valid, error = verify_hamiltonian_path(graph, submitted_path, check_circuit)
        
        # Check start/end constraints
        if is_valid and start_node and submitted_path and submitted_path[0] != start_node:
            is_valid = False
            error = f"Path must start at {start_node}"
        if is_valid and end_node and submitted_path:
            end_check = submitted_path[-1] if not check_circuit else submitted_path[-2] if len(submitted_path) > 1 else submitted_path[0]
            if end_check != end_node:
                is_valid = False
                error = f"Path must end at {end_node}"
        
        if is_valid:
            is_circuit = check_circuit or (len(submitted_path) > 1 and submitted_path[0] == submitted_path[-1])
            return HamiltonianResult(
                exists=True,
                path=submitted_path,
                is_circuit=is_circuit,
                timed_out=False
            )
        else:
            return HamiltonianResult(
                exists=None,  # We don't know without computing
                path=None,
                is_circuit=check_circuit,
                timed_out=False
            )
    
    # Check existence or find path
    return check_hamiltonian_existence(
        graph, check_circuit, start_node, end_node, timeout
    )


def get_eulerian_feedback(graph: Graph, check_circuit: bool = False) -> list[str]:
    """
    Get detailed feedback about why Eulerian path/circuit doesn't exist.
    
    Args:
        graph: The Graph object
        check_circuit: Whether checking for circuit
        
    Returns:
        List of feedback strings explaining the situation
    """
    feedback = []
    
    if graph.directed:
        has_path, has_circuit, starts, ends, reason = check_eulerian_directed(graph)
        in_deg, out_deg = get_in_out_degree(graph)
        
        if not is_weakly_connected_directed(graph):
            feedback.append("The graph is not connected (weakly). An Eulerian path/circuit requires all edges to be in a single connected component.")
            return feedback
        
        if check_circuit:
            if has_circuit:
                feedback.append("An Eulerian circuit exists! All vertices have equal in-degree and out-degree.")
            else:
                feedback.append("No Eulerian circuit exists.")
                # List imbalanced vertices
                for node_id in in_deg:
                    if in_deg[node_id] != out_deg[node_id]:
                        feedback.append(f"  - Vertex {node_id}: in-degree = {in_deg[node_id]}, out-degree = {out_deg[node_id]}")
                feedback.append("For a circuit, all vertices must have equal in-degree and out-degree.")
        else:
            if has_path:
                if has_circuit:
                    feedback.append("An Eulerian circuit (and thus path) exists!")
                else:
                    feedback.append(f"An Eulerian path exists from {starts[0]} to {ends[0]}.")
                    feedback.append("(Not a circuit because one vertex has out-degree > in-degree and one has in-degree > out-degree.)")
            else:
                feedback.append("No Eulerian path exists.")
                feedback.append(reason)
    else:
        has_path, has_circuit, odd_vertices, reason = check_eulerian_undirected(graph)
        adj = build_adjacency_list(graph)
        
        if not is_connected_undirected(graph):
            feedback.append("The graph is not connected. An Eulerian path/circuit requires all edges to be in a single connected component.")
            return feedback
        
        if check_circuit:
            if has_circuit:
                feedback.append("An Eulerian circuit exists! All vertices have even degree.")
            else:
                feedback.append("No Eulerian circuit exists.")
                for v in odd_vertices:
                    feedback.append(f"  - Vertex {v} has odd degree ({len(adj.get(v, set()))})")
                feedback.append("For a circuit, all vertices must have even degree.")
        else:
            if has_path:
                if has_circuit:
                    feedback.append("An Eulerian circuit (and thus path) exists!")
                else:
                    feedback.append(f"An Eulerian path exists between {odd_vertices[0]} and {odd_vertices[1]}.")
                    feedback.append("(These are the only vertices with odd degree.)")
            else:
                feedback.append("No Eulerian path exists.")
                feedback.append(f"Found {len(odd_vertices)} vertices with odd degree: {', '.join(odd_vertices[:5])}{'...' if len(odd_vertices) > 5 else ''}")
                feedback.append("An Eulerian path requires exactly 0 or 2 vertices with odd degree.")
    
    return feedback


def get_hamiltonian_feedback(
    graph: Graph,
    check_circuit: bool = False,
    result: Optional[HamiltonianResult] = None
) -> list[str]:
    """
    Get feedback about Hamiltonian path/circuit existence.
    
    Args:
        graph: The Graph object
        check_circuit: Whether checking for circuit
        result: Previous computation result (if available)
        
    Returns:
        List of feedback strings
    """
    feedback = []
    n = len(graph.nodes)
    m = len(graph.edges)
    
    if result and result.timed_out:
        feedback.append(f"Computation timed out. The graph has {n} vertices, which may be too large for exhaustive search.")
        feedback.append("Hamiltonian path/circuit is an NP-complete problem.")
        return feedback
    
    # Basic necessary conditions
    if n > 1:
        min_edges = n if check_circuit else n - 1
        if m < min_edges:
            feedback.append(f"Not enough edges. A {'Hamiltonian circuit' if check_circuit else 'Hamiltonian path'} requires at least {min_edges} edges, but graph has only {m}.")
            return feedback
    
    if result:
        if result.exists:
            feedback.append(f"A Hamiltonian {'circuit' if check_circuit else 'path'} exists!")
            if result.path:
                feedback.append(f"One such {'circuit' if check_circuit else 'path'}: {' -> '.join(result.path)}")
        elif result.exists is False:
            feedback.append(f"No Hamiltonian {'circuit' if check_circuit else 'path'} exists.")
            
            # Try to give some insight
            adj = build_adjacency_list(graph)
            min_degree = min(len(adj[v]) for v in adj) if adj else 0
            
            if check_circuit and n > 2:
                # Dirac's theorem: if min degree >= n/2, Hamiltonian circuit exists
                threshold = n // 2
                if min_degree < threshold:
                    feedback.append(f"Hint: Minimum vertex degree is {min_degree}, which is less than n/2 = {threshold}.")
                    feedback.append("(Dirac's theorem: graphs with min degree ≥ n/2 always have Hamiltonian circuits.)")
        else:
            feedback.append("Could not determine existence (computation may have timed out).")
    
    return feedback
