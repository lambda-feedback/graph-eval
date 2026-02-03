"""
Minimum Spanning Tree Algorithms

This module implements MST algorithms and verification:
- Kruskal's algorithm with union-find data structure
- Prim's algorithm with priority queue
- MST verification (checking if a tree is spanning and minimum weight)
- Support for both algorithms with auto-selection
- Graceful handling of disconnected graphs

All algorithms work with the Graph schema defined in schemas.graph.
"""

from typing import Optional, Literal
from collections import defaultdict
import heapq

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.graph import Graph, Node, Edge
from schemas.result import TreeResult, VisualizationData
from .utils import (
    UnionFind,
    build_adjacency_list_weighted,
    build_edge_set,
    get_edge_weight,
    is_connected,
    count_components,
)


# =============================================================================
# GRAPH CONNECTIVITY (MST-specific wrapper)
# =============================================================================

def is_graph_connected(graph: Graph) -> bool:
    """
    Check if the graph is connected (for undirected graphs).
    
    Args:
        graph: The Graph object
        
    Returns:
        True if graph is connected, False otherwise
    """
    return is_connected(graph, include_isolated=True)


# =============================================================================
# KRUSKAL'S ALGORITHM
# =============================================================================

def kruskal_mst(graph: Graph) -> tuple[list[Edge], float, bool]:
    """
    Find MST using Kruskal's algorithm with union-find.
    
    Kruskal's algorithm sorts all edges by weight and adds them one by one,
    skipping edges that would create a cycle.
    
    Args:
        graph: The Graph object (should be undirected and connected)
        
    Returns:
        Tuple of (MST edges, total weight, is_connected)
        If graph is disconnected, returns minimum spanning forest
    """
    if not graph.nodes:
        return [], 0.0, True
    
    if len(graph.nodes) == 1:
        return [], 0.0, True
    
    node_ids = [node.id for node in graph.nodes]
    uf = UnionFind(node_ids)
    
    # Sort edges by weight
    edges_with_weight = []
    for edge in graph.edges:
        weight = edge.weight if edge.weight is not None else 1.0
        edges_with_weight.append((weight, edge))
    
    edges_with_weight.sort(key=lambda x: x[0])
    
    mst_edges: list[Edge] = []
    total_weight = 0.0
    
    for weight, edge in edges_with_weight:
        if uf.union(edge.source, edge.target):
            mst_edges.append(edge)
            total_weight += weight
            
            # MST has n-1 edges for n nodes
            if len(mst_edges) == len(graph.nodes) - 1:
                break
    
    # Check if graph is connected (MST should have n-1 edges)
    is_connected = len(mst_edges) == len(graph.nodes) - 1
    
    return mst_edges, total_weight, is_connected


# =============================================================================
# PRIM'S ALGORITHM
# =============================================================================

def prim_mst(graph: Graph, start_node: Optional[str] = None) -> tuple[list[Edge], float, bool]:
    """
    Find MST using Prim's algorithm with priority queue.
    
    Prim's algorithm grows the MST from a starting vertex, always adding
    the minimum weight edge that connects the tree to a new vertex.
    
    Args:
        graph: The Graph object (should be undirected and connected)
        start_node: Optional starting node ID (defaults to first node)
        
    Returns:
        Tuple of (MST edges, total weight, is_connected)
        If graph is disconnected, returns MST of the component containing start_node
    """
    if not graph.nodes:
        return [], 0.0, True
    
    if len(graph.nodes) == 1:
        return [], 0.0, True
    
    adj = build_adjacency_list_weighted(graph)
    
    # Start from given node or first node
    if start_node is None:
        start_node = graph.nodes[0].id
    elif start_node not in adj:
        raise ValueError(f"Start node '{start_node}' not found in graph")
    
    # Track visited nodes and MST edges
    visited: set[str] = set()
    mst_edges: list[Edge] = []
    total_weight = 0.0
    
    # Priority queue: (weight, from_node, to_node)
    # Using counter to break ties consistently
    counter = 0
    pq: list[tuple[float, int, str, str]] = []
    
    # Start from the starting node
    visited.add(start_node)
    for neighbor, weight in adj.get(start_node, []):
        heapq.heappush(pq, (weight, counter, start_node, neighbor))
        counter += 1
    
    while pq and len(visited) < len(graph.nodes):
        weight, _, from_node, to_node = heapq.heappop(pq)
        
        if to_node in visited:
            continue
        
        # Add edge to MST
        visited.add(to_node)
        mst_edges.append(Edge(source=from_node, target=to_node, weight=weight))
        total_weight += weight
        
        # Add new edges to priority queue
        for neighbor, edge_weight in adj.get(to_node, []):
            if neighbor not in visited:
                heapq.heappush(pq, (edge_weight, counter, to_node, neighbor))
                counter += 1
    
    # Check if all nodes were visited (connected graph)
    is_connected = len(visited) == len(graph.nodes)
    
    return mst_edges, total_weight, is_connected


# =============================================================================
# MST COMPUTATION WITH AUTO-SELECTION
# =============================================================================

def compute_mst(
    graph: Graph,
    algorithm: Literal["kruskal", "prim", "auto"] = "auto",
    start_node: Optional[str] = None
) -> tuple[list[Edge], float, bool, str]:
    """
    Compute MST using specified or auto-selected algorithm.
    
    Auto-selection heuristic:
    - For dense graphs (edges > nodes * log(nodes)), use Prim's
    - For sparse graphs, use Kruskal's
    
    Args:
        graph: The Graph object
        algorithm: Algorithm to use ("kruskal", "prim", or "auto")
        start_node: Starting node for Prim's algorithm
        
    Returns:
        Tuple of (MST edges, total weight, is_connected, algorithm_used)
    """
    if algorithm == "auto":
        # Auto-select based on graph density
        n = len(graph.nodes)
        m = len(graph.edges)
        
        if n == 0:
            return [], 0.0, True, "none"
        
        # Use Prim's for dense graphs, Kruskal's for sparse
        import math
        threshold = n * math.log(n + 1) if n > 0 else 0
        
        if m > threshold:
            algorithm = "prim"
        else:
            algorithm = "kruskal"
    
    if algorithm == "kruskal":
        edges, weight, connected = kruskal_mst(graph)
        return edges, weight, connected, "kruskal"
    else:
        edges, weight, connected = prim_mst(graph, start_node)
        return edges, weight, connected, "prim"


# =============================================================================
# MST VERIFICATION
# =============================================================================

def verify_spanning_tree(
    graph: Graph,
    tree_edges: list[Edge]
) -> tuple[bool, Optional[str]]:
    """
    Verify if given edges form a valid spanning tree of the graph.
    
    A valid spanning tree must:
    1. Be a subgraph of the original graph
    2. Include all vertices
    3. Have exactly n-1 edges (for n vertices)
    4. Be connected (no cycles)
    
    Args:
        graph: The original Graph object
        tree_edges: List of edges claimed to be a spanning tree
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    n = len(graph.nodes)
    
    # Empty graph case
    if n == 0:
        return len(tree_edges) == 0, "Empty graph should have empty tree"
    
    # Single node case
    if n == 1:
        return len(tree_edges) == 0, "Single node should have no edges"
    
    # Check edge count
    if len(tree_edges) != n - 1:
        return False, f"Spanning tree should have {n-1} edges, got {len(tree_edges)}"
    
    # Build set of valid edges from original graph
    valid_edges = build_edge_set(graph)
    
    # Check all tree edges are valid graph edges
    node_ids = {node.id for node in graph.nodes}
    tree_node_ids: set[str] = set()
    
    for edge in tree_edges:
        # Check nodes exist
        if edge.source not in node_ids:
            return False, f"Node '{edge.source}' not in graph"
        if edge.target not in node_ids:
            return False, f"Node '{edge.target}' not in graph"
        
        tree_node_ids.add(edge.source)
        tree_node_ids.add(edge.target)
        
        # Check edge exists in graph
        edge_tuple = tuple(sorted([edge.source, edge.target]))
        if edge_tuple not in valid_edges:
            return False, f"Edge ({edge.source}, {edge.target}) not in graph"
    
    # Check all nodes are covered
    if tree_node_ids != node_ids:
        missing = node_ids - tree_node_ids
        return False, f"Tree doesn't span all nodes, missing: {missing}"
    
    # Check for connectivity (use union-find to detect if it forms a tree)
    uf = UnionFind(list(node_ids))
    for edge in tree_edges:
        if not uf.union(edge.source, edge.target):
            return False, f"Tree contains a cycle (edge {edge.source}-{edge.target} creates cycle)"
    
    return True, None


def verify_mst(
    graph: Graph,
    tree_edges: list[Edge],
    tolerance: float = 1e-9
) -> TreeResult:
    """
    Verify if given edges form a valid minimum spanning tree.
    
    Verification steps:
    1. Check if it's a valid spanning tree
    2. Compute its total weight
    3. Compare with actual MST weight
    
    Args:
        graph: The original Graph object
        tree_edges: List of edges claimed to be MST
        tolerance: Tolerance for weight comparison
        
    Returns:
        TreeResult with verification details
    """
    # First check if it's a valid spanning tree
    is_spanning, error = verify_spanning_tree(graph, tree_edges)
    
    # Convert edges to proper format for TreeResult
    edges_for_result = [
        Edge(**e.model_dump()) if hasattr(e, 'model_dump') else e
        for e in tree_edges
    ]
    
    if not is_spanning:
        return TreeResult(
            is_tree=False,
            is_spanning_tree=False,
            is_mst=False,
            total_weight=None,
            edges=edges_for_result
        )
    
    # Calculate submitted tree weight
    submitted_weight = 0.0
    for edge in tree_edges:
        weight = get_edge_weight(graph, edge.source, edge.target)
        if weight is None:
            # Use edge's own weight if available
            weight = edge.weight if edge.weight is not None else 1.0
        submitted_weight += weight
    
    # Compute actual MST weight
    mst_edges, mst_weight, is_connected, _ = compute_mst(graph)
    
    # Compare weights
    is_mst = abs(submitted_weight - mst_weight) <= tolerance
    
    return TreeResult(
        is_tree=True,
        is_spanning_tree=True,
        is_mst=is_mst,
        total_weight=submitted_weight,
        edges=edges_for_result
    )


def verify_mst_edges(
    graph: Graph,
    submitted_edges: list[tuple[str, str]] | list[Edge],
    tolerance: float = 1e-9
) -> TreeResult:
    """
    Verify MST given as list of edge tuples or Edge objects.
    
    Args:
        graph: The original Graph object
        submitted_edges: Edges as tuples (source, target) or Edge objects
        tolerance: Tolerance for weight comparison
        
    Returns:
        TreeResult with verification details
    """
    # Convert tuples to Edge objects if needed
    edges: list[Edge] = []
    for e in submitted_edges:
        # Check if it's an Edge-like object (has source and target attributes)
        if hasattr(e, 'source') and hasattr(e, 'target'):
            edges.append(e)
        elif isinstance(e, (tuple, list)) and len(e) >= 2:
            weight = get_edge_weight(graph, e[0], e[1])
            edges.append(Edge(source=e[0], target=e[1], weight=weight))
        else:
            raise ValueError(f"Invalid edge format: {e}")
    
    return verify_mst(graph, edges, tolerance)


# =============================================================================
# DISCONNECTED GRAPH HANDLING
# =============================================================================

def compute_minimum_spanning_forest(graph: Graph) -> tuple[list[list[Edge]], float, int]:
    """
    Compute minimum spanning forest for a potentially disconnected graph.
    
    A minimum spanning forest is a collection of MSTs, one for each
    connected component.
    
    Args:
        graph: The Graph object (may be disconnected)
        
    Returns:
        Tuple of (list of MSTs per component, total weight, number of components)
    """
    if not graph.nodes:
        return [], 0.0, 0
    
    # Find connected components using union-find
    node_ids = [node.id for node in graph.nodes]
    uf = UnionFind(node_ids)
    
    for edge in graph.edges:
        uf.union(edge.source, edge.target)
    
    components = uf.get_components()
    
    # Build MST for each component
    forest: list[list[Edge]] = []
    total_weight = 0.0
    
    for component in components:
        if len(component) == 1:
            # Single node component has no edges
            forest.append([])
            continue
        
        # Create subgraph for this component
        component_nodes = [Node(id=nid) for nid in component]
        # Convert edges to dicts for proper Pydantic model creation
        component_edges = [
            Edge(**edge.model_dump()) if hasattr(edge, 'model_dump') else edge
            for edge in graph.edges
            if edge.source in component and edge.target in component
        ]
        
        subgraph = Graph(
            nodes=component_nodes,
            edges=component_edges,
            directed=graph.directed,
            weighted=graph.weighted
        )
        
        # Compute MST for component
        mst_edges, weight, _, _ = compute_mst(subgraph)
        forest.append(mst_edges)
        total_weight += weight
    
    return forest, total_weight, len(components)


# =============================================================================
# VISUALIZATION SUPPORT
# =============================================================================

def get_mst_visualization(
    graph: Graph,
    mst_edges: list[Edge],
    highlight_color: str = "#00ff00"
) -> VisualizationData:
    """
    Generate visualization data for MST edges.
    
    Args:
        graph: The original Graph object
        mst_edges: MST edges to highlight
        highlight_color: Color for MST edges
        
    Returns:
        VisualizationData for UI rendering
    """
    # Get all nodes involved in MST
    mst_nodes = set()
    for edge in mst_edges:
        mst_nodes.add(edge.source)
        mst_nodes.add(edge.target)
    
    # Create edge color mapping
    edge_colors: dict[str, str] = {}
    for i, edge in enumerate(mst_edges):
        edge_id = edge.id if edge.id else f"mst_e{i}"
        edge_colors[edge_id] = highlight_color
    
    # Convert edges to proper format for VisualizationData
    edges_for_viz = [
        Edge(**e.model_dump()) if hasattr(e, 'model_dump') else e
        for e in mst_edges
    ]
    
    return VisualizationData(
        highlight_nodes=list(mst_nodes),
        highlight_edges=edges_for_viz,
        edge_colors=edge_colors
    )


def get_mst_animation_steps(
    graph: Graph,
    algorithm: Literal["kruskal", "prim"] = "kruskal"
) -> list[dict]:
    """
    Generate step-by-step animation for MST construction.
    
    Args:
        graph: The Graph object
        algorithm: Algorithm to animate
        
    Returns:
        List of animation steps with state information
    """
    steps = []
    
    if algorithm == "kruskal":
        steps = _animate_kruskal(graph)
    else:
        steps = _animate_prim(graph)
    
    return steps


def _animate_kruskal(graph: Graph) -> list[dict]:
    """Generate Kruskal's algorithm animation steps."""
    steps = []
    
    if not graph.nodes or len(graph.nodes) <= 1:
        return steps
    
    node_ids = [node.id for node in graph.nodes]
    uf = UnionFind(node_ids)
    
    # Sort edges by weight
    edges_with_weight = []
    for edge in graph.edges:
        weight = edge.weight if edge.weight is not None else 1.0
        edges_with_weight.append((weight, edge))
    
    edges_with_weight.sort(key=lambda x: x[0])
    
    mst_edges: list[Edge] = []
    total_weight = 0.0
    
    steps.append({
        "step": 0,
        "description": "Initialize: Sort all edges by weight",
        "sorted_edges": [(w, e.source, e.target) for w, e in edges_with_weight],
        "mst_edges": [],
        "total_weight": 0.0,
        "components": [list(c) for c in uf.get_components()]
    })
    
    step_num = 1
    for weight, edge in edges_with_weight:
        considering = {
            "step": step_num,
            "description": f"Consider edge ({edge.source}, {edge.target}) with weight {weight}",
            "current_edge": (edge.source, edge.target, weight),
            "mst_edges": [(e.source, e.target) for e in mst_edges],
            "total_weight": total_weight
        }
        
        if uf.union(edge.source, edge.target):
            mst_edges.append(edge)
            total_weight += weight
            considering["action"] = "ADD"
            considering["reason"] = "Connects two different components"
        else:
            considering["action"] = "SKIP"
            considering["reason"] = "Would create a cycle"
        
        considering["components"] = [list(c) for c in uf.get_components()]
        considering["mst_edges_after"] = [(e.source, e.target) for e in mst_edges]
        considering["total_weight_after"] = total_weight
        
        steps.append(considering)
        step_num += 1
        
        if len(mst_edges) == len(graph.nodes) - 1:
            break
    
    steps.append({
        "step": step_num,
        "description": "MST complete",
        "mst_edges": [(e.source, e.target) for e in mst_edges],
        "total_weight": total_weight,
        "final": True
    })
    
    return steps


def _animate_prim(graph: Graph) -> list[dict]:
    """Generate Prim's algorithm animation steps."""
    steps = []
    
    if not graph.nodes or len(graph.nodes) <= 1:
        return steps
    
    adj = build_adjacency_list_weighted(graph)
    start_node = graph.nodes[0].id
    
    visited: set[str] = set()
    mst_edges: list[Edge] = []
    total_weight = 0.0
    
    counter = 0
    pq: list[tuple[float, int, str, str]] = []
    
    visited.add(start_node)
    for neighbor, weight in adj.get(start_node, []):
        heapq.heappush(pq, (weight, counter, start_node, neighbor))
        counter += 1
    
    steps.append({
        "step": 0,
        "description": f"Start from node {start_node}",
        "visited": [start_node],
        "priority_queue": [(w, f, t) for w, _, f, t in sorted(pq)],
        "mst_edges": [],
        "total_weight": 0.0
    })
    
    step_num = 1
    while pq and len(visited) < len(graph.nodes):
        weight, _, from_node, to_node = heapq.heappop(pq)
        
        step_info = {
            "step": step_num,
            "description": f"Process edge ({from_node}, {to_node}) with weight {weight}",
            "current_edge": (from_node, to_node, weight),
            "visited_before": list(visited),
            "mst_edges": [(e.source, e.target) for e in mst_edges],
            "total_weight": total_weight
        }
        
        if to_node in visited:
            step_info["action"] = "SKIP"
            step_info["reason"] = f"Node {to_node} already in tree"
            step_info["visited_after"] = list(visited)
            steps.append(step_info)
            step_num += 1
            continue
        
        visited.add(to_node)
        mst_edges.append(Edge(source=from_node, target=to_node, weight=weight))
        total_weight += weight
        
        step_info["action"] = "ADD"
        step_info["reason"] = f"Node {to_node} not yet in tree"
        step_info["visited_after"] = list(visited)
        step_info["mst_edges_after"] = [(e.source, e.target) for e in mst_edges]
        step_info["total_weight_after"] = total_weight
        
        for neighbor, edge_weight in adj.get(to_node, []):
            if neighbor not in visited:
                heapq.heappush(pq, (edge_weight, counter, to_node, neighbor))
                counter += 1
        
        step_info["priority_queue_after"] = [(w, f, t) for w, _, f, t in sorted(pq)]
        steps.append(step_info)
        step_num += 1
    
    steps.append({
        "step": step_num,
        "description": "MST complete",
        "mst_edges": [(e.source, e.target) for e in mst_edges],
        "total_weight": total_weight,
        "visited": list(visited),
        "final": True
    })
    
    return steps


# =============================================================================
# HIGH-LEVEL API
# =============================================================================

def find_mst(
    graph: Graph,
    algorithm: Literal["kruskal", "prim", "auto"] = "auto",
    start_node: Optional[str] = None
) -> TreeResult:
    """
    Find minimum spanning tree and return result.
    
    Args:
        graph: The Graph object
        algorithm: Algorithm to use
        start_node: Starting node for Prim's algorithm
        
    Returns:
        TreeResult with MST details
    """
    # Check connectivity
    is_connected = is_graph_connected(graph)
    
    if not is_connected:
        # Return info about disconnected graph
        forest, total_weight, num_components = compute_minimum_spanning_forest(graph)
        all_edges = [edge for component_edges in forest for edge in component_edges]
        
        # Convert edges to proper format for TreeResult
        edges_for_result = [
            Edge(**e.model_dump()) if hasattr(e, 'model_dump') else e
            for e in all_edges
        ]
        
        return TreeResult(
            is_tree=False,
            is_spanning_tree=False,
            is_mst=False,
            total_weight=total_weight,
            edges=edges_for_result
        )
    
    # Compute MST
    mst_edges, total_weight, connected, algorithm_used = compute_mst(
        graph, algorithm, start_node
    )
    
    # Convert edges to proper format for TreeResult
    edges_for_result = [
        Edge(**e.model_dump()) if hasattr(e, 'model_dump') else e
        for e in mst_edges
    ]
    
    return TreeResult(
        is_tree=True,
        is_spanning_tree=True,
        is_mst=True,
        total_weight=total_weight,
        edges=edges_for_result
    )


def evaluate_mst_submission(
    graph: Graph,
    submitted_edges: list[Edge] | list[tuple[str, str]],
    tolerance: float = 1e-9
) -> TreeResult:
    """
    Evaluate a student's MST submission.
    
    Args:
        graph: The original Graph object
        submitted_edges: Student's submitted MST edges
        tolerance: Tolerance for weight comparison
        
    Returns:
        TreeResult with evaluation details
    """
    return verify_mst_edges(graph, submitted_edges, tolerance)
