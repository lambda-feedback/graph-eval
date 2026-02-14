"""
Graph Coloring Algorithms

This module implements various graph coloring algorithms:
- k-coloring verification
- Greedy coloring algorithm
- DSatur (Degree of Saturation) algorithm
- Chromatic number computation (backtracking for small graphs)
- Edge coloring support

All algorithms work with the Graph schema defined in schemas.graph.
"""

from typing import Optional
from collections import defaultdict

from ..schemas.graph import Graph, Node, Edge
from ..schemas.result import ColoringResult
from .utils import build_adjacency_list


def build_line_graph_adjacency(graph: Graph) -> tuple[dict[str, set[str]], dict[str, tuple[str, str]]]:
    """
    Build adjacency list for the line graph (used for edge coloring).
    
    In the line graph, each edge becomes a vertex, and two vertices are
    adjacent if their corresponding edges share a common endpoint.
    
    Args:
        graph: The Graph object
        
    Returns:
        Tuple of (adjacency list, edge_id to (source, target) mapping)
    """
    # Create unique IDs for edges
    edge_ids: dict[str, tuple[str, str]] = {}
    edges_at_node: dict[str, list[str]] = defaultdict(list)
    
    for i, edge in enumerate(graph.edges):
        edge_id = edge.id if edge.id else f"e{i}"
        edge_ids[edge_id] = (edge.source, edge.target)
        edges_at_node[edge.source].append(edge_id)
        edges_at_node[edge.target].append(edge_id)
    
    # Build line graph adjacency
    line_adj: dict[str, set[str]] = defaultdict(set)
    
    for edge_id in edge_ids:
        line_adj[edge_id] = set()
    
    # Two edges are adjacent in line graph if they share a vertex
    for node_id, incident_edges in edges_at_node.items():
        for i, e1 in enumerate(incident_edges):
            for e2 in incident_edges[i+1:]:
                line_adj[e1].add(e2)
                line_adj[e2].add(e1)
    
    return dict(line_adj), edge_ids


# =============================================================================
# COLORING VERIFICATION
# =============================================================================

def verify_vertex_coloring(
    graph: Graph,
    coloring: dict[str, int],
    k: Optional[int] = None
) -> ColoringResult:
    """
    Verify if a vertex coloring is valid.
    
    A valid vertex coloring assigns colors to vertices such that no two
    adjacent vertices have the same color.
    
    Args:
        graph: The Graph object
        coloring: Dictionary mapping node IDs to color integers
        k: Maximum number of colors allowed (optional)
        
    Returns:
        ColoringResult with validation details
    """
    adj = build_adjacency_list(graph)
    conflicts: list[tuple[str, str]] = []
    node_ids = {node.id for node in graph.nodes}
    
    # Check all nodes are colored
    uncolored = node_ids - set(coloring.keys())
    if uncolored:
        return ColoringResult(
            is_valid_coloring=False,
            coloring=coloring,
            num_colors_used=len(set(coloring.values())) if coloring else 0,
            chromatic_number=None,
            conflicts=[(n, "UNCOLORED") for n in uncolored]
        )
    
    # Check for conflicts (adjacent nodes with same color)
    checked_edges = set()
    for node_id in coloring:
        if node_id not in adj:
            continue
        for neighbor in adj[node_id]:
            edge_key = tuple(sorted([node_id, neighbor]))
            if edge_key in checked_edges:
                continue
            checked_edges.add(edge_key)
            
            if neighbor in coloring and coloring[node_id] == coloring[neighbor]:
                conflicts.append((node_id, neighbor))
    
    colors_used = set(coloring.values())
    num_colors = len(colors_used)
    
    # Check k-coloring constraint
    is_valid = len(conflicts) == 0
    if k is not None and num_colors > k:
        is_valid = False
    
    return ColoringResult(
        is_valid_coloring=is_valid,
        coloring=coloring,
        num_colors_used=num_colors,
        chromatic_number=None,
        conflicts=conflicts if conflicts else None
    )


def detect_coloring_conflicts(
    graph: Graph,
    coloring: dict[str, int]
) -> list[tuple[str, str]]:
    """
    Detect all coloring conflicts in a vertex coloring.
    
    Args:
        graph: The Graph object
        coloring: Dictionary mapping node IDs to color integers
        
    Returns:
        List of (node1, node2) tuples representing conflicting edges
    """
    result = verify_vertex_coloring(graph, coloring)
    return result.conflicts or []


def verify_edge_coloring(
    graph: Graph,
    edge_coloring: dict[str, int],
    k: Optional[int] = None
) -> ColoringResult:
    """
    Verify if an edge coloring is valid.
    
    A valid edge coloring assigns colors to edges such that no two
    edges sharing a common vertex have the same color.
    
    Args:
        graph: The Graph object
        edge_coloring: Dictionary mapping edge IDs to color integers
        k: Maximum number of colors allowed (optional)
        
    Returns:
        ColoringResult with validation details
    """
    line_adj, edge_ids = build_line_graph_adjacency(graph)
    conflicts: list[tuple[str, str]] = []
    
    # Check all edges are colored
    uncolored = set(edge_ids.keys()) - set(edge_coloring.keys())
    if uncolored:
        return ColoringResult(
            is_valid_coloring=False,
            coloring=edge_coloring,
            num_colors_used=len(set(edge_coloring.values())) if edge_coloring else 0,
            chromatic_number=None,
            conflicts=[(e, "UNCOLORED") for e in uncolored]
        )
    
    # Check for conflicts (adjacent edges with same color)
    checked_pairs = set()
    for edge_id in edge_coloring:
        if edge_id not in line_adj:
            continue
        for neighbor_edge in line_adj[edge_id]:
            pair_key = tuple(sorted([edge_id, neighbor_edge]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            
            if neighbor_edge in edge_coloring and edge_coloring[edge_id] == edge_coloring[neighbor_edge]:
                conflicts.append((edge_id, neighbor_edge))
    
    colors_used = set(edge_coloring.values())
    num_colors = len(colors_used)
    
    # Check k-coloring constraint
    is_valid = len(conflicts) == 0
    if k is not None and num_colors > k:
        is_valid = False
    
    return ColoringResult(
        is_valid_coloring=is_valid,
        coloring=edge_coloring,
        num_colors_used=num_colors,
        chromatic_number=None,
        conflicts=conflicts if conflicts else None
    )


def detect_edge_coloring_conflicts(
    graph: Graph,
    edge_coloring: dict[str, int]
) -> list[tuple[str, str]]:
    """
    Detect all coloring conflicts in an edge coloring.
    
    Args:
        graph: The Graph object
        edge_coloring: Dictionary mapping edge IDs to color integers
        
    Returns:
        List of (edge1, edge2) tuples representing conflicting edge pairs
    """
    result = verify_edge_coloring(graph, edge_coloring)
    return result.conflicts or []


# =============================================================================
# GREEDY COLORING ALGORITHM
# =============================================================================

def greedy_coloring(
    graph: Graph,
    order: Optional[list[str]] = None
) -> dict[str, int]:
    """
    Color a graph using the greedy algorithm.
    
    The greedy algorithm colors vertices one by one, always choosing the
    smallest available color that doesn't conflict with neighbors.
    
    Args:
        graph: The Graph object
        order: Optional custom ordering of vertices (default: order in graph)
        
    Returns:
        Dictionary mapping node IDs to color integers (0-indexed)
    """
    adj = build_adjacency_list(graph)
    
    if order is None:
        order = [node.id for node in graph.nodes]
    
    coloring: dict[str, int] = {}
    
    for node_id in order:
        # Find colors used by neighbors
        neighbor_colors = set()
        if node_id in adj:
            for neighbor in adj[node_id]:
                if neighbor in coloring:
                    neighbor_colors.add(coloring[neighbor])
        
        # Find smallest available color
        color = 0
        while color in neighbor_colors:
            color += 1
        
        coloring[node_id] = color
    
    return coloring


# =============================================================================
# DSATUR ALGORITHM
# =============================================================================

def dsatur_coloring(graph: Graph) -> dict[str, int]:
    """
    Color a graph using the DSatur (Degree of Saturation) algorithm.
    
    DSatur is a heuristic that typically produces better colorings than
    simple greedy. It always colors the vertex with the highest saturation
    degree (number of distinct colors in neighbors), breaking ties by
    choosing the vertex with highest degree.
    
    Args:
        graph: The Graph object
        
    Returns:
        Dictionary mapping node IDs to color integers (0-indexed)
    """
    adj = build_adjacency_list(graph)
    n = len(graph.nodes)
    
    if n == 0:
        return {}
    
    coloring: dict[str, int] = {}
    # saturation[node] = set of colors used by colored neighbors
    saturation: dict[str, set[int]] = {node.id: set() for node in graph.nodes}
    # degree of each node
    degrees = {node_id: len(neighbors) for node_id, neighbors in adj.items()}
    
    # Use a max-heap to efficiently get the node with highest saturation
    # Heap entries: (-saturation_degree, -degree, node_id)
    # Negative because heapq is a min-heap
    uncolored = set(node.id for node in graph.nodes)
    
    while uncolored:
        # Find uncolored vertex with max saturation, break ties with degree
        best_node = None
        best_sat = -1
        best_deg = -1
        
        for node_id in uncolored:
            sat = len(saturation[node_id])
            deg = degrees.get(node_id, 0)
            if sat > best_sat or (sat == best_sat and deg > best_deg):
                best_sat = sat
                best_deg = deg
                best_node = node_id
        
        if best_node is None:
            break
        
        # Find smallest available color for best_node
        neighbor_colors = saturation[best_node]
        color = 0
        while color in neighbor_colors:
            color += 1
        
        coloring[best_node] = color
        uncolored.remove(best_node)
        
        # Update saturation of uncolored neighbors
        for neighbor in adj.get(best_node, set()):
            if neighbor in uncolored:
                saturation[neighbor].add(color)
    
    return coloring


# =============================================================================
# EDGE COLORING ALGORITHMS
# =============================================================================

def greedy_edge_coloring(graph: Graph) -> dict[str, int]:
    """
    Color edges of a graph using a greedy algorithm.
    
    This colors edges so that no two edges sharing a vertex have the same color.
    
    Args:
        graph: The Graph object
        
    Returns:
        Dictionary mapping edge IDs to color integers (0-indexed)
    """
    edge_coloring: dict[str, int] = {}
    
    # Track colors used at each vertex
    colors_at_vertex: dict[str, set[int]] = defaultdict(set)
    
    for i, edge in enumerate(graph.edges):
        edge_id = edge.id if edge.id else f"e{i}"
        
        # Colors forbidden at both endpoints
        forbidden = colors_at_vertex[edge.source] | colors_at_vertex[edge.target]
        
        # Find smallest available color
        color = 0
        while color in forbidden:
            color += 1
        
        edge_coloring[edge_id] = color
        colors_at_vertex[edge.source].add(color)
        colors_at_vertex[edge.target].add(color)
    
    return edge_coloring


# =============================================================================
# CHROMATIC NUMBER COMPUTATION
# =============================================================================

def compute_chromatic_number(
    graph: Graph,
    max_nodes: int = 10
) -> Optional[int]:
    """
    Compute the chromatic number of a graph using backtracking.
    
    The chromatic number is the minimum number of colors needed to color
    the graph. This uses a backtracking algorithm that is only practical
    for small graphs.
    
    Args:
        graph: The Graph object
        max_nodes: Maximum number of nodes to attempt (default 10)
        
    Returns:
        The chromatic number, or None if graph is too large
    """
    n = len(graph.nodes)
    
    if n == 0:
        return 0
    
    if n > max_nodes:
        return None
    
    adj = build_adjacency_list(graph)
    node_ids = [node.id for node in graph.nodes]
    node_index = {node_id: i for i, node_id in enumerate(node_ids)}
    
    # Try coloring with k colors for increasing k
    def can_color_with_k(k: int) -> bool:
        """Check if graph can be colored with k colors using backtracking."""
        colors = [-1] * n
        
        def is_safe(node_idx: int, color: int) -> bool:
            """Check if assigning color to node is safe."""
            node_id = node_ids[node_idx]
            for neighbor in adj.get(node_id, set()):
                neighbor_idx = node_index[neighbor]
                if colors[neighbor_idx] == color:
                    return False
            return True
        
        def backtrack(node_idx: int) -> bool:
            """Try to color nodes starting from node_idx."""
            if node_idx == n:
                return True
            
            for color in range(k):
                if is_safe(node_idx, color):
                    colors[node_idx] = color
                    if backtrack(node_idx + 1):
                        return True
                    colors[node_idx] = -1
            
            return False
        
        return backtrack(0)
    
    # Binary search for chromatic number
    # Lower bound: 1 (if graph is empty) or 2 (if has edges) or clique size
    # Upper bound: n or max_degree + 1
    
    # Calculate max degree
    max_degree = max((len(neighbors) for neighbors in adj.values()), default=0)
    
    # If no edges, chromatic number is 1
    if len(graph.edges) == 0:
        return 1
    
    # Try from 1 upward
    for k in range(1, n + 1):
        if can_color_with_k(k):
            return k
    
    return n  # Worst case


def compute_chromatic_index(
    graph: Graph,
    max_edges: int = 15
) -> Optional[int]:
    """
    Compute the chromatic index (edge chromatic number) of a graph.
    
    The chromatic index is the minimum number of colors needed to color
    the edges. By Vizing's theorem, it's either Δ or Δ+1 where Δ is the
    maximum degree.
    
    Args:
        graph: The Graph object
        max_edges: Maximum number of edges to attempt (default 15)
        
    Returns:
        The chromatic index, or None if graph is too large
    """
    m = len(graph.edges)
    
    if m == 0:
        return 0
    
    if m > max_edges:
        return None
    
    line_adj, edge_ids = build_line_graph_adjacency(graph)
    edge_list = list(edge_ids.keys())
    edge_index = {eid: i for i, eid in enumerate(edge_list)}
    n_edges = len(edge_list)
    
    def can_color_edges_with_k(k: int) -> bool:
        """Check if edges can be colored with k colors."""
        colors = [-1] * n_edges
        
        def is_safe(edge_idx: int, color: int) -> bool:
            edge_id = edge_list[edge_idx]
            for neighbor_edge in line_adj.get(edge_id, set()):
                neighbor_idx = edge_index[neighbor_edge]
                if colors[neighbor_idx] == color:
                    return False
            return True
        
        def backtrack(edge_idx: int) -> bool:
            if edge_idx == n_edges:
                return True
            
            for color in range(k):
                if is_safe(edge_idx, color):
                    colors[edge_idx] = color
                    if backtrack(edge_idx + 1):
                        return True
                    colors[edge_idx] = -1
            
            return False
        
        return backtrack(0)
    
    # Calculate max degree
    adj = build_adjacency_list(graph)
    max_degree = max((len(neighbors) for neighbors in adj.values()), default=0)
    
    # By Vizing's theorem, chromatic index is either Δ or Δ+1
    if can_color_edges_with_k(max_degree):
        return max_degree
    else:
        return max_degree + 1


# =============================================================================
# HIGH-LEVEL COLORING FUNCTIONS
# =============================================================================

def color_graph(
    graph: Graph,
    algorithm: str = "auto",
    k: Optional[int] = None
) -> ColoringResult:
    """
    Color a graph using the specified algorithm.
    
    Args:
        graph: The Graph object
        algorithm: "greedy", "dsatur", "backtracking", or "auto"
        k: Number of colors to use (optional, only for backtracking)
        
    Returns:
        ColoringResult with the coloring and details
    """
    if algorithm == "auto":
        # Use DSatur for better results
        algorithm = "dsatur"
    
    if algorithm == "greedy":
        coloring = greedy_coloring(graph)
    elif algorithm == "dsatur":
        coloring = dsatur_coloring(graph)
    elif algorithm == "backtracking":
        # For backtracking, we find the chromatic number and color with that
        chi = compute_chromatic_number(graph)
        if chi is None:
            # Fall back to DSatur for large graphs
            coloring = dsatur_coloring(graph)
        else:
            # Use backtracking to find an optimal coloring with chi colors
            adj = build_adjacency_list(graph)
            node_ids = [node.id for node in graph.nodes]
            node_index = {node_id: i for i, node_id in enumerate(node_ids)}
            n = len(node_ids)
            colors = [-1] * n
            
            def is_safe(node_idx: int, color: int) -> bool:
                """Check if assigning color to node is safe."""
                node_id = node_ids[node_idx]
                for neighbor in adj.get(node_id, set()):
                    neighbor_idx = node_index[neighbor]
                    if colors[neighbor_idx] == color:
                        return False
                return True
            
            def backtrack(node_idx: int) -> bool:
                """Try to color nodes starting from node_idx."""
                if node_idx == n:
                    return True
                
                for color in range(chi):
                    if is_safe(node_idx, color):
                        colors[node_idx] = color
                        if backtrack(node_idx + 1):
                            return True
                        colors[node_idx] = -1
                
                return False
            
            if backtrack(0):
                coloring = {node_ids[i]: colors[i] for i in range(n)}
            else:
                # Should not happen if chi is correct, but fallback to DSatur
                coloring = dsatur_coloring(graph)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    num_colors = len(set(coloring.values())) if coloring else 0
    
    # Verify the coloring
    result = verify_vertex_coloring(graph, coloring, k)
    
    return result


def color_edges(graph: Graph) -> ColoringResult:
    """
    Color edges of a graph.
    
    Args:
        graph: The Graph object
        
    Returns:
        ColoringResult with the edge coloring and details
    """
    edge_coloring = greedy_edge_coloring(graph)
    return verify_edge_coloring(graph, edge_coloring)
