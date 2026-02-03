"""
Common Utilities for Graph Algorithms

This module contains shared helper functions and data structures used
across multiple graph algorithm modules.

Contents:
- UnionFind: Disjoint set union data structure
- Adjacency list builders (weighted and unweighted)
- Graph connectivity checks
- Degree calculations
"""

from typing import Optional
from collections import defaultdict, deque

from ..schemas.graph import Graph


# =============================================================================
# UNION-FIND DATA STRUCTURE
# =============================================================================

class UnionFind:
    """
    Union-Find (Disjoint Set Union) data structure with path compression
    and union by rank for efficient component tracking.
    """
    
    def __init__(self, nodes: list[str]):
        """
        Initialize Union-Find with given nodes.
        
        Args:
            nodes: List of node IDs
        """
        self.parent: dict[str, str] = {node: node for node in nodes}
        self.rank: dict[str, int] = {node: 0 for node in nodes}
    
    def find(self, x: str) -> str:
        """
        Find the root/representative of the set containing x.
        Uses path compression for efficiency.
        
        Args:
            x: Node ID to find root for
            
        Returns:
            Root node ID of the set containing x
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x: str, y: str) -> bool:
        """
        Union the sets containing x and y.
        Uses union by rank for efficiency.
        
        Args:
            x: First node ID
            y: Second node ID
            
        Returns:
            True if union was performed (nodes were in different sets),
            False if nodes were already in the same set
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False  # Already in same set
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True
    
    def connected(self, x: str, y: str) -> bool:
        """
        Check if two nodes are in the same set.
        
        Args:
            x: First node ID
            y: Second node ID
            
        Returns:
            True if nodes are in the same set, False otherwise
        """
        return self.find(x) == self.find(y)
    
    def get_components(self) -> list[set[str]]:
        """
        Get all connected components.
        
        Returns:
            List of sets, each containing node IDs in one component
        """
        components: dict[str, set[str]] = defaultdict(set)
        for node in self.parent:
            root = self.find(node)
            components[root].add(node)
        return list(components.values())


# =============================================================================
# ADJACENCY LIST BUILDERS
# =============================================================================

def build_adjacency_list(graph: Graph) -> dict[str, set[str]]:
    """
    Build an adjacency list representation from a Graph object.
    
    Args:
        graph: The Graph object
        
    Returns:
        Dictionary mapping node IDs to sets of neighbor node IDs
    """
    adj: dict[str, set[str]] = defaultdict(set)
    
    # Initialize all nodes (even isolated ones)
    for node in graph.nodes:
        if node.id not in adj:
            adj[node.id] = set()
    
    # Add edges
    for edge in graph.edges:
        adj[edge.source].add(edge.target)
        if not graph.directed:
            adj[edge.target].add(edge.source)
    
    return dict(adj)


def build_adjacency_list_weighted(graph: Graph) -> dict[str, list[tuple[str, float]]]:
    """
    Build a weighted adjacency list representation from a Graph object.
    
    Args:
        graph: The Graph object
        
    Returns:
        Dictionary mapping node IDs to lists of (neighbor_id, weight) tuples
    """
    adj: dict[str, list[tuple[str, float]]] = defaultdict(list)
    
    # Initialize all nodes (even isolated ones)
    for node in graph.nodes:
        if node.id not in adj:
            adj[node.id] = []
    
    # Add edges
    for edge in graph.edges:
        weight = edge.weight if edge.weight is not None else 1.0
        adj[edge.source].append((edge.target, weight))
        if not graph.directed:
            adj[edge.target].append((edge.source, weight))
    
    return dict(adj)


def build_adjacency_multiset(graph: Graph) -> dict[str, dict[str, int]]:
    """
    Build an adjacency multiset for multigraph support (counting edges).
    
    Args:
        graph: The Graph object
        
    Returns:
        Dictionary mapping node IDs to dictionaries of neighbor counts
    """
    adj: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    # Initialize all nodes
    for node in graph.nodes:
        if node.id not in adj:
            adj[node.id] = defaultdict(int)
    
    # Add edges (with multiplicity)
    for edge in graph.edges:
        adj[edge.source][edge.target] += 1
        if not graph.directed:
            adj[edge.target][edge.source] += 1
    
    return {k: dict(v) for k, v in adj.items()}


def build_edge_set(graph: Graph) -> set[tuple[str, str]]:
    """
    Build a set of edge tuples (normalized for undirected graphs).
    
    Args:
        graph: The Graph object
        
    Returns:
        Set of (source, target) tuples, normalized so source <= target for undirected
    """
    edges = set()
    for edge in graph.edges:
        if graph.directed:
            edges.add((edge.source, edge.target))
        else:
            # Normalize undirected edges
            edges.add(tuple(sorted([edge.source, edge.target])))
    return edges


# =============================================================================
# DEGREE CALCULATIONS
# =============================================================================

def get_degree(adj: dict[str, set[str]], node: str) -> int:
    """Get the degree of a node in an undirected graph."""
    return len(adj.get(node, set()))


def get_in_out_degree(graph: Graph) -> tuple[dict[str, int], dict[str, int]]:
    """
    Calculate in-degree and out-degree for each node in a directed graph.
    
    Args:
        graph: The Graph object (should be directed)
        
    Returns:
        Tuple of (in_degree dict, out_degree dict)
    """
    in_degree: dict[str, int] = defaultdict(int)
    out_degree: dict[str, int] = defaultdict(int)
    
    # Initialize all nodes
    for node in graph.nodes:
        in_degree[node.id] = 0
        out_degree[node.id] = 0
    
    # Count degrees
    for edge in graph.edges:
        out_degree[edge.source] += 1
        in_degree[edge.target] += 1
    
    return dict(in_degree), dict(out_degree)


# =============================================================================
# CONNECTIVITY CHECKS
# =============================================================================

def is_connected(graph: Graph, include_isolated: bool = True) -> bool:
    """
    Check if an undirected graph is connected.
    
    Args:
        graph: The Graph object
        include_isolated: If True, isolated vertices must also be connected.
                         If False, only checks connectivity of non-isolated vertices.
        
    Returns:
        True if connected according to the criteria
    """
    if not graph.nodes:
        return True
    
    adj = build_adjacency_list(graph)
    
    if include_isolated:
        # All nodes must be reachable from the start
        start = graph.nodes[0].id
    else:
        # Find first non-isolated vertex
        start = None
        for node_id in adj:
            if adj[node_id]:
                start = node_id
                break
        
        # If no edges, graph is trivially connected
        if start is None:
            return True
    
    # BFS from start
    visited = set()
    queue = deque([start])
    visited.add(start)
    
    while queue:
        node = queue.popleft()
        for neighbor in adj.get(node, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    if include_isolated:
        return len(visited) == len(graph.nodes)
    else:
        # Check all non-isolated vertices are visited
        for node_id in adj:
            if adj[node_id] and node_id not in visited:
                return False
        return True


def is_weakly_connected(graph: Graph) -> bool:
    """
    Check if a directed graph is weakly connected.
    (Connected when treating edges as undirected)
    
    Args:
        graph: The Graph object
        
    Returns:
        True if weakly connected
    """
    if not graph.nodes:
        return True
    
    # Build undirected version
    adj: dict[str, set[str]] = defaultdict(set)
    for node in graph.nodes:
        adj[node.id] = set()
    for edge in graph.edges:
        adj[edge.source].add(edge.target)
        adj[edge.target].add(edge.source)
    
    # Find first non-isolated vertex
    start = None
    for node_id in adj:
        if adj[node_id]:
            start = node_id
            break
    
    if start is None:
        return True
    
    # BFS
    visited = set()
    queue = deque([start])
    visited.add(start)
    
    while queue:
        node = queue.popleft()
        for neighbor in adj[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    for node_id in adj:
        if adj[node_id] and node_id not in visited:
            return False
    
    return True


def count_components(graph: Graph) -> int:
    """
    Count the number of connected components in the graph.
    
    Args:
        graph: The Graph object
        
    Returns:
        Number of connected components
    """
    if not graph.nodes:
        return 0
    
    node_ids = [node.id for node in graph.nodes]
    uf = UnionFind(node_ids)
    
    for edge in graph.edges:
        uf.union(edge.source, edge.target)
    
    return len(uf.get_components())


# =============================================================================
# EDGE WEIGHT UTILITIES
# =============================================================================

def get_edge_weight(graph: Graph, source: str, target: str) -> Optional[float]:
    """
    Get the weight of an edge between two nodes.
    
    Args:
        graph: The Graph object
        source: Source node ID
        target: Target node ID
        
    Returns:
        Edge weight, or None if edge doesn't exist
    """
    for edge in graph.edges:
        if graph.directed:
            if edge.source == source and edge.target == target:
                return edge.weight if edge.weight is not None else 1.0
        else:
            if (edge.source == source and edge.target == target) or \
               (edge.source == target and edge.target == source):
                return edge.weight if edge.weight is not None else 1.0
    return None


__all__ = [
    # Union-Find
    "UnionFind",
    
    # Adjacency builders
    "build_adjacency_list",
    "build_adjacency_list_weighted",
    "build_adjacency_multiset",
    "build_edge_set",
    
    # Degree calculations
    "get_degree",
    "get_in_out_degree",
    
    # Connectivity
    "is_connected",
    "is_weakly_connected",
    "count_components",
    
    # Edge utilities
    "get_edge_weight",
]
