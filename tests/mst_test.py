"""
Unit Tests for Minimum Spanning Tree Algorithms

This module contains comprehensive tests for:
- Kruskal's algorithm with union-find
- Prim's algorithm with priority queue
- MST verification (spanning tree and minimum weight)
- Auto-selection of algorithm
- Disconnected graph handling
- Visualization support

Test graph types include:
- Empty graphs
- Single vertex graphs
- Simple paths
- Complete graphs (Kn)
- Cycle graphs
- Tree graphs
- Disconnected graphs
- Graphs with equal weight edges
- Negative weight edges
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation_function.schemas.graph import Graph, Node, Edge
from evaluation_function.algorithms.mst import (
    # Union-Find
    UnionFind,
    
    # Helper functions
    build_adjacency_list_weighted,
    build_edge_set,
    get_edge_weight,
    is_graph_connected,
    count_components,
    
    # Kruskal's algorithm
    kruskal_mst,
    
    # Prim's algorithm
    prim_mst,
    
    # MST computation
    compute_mst,
    
    # Verification
    verify_spanning_tree,
    verify_mst,
    verify_mst_edges,
    
    # Disconnected handling
    compute_minimum_spanning_forest,
    
    # Visualization
    get_mst_visualization,
    get_mst_animation_steps,
    
    # High-level API
    find_mst,
    evaluate_mst_submission,
)


# =============================================================================
# TEST GRAPH FIXTURES
# =============================================================================

@pytest.fixture
def empty_graph():
    """Empty graph with no nodes or edges."""
    return Graph(nodes=[], edges=[])


@pytest.fixture
def single_vertex_graph():
    """Graph with a single vertex and no edges."""
    return Graph(
        nodes=[Node(id="A")],
        edges=[]
    )


@pytest.fixture
def two_vertex_graph():
    """Graph with two vertices connected by an edge."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B")],
        edges=[Edge(source="A", target="B", weight=5.0)]
    )


@pytest.fixture
def simple_path_graph():
    """Simple path graph A-B-C-D."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=2.0),
            Edge(source="C", target="D", weight=3.0)
        ]
    )


@pytest.fixture
def triangle_graph():
    """Triangle graph with different weights."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=2.0),
            Edge(source="A", target="C", weight=3.0)
        ]
    )


@pytest.fixture
def k4_weighted_graph():
    """Complete graph K4 with weights."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="A", target="C", weight=4.0),
            Edge(source="A", target="D", weight=3.0),
            Edge(source="B", target="C", weight=2.0),
            Edge(source="B", target="D", weight=5.0),
            Edge(source="C", target="D", weight=6.0)
        ],
        weighted=True
    )


@pytest.fixture
def cycle_graph_4():
    """Cycle graph C4 with weights."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=2.0),
            Edge(source="C", target="D", weight=3.0),
            Edge(source="D", target="A", weight=4.0)
        ]
    )


@pytest.fixture
def disconnected_graph():
    """Graph with two disconnected components."""
    return Graph(
        nodes=[
            Node(id="A"), Node(id="B"), Node(id="C"),  # Component 1
            Node(id="D"), Node(id="E")                  # Component 2
        ],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=2.0),
            Edge(source="D", target="E", weight=3.0)
        ]
    )


@pytest.fixture
def disconnected_with_isolate():
    """Graph with a component and an isolated node."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=2.0)
        ]
        # Node D is isolated
    )


@pytest.fixture
def equal_weight_graph():
    """Graph where all edges have equal weight."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="A", target="C", weight=1.0),
            Edge(source="A", target="D", weight=1.0),
            Edge(source="B", target="C", weight=1.0),
            Edge(source="B", target="D", weight=1.0),
            Edge(source="C", target="D", weight=1.0)
        ]
    )


@pytest.fixture
def negative_weight_graph():
    """Graph with negative edge weights."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
        edges=[
            Edge(source="A", target="B", weight=-2.0),
            Edge(source="B", target="C", weight=3.0),
            Edge(source="A", target="C", weight=1.0)
        ]
    )


@pytest.fixture
def classic_mst_graph():
    """
    Classic MST example graph:
        1       4
    A ----- B ----- C
    |       |       |
   2|      3|      1|
    |       |       |
    D ----- E ----- F
        5       2
    
    MST should have weight 1+2+3+1+2 = 9
    """
    return Graph(
        nodes=[
            Node(id="A"), Node(id="B"), Node(id="C"),
            Node(id="D"), Node(id="E"), Node(id="F")
        ],
        edges=[
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=4.0),
            Edge(source="A", target="D", weight=2.0),
            Edge(source="B", target="E", weight=3.0),
            Edge(source="C", target="F", weight=1.0),
            Edge(source="D", target="E", weight=5.0),
            Edge(source="E", target="F", weight=2.0)
        ],
        weighted=True
    )


@pytest.fixture
def large_graph():
    """Larger graph for performance testing."""
    nodes = [Node(id=str(i)) for i in range(20)]
    edges = []
    # Create a connected graph with various weights
    for i in range(19):
        edges.append(Edge(source=str(i), target=str(i+1), weight=float(i+1)))
    # Add some extra edges
    for i in range(0, 18, 2):
        edges.append(Edge(source=str(i), target=str(i+2), weight=float(i+10)))
    
    return Graph(nodes=nodes, edges=edges, weighted=True)


# =============================================================================
# UNION-FIND TESTS
# =============================================================================

class TestUnionFind:
    """Tests for Union-Find data structure."""
    
    def test_initialization(self):
        """Test Union-Find initialization."""
        uf = UnionFind(["A", "B", "C"])
        assert uf.find("A") == "A"
        assert uf.find("B") == "B"
        assert uf.find("C") == "C"
    
    def test_union_basic(self):
        """Test basic union operation."""
        uf = UnionFind(["A", "B", "C"])
        assert uf.union("A", "B") == True
        assert uf.connected("A", "B") == True
        assert uf.connected("A", "C") == False
    
    def test_union_already_connected(self):
        """Test union returns False when already connected."""
        uf = UnionFind(["A", "B", "C"])
        uf.union("A", "B")
        assert uf.union("A", "B") == False
    
    def test_transitive_connectivity(self):
        """Test transitive connectivity after unions."""
        uf = UnionFind(["A", "B", "C", "D"])
        uf.union("A", "B")
        uf.union("C", "D")
        assert uf.connected("A", "C") == False
        uf.union("B", "C")
        assert uf.connected("A", "D") == True
    
    def test_get_components(self):
        """Test getting connected components."""
        uf = UnionFind(["A", "B", "C", "D", "E"])
        uf.union("A", "B")
        uf.union("C", "D")
        
        components = uf.get_components()
        assert len(components) == 3
        
        # Convert to comparable format
        component_sets = [frozenset(c) for c in components]
        assert frozenset(["A", "B"]) in component_sets
        assert frozenset(["C", "D"]) in component_sets
        assert frozenset(["E"]) in component_sets
    
    def test_path_compression(self):
        """Test that path compression works (find should flatten tree)."""
        uf = UnionFind(["A", "B", "C", "D"])
        uf.union("A", "B")
        uf.union("B", "C")
        uf.union("C", "D")
        
        # After find with path compression, all should point to same root
        root = uf.find("D")
        assert uf.find("A") == root
        assert uf.find("B") == root
        assert uf.find("C") == root


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_build_adjacency_list_weighted(self, triangle_graph):
        """Test building weighted adjacency list."""
        adj = build_adjacency_list_weighted(triangle_graph)
        
        assert "A" in adj
        assert "B" in adj
        assert "C" in adj
        
        # Check A's neighbors
        a_neighbors = {(n, w) for n, w in adj["A"]}
        assert ("B", 1.0) in a_neighbors
        assert ("C", 3.0) in a_neighbors
    
    def test_build_edge_set(self, triangle_graph):
        """Test building edge set."""
        edges = build_edge_set(triangle_graph)
        
        assert ("A", "B") in edges or ("B", "A") in edges
        assert ("A", "C") in edges or ("C", "A") in edges
        assert ("B", "C") in edges or ("C", "B") in edges
    
    def test_get_edge_weight(self, triangle_graph):
        """Test getting edge weight."""
        assert get_edge_weight(triangle_graph, "A", "B") == 1.0
        assert get_edge_weight(triangle_graph, "B", "A") == 1.0  # Undirected
        assert get_edge_weight(triangle_graph, "A", "C") == 3.0
        assert get_edge_weight(triangle_graph, "A", "D") is None  # Non-existent
    
    def test_is_graph_connected_true(self, triangle_graph):
        """Test connectivity check for connected graph."""
        assert is_graph_connected(triangle_graph) == True
    
    def test_is_graph_connected_false(self, disconnected_graph):
        """Test connectivity check for disconnected graph."""
        assert is_graph_connected(disconnected_graph) == False
    
    def test_is_graph_connected_empty(self, empty_graph):
        """Test connectivity check for empty graph."""
        assert is_graph_connected(empty_graph) == True
    
    def test_is_graph_connected_single(self, single_vertex_graph):
        """Test connectivity check for single vertex."""
        assert is_graph_connected(single_vertex_graph) == True
    
    def test_count_components(self, disconnected_graph):
        """Test component counting."""
        assert count_components(disconnected_graph) == 2
    
    def test_count_components_connected(self, triangle_graph):
        """Test component counting for connected graph."""
        assert count_components(triangle_graph) == 1
    
    def test_count_components_with_isolate(self, disconnected_with_isolate):
        """Test component counting with isolated node."""
        assert count_components(disconnected_with_isolate) == 2


# =============================================================================
# KRUSKAL'S ALGORITHM TESTS
# =============================================================================

class TestKruskalMST:
    """Tests for Kruskal's algorithm."""
    
    def test_empty_graph(self, empty_graph):
        """Test Kruskal's on empty graph."""
        edges, weight, connected = kruskal_mst(empty_graph)
        assert edges == []
        assert weight == 0.0
        assert connected == True
    
    def test_single_vertex(self, single_vertex_graph):
        """Test Kruskal's on single vertex graph."""
        edges, weight, connected = kruskal_mst(single_vertex_graph)
        assert edges == []
        assert weight == 0.0
        assert connected == True
    
    def test_two_vertices(self, two_vertex_graph):
        """Test Kruskal's on two vertex graph."""
        edges, weight, connected = kruskal_mst(two_vertex_graph)
        assert len(edges) == 1
        assert weight == 5.0
        assert connected == True
    
    def test_triangle(self, triangle_graph):
        """Test Kruskal's on triangle graph."""
        edges, weight, connected = kruskal_mst(triangle_graph)
        assert len(edges) == 2
        assert weight == 3.0  # 1 + 2
        assert connected == True
    
    def test_k4_weighted(self, k4_weighted_graph):
        """Test Kruskal's on K4 with weights."""
        edges, weight, connected = kruskal_mst(k4_weighted_graph)
        assert len(edges) == 3
        assert weight == 6.0  # 1 + 2 + 3
        assert connected == True
    
    def test_cycle_graph(self, cycle_graph_4):
        """Test Kruskal's on cycle graph."""
        edges, weight, connected = kruskal_mst(cycle_graph_4)
        assert len(edges) == 3
        assert weight == 6.0  # 1 + 2 + 3 (removes heaviest edge 4)
        assert connected == True
    
    def test_disconnected(self, disconnected_graph):
        """Test Kruskal's on disconnected graph."""
        edges, weight, connected = kruskal_mst(disconnected_graph)
        # Returns minimum spanning forest
        assert len(edges) == 3  # 2 + 1 edges for two components
        assert weight == 6.0  # 1 + 2 + 3
        assert connected == False
    
    def test_classic_mst(self, classic_mst_graph):
        """Test Kruskal's on classic MST example."""
        edges, weight, connected = kruskal_mst(classic_mst_graph)
        assert len(edges) == 5  # n-1 edges
        assert weight == 9.0  # 1 + 2 + 3 + 1 + 2
        assert connected == True
    
    def test_equal_weights(self, equal_weight_graph):
        """Test Kruskal's with equal weight edges."""
        edges, weight, connected = kruskal_mst(equal_weight_graph)
        assert len(edges) == 3
        assert weight == 3.0  # 3 edges * 1.0 each
        assert connected == True
    
    def test_negative_weights(self, negative_weight_graph):
        """Test Kruskal's with negative weights."""
        edges, weight, connected = kruskal_mst(negative_weight_graph)
        assert len(edges) == 2
        # MST will pick the two smallest weights: -2 and 1 = -1
        assert weight == -1.0
        assert connected == True


# =============================================================================
# PRIM'S ALGORITHM TESTS
# =============================================================================

class TestPrimMST:
    """Tests for Prim's algorithm."""
    
    def test_empty_graph(self, empty_graph):
        """Test Prim's on empty graph."""
        edges, weight, connected = prim_mst(empty_graph)
        assert edges == []
        assert weight == 0.0
        assert connected == True
    
    def test_single_vertex(self, single_vertex_graph):
        """Test Prim's on single vertex graph."""
        edges, weight, connected = prim_mst(single_vertex_graph)
        assert edges == []
        assert weight == 0.0
        assert connected == True
    
    def test_two_vertices(self, two_vertex_graph):
        """Test Prim's on two vertex graph."""
        edges, weight, connected = prim_mst(two_vertex_graph)
        assert len(edges) == 1
        assert weight == 5.0
        assert connected == True
    
    def test_triangle(self, triangle_graph):
        """Test Prim's on triangle graph."""
        edges, weight, connected = prim_mst(triangle_graph)
        assert len(edges) == 2
        assert weight == 3.0  # 1 + 2
        assert connected == True
    
    def test_k4_weighted(self, k4_weighted_graph):
        """Test Prim's on K4 with weights."""
        edges, weight, connected = prim_mst(k4_weighted_graph)
        assert len(edges) == 3
        assert weight == 6.0  # 1 + 2 + 3
        assert connected == True
    
    def test_cycle_graph(self, cycle_graph_4):
        """Test Prim's on cycle graph."""
        edges, weight, connected = prim_mst(cycle_graph_4)
        assert len(edges) == 3
        assert weight == 6.0  # 1 + 2 + 3
        assert connected == True
    
    def test_disconnected(self, disconnected_graph):
        """Test Prim's on disconnected graph."""
        # Prim's only builds MST for reachable component
        edges, weight, connected = prim_mst(disconnected_graph)
        assert connected == False
        # Only reaches one component from start
        assert len(edges) == 2
    
    def test_classic_mst(self, classic_mst_graph):
        """Test Prim's on classic MST example."""
        edges, weight, connected = prim_mst(classic_mst_graph)
        assert len(edges) == 5  # n-1 edges
        assert weight == 9.0
        assert connected == True
    
    def test_start_node(self, triangle_graph):
        """Test Prim's with specified start node."""
        edges1, weight1, _ = prim_mst(triangle_graph, start_node="A")
        edges2, weight2, _ = prim_mst(triangle_graph, start_node="C")
        
        # Both should produce same total weight
        assert weight1 == weight2 == 3.0
    
    def test_invalid_start_node(self, triangle_graph):
        """Test Prim's with invalid start node."""
        with pytest.raises(ValueError):
            prim_mst(triangle_graph, start_node="Z")


# =============================================================================
# MST COMPUTATION WITH AUTO-SELECTION TESTS
# =============================================================================

class TestComputeMST:
    """Tests for compute_mst with auto-selection."""
    
    def test_auto_selection(self, classic_mst_graph):
        """Test auto algorithm selection."""
        edges, weight, connected, algorithm = compute_mst(classic_mst_graph, "auto")
        assert weight == 9.0
        assert connected == True
        assert algorithm in ["kruskal", "prim"]
    
    def test_force_kruskal(self, classic_mst_graph):
        """Test forcing Kruskal's algorithm."""
        edges, weight, connected, algorithm = compute_mst(classic_mst_graph, "kruskal")
        assert weight == 9.0
        assert algorithm == "kruskal"
    
    def test_force_prim(self, classic_mst_graph):
        """Test forcing Prim's algorithm."""
        edges, weight, connected, algorithm = compute_mst(classic_mst_graph, "prim")
        assert weight == 9.0
        assert algorithm == "prim"
    
    def test_both_algorithms_same_weight(self, k4_weighted_graph):
        """Test that both algorithms produce same total weight."""
        _, weight_k, _, _ = compute_mst(k4_weighted_graph, "kruskal")
        _, weight_p, _, _ = compute_mst(k4_weighted_graph, "prim")
        assert weight_k == weight_p


# =============================================================================
# MST VERIFICATION TESTS
# =============================================================================

class TestVerifySpanningTree:
    """Tests for spanning tree verification."""
    
    def test_valid_spanning_tree(self, triangle_graph):
        """Test valid spanning tree verification."""
        tree_edges = [
            Edge(source="A", target="B"),
            Edge(source="B", target="C")
        ]
        is_valid, error = verify_spanning_tree(triangle_graph, tree_edges)
        assert is_valid == True
        assert error is None
    
    def test_wrong_edge_count(self, triangle_graph):
        """Test spanning tree with wrong number of edges."""
        tree_edges = [
            Edge(source="A", target="B")
        ]
        is_valid, error = verify_spanning_tree(triangle_graph, tree_edges)
        assert is_valid == False
        assert "2 edges" in error
    
    def test_non_graph_edge(self, triangle_graph):
        """Test spanning tree with edge not in graph."""
        tree_edges = [
            Edge(source="A", target="B"),
            Edge(source="A", target="D")  # D doesn't exist
        ]
        is_valid, error = verify_spanning_tree(triangle_graph, tree_edges)
        assert is_valid == False
    
    def test_cycle_in_tree(self, triangle_graph):
        """Test spanning tree with cycle."""
        tree_edges = [
            Edge(source="A", target="B"),
            Edge(source="B", target="C"),
            Edge(source="A", target="C")  # Creates cycle
        ]
        # This has wrong edge count anyway
        is_valid, error = verify_spanning_tree(triangle_graph, tree_edges)
        assert is_valid == False
    
    def test_empty_graph_empty_tree(self, empty_graph):
        """Test empty graph with empty tree."""
        is_valid, _ = verify_spanning_tree(empty_graph, [])
        assert is_valid == True
    
    def test_single_vertex_no_edges(self, single_vertex_graph):
        """Test single vertex with no edges."""
        is_valid, _ = verify_spanning_tree(single_vertex_graph, [])
        assert is_valid == True


class TestVerifyMST:
    """Tests for MST verification."""
    
    def test_valid_mst(self, triangle_graph):
        """Test valid MST verification."""
        mst_edges = [
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=2.0)
        ]
        result = verify_mst(triangle_graph, mst_edges)
        assert result.is_tree == True
        assert result.is_spanning_tree == True
        assert result.is_mst == True
        assert result.total_weight == 3.0
    
    def test_valid_spanning_not_minimum(self, triangle_graph):
        """Test valid spanning tree that is not minimum."""
        # This is a valid spanning tree but not minimum
        tree_edges = [
            Edge(source="A", target="B", weight=1.0),
            Edge(source="A", target="C", weight=3.0)  # Using heavier edge
        ]
        result = verify_mst(triangle_graph, tree_edges)
        assert result.is_tree == True
        assert result.is_spanning_tree == True
        assert result.is_mst == False  # Weight is 4, not 3
        assert result.total_weight == 4.0
    
    def test_invalid_spanning_tree(self, triangle_graph):
        """Test invalid spanning tree verification."""
        tree_edges = [
            Edge(source="A", target="B")
        ]
        result = verify_mst(triangle_graph, tree_edges)
        assert result.is_tree == False
        assert result.is_spanning_tree == False
        assert result.is_mst == False
    
    def test_k4_mst(self, k4_weighted_graph):
        """Test MST verification for K4."""
        # Correct MST edges: A-B (1), B-C (2), A-D (3)
        mst_edges = [
            Edge(source="A", target="B", weight=1.0),
            Edge(source="B", target="C", weight=2.0),
            Edge(source="A", target="D", weight=3.0)
        ]
        result = verify_mst(k4_weighted_graph, mst_edges)
        assert result.is_mst == True
        assert result.total_weight == 6.0


class TestVerifyMSTEdges:
    """Tests for verify_mst_edges with different input formats."""
    
    def test_edge_tuples(self, triangle_graph):
        """Test verification with edge tuples."""
        edges = [("A", "B"), ("B", "C")]
        result = verify_mst_edges(triangle_graph, edges)
        assert result.is_mst == True
    
    def test_edge_objects(self, triangle_graph):
        """Test verification with Edge objects."""
        edges = [
            Edge(source="A", target="B"),
            Edge(source="B", target="C")
        ]
        result = verify_mst_edges(triangle_graph, edges)
        assert result.is_mst == True
    
    def test_invalid_edge_format(self, triangle_graph):
        """Test verification with invalid edge format."""
        with pytest.raises(ValueError):
            verify_mst_edges(triangle_graph, ["invalid"])


# =============================================================================
# DISCONNECTED GRAPH TESTS
# =============================================================================

class TestDisconnectedGraphs:
    """Tests for disconnected graph handling."""
    
    def test_minimum_spanning_forest(self, disconnected_graph):
        """Test minimum spanning forest computation."""
        forest, total_weight, num_components = compute_minimum_spanning_forest(disconnected_graph)
        
        assert num_components == 2
        assert total_weight == 6.0  # (1 + 2) + 3
        assert len(forest) == 2
    
    def test_forest_with_isolate(self, disconnected_with_isolate):
        """Test forest with isolated node."""
        forest, total_weight, num_components = compute_minimum_spanning_forest(disconnected_with_isolate)
        
        assert num_components == 2
        # One component has edges, one is isolated
        total_edges = sum(len(f) for f in forest)
        assert total_edges == 2  # A-B, B-C
    
    def test_empty_graph_forest(self, empty_graph):
        """Test forest of empty graph."""
        forest, total_weight, num_components = compute_minimum_spanning_forest(empty_graph)
        
        assert num_components == 0
        assert total_weight == 0.0
        assert forest == []
    
    def test_find_mst_disconnected(self, disconnected_graph):
        """Test find_mst on disconnected graph."""
        result = find_mst(disconnected_graph)
        
        assert result.is_tree == False
        assert result.is_spanning_tree == False
        assert result.is_mst == False


# =============================================================================
# VISUALIZATION TESTS
# =============================================================================

class TestVisualization:
    """Tests for visualization support."""
    
    def test_get_mst_visualization(self, triangle_graph):
        """Test MST visualization data generation."""
        mst_edges = [
            Edge(source="A", target="B"),
            Edge(source="B", target="C")
        ]
        viz = get_mst_visualization(triangle_graph, mst_edges)
        
        assert len(viz.highlight_nodes) == 3
        assert len(viz.highlight_edges) == 2
        assert "A" in viz.highlight_nodes
        assert "B" in viz.highlight_nodes
        assert "C" in viz.highlight_nodes
    
    def test_animation_steps_kruskal(self, triangle_graph):
        """Test Kruskal animation steps."""
        steps = get_mst_animation_steps(triangle_graph, "kruskal")
        
        assert len(steps) > 0
        assert steps[0]["step"] == 0  # Initialization step
        assert steps[-1].get("final", False) == True
    
    def test_animation_steps_prim(self, triangle_graph):
        """Test Prim animation steps."""
        steps = get_mst_animation_steps(triangle_graph, "prim")
        
        assert len(steps) > 0
        assert steps[0]["step"] == 0  # Initialization step
        assert steps[-1].get("final", False) == True
    
    def test_animation_empty_graph(self, empty_graph):
        """Test animation on empty graph."""
        steps = get_mst_animation_steps(empty_graph, "kruskal")
        assert steps == []


# =============================================================================
# HIGH-LEVEL API TESTS
# =============================================================================

class TestHighLevelAPI:
    """Tests for high-level API functions."""
    
    def test_find_mst(self, classic_mst_graph):
        """Test find_mst function."""
        result = find_mst(classic_mst_graph)
        
        assert result.is_tree == True
        assert result.is_spanning_tree == True
        assert result.is_mst == True
        assert result.total_weight == 9.0
        assert len(result.edges) == 5
    
    def test_find_mst_with_algorithm(self, classic_mst_graph):
        """Test find_mst with specific algorithm."""
        result_k = find_mst(classic_mst_graph, algorithm="kruskal")
        result_p = find_mst(classic_mst_graph, algorithm="prim")
        
        assert result_k.total_weight == result_p.total_weight
    
    def test_evaluate_mst_submission_correct(self, k4_weighted_graph):
        """Test evaluating correct MST submission."""
        submitted = [("A", "B"), ("B", "C"), ("A", "D")]
        result = evaluate_mst_submission(k4_weighted_graph, submitted)
        
        assert result.is_mst == True
    
    def test_evaluate_mst_submission_incorrect(self, k4_weighted_graph):
        """Test evaluating incorrect MST submission."""
        # Submitting non-minimum spanning tree
        submitted = [("A", "B"), ("A", "C"), ("B", "D")]  # Weight: 1+4+5 = 10
        result = evaluate_mst_submission(k4_weighted_graph, submitted)
        
        assert result.is_spanning_tree == True
        assert result.is_mst == False


# =============================================================================
# EDGE CASES AND SPECIAL GRAPHS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and special graphs."""
    
    def test_single_edge_graph(self):
        """Test graph with single edge."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[Edge(source="A", target="B", weight=1.0)]
        )
        result = find_mst(graph)
        assert result.is_mst == True
        assert result.total_weight == 1.0
    
    def test_star_graph(self):
        """Test star graph (one center connected to all others)."""
        graph = Graph(
            nodes=[Node(id="C"), Node(id="A"), Node(id="B"), Node(id="D"), Node(id="E")],
            edges=[
                Edge(source="C", target="A", weight=1.0),
                Edge(source="C", target="B", weight=2.0),
                Edge(source="C", target="D", weight=3.0),
                Edge(source="C", target="E", weight=4.0)
            ]
        )
        result = find_mst(graph)
        # Star is already a tree
        assert result.is_mst == True
        assert result.total_weight == 10.0  # 1+2+3+4
    
    def test_complete_bipartite_graph(self):
        """Test complete bipartite graph K2,3."""
        graph = Graph(
            nodes=[
                Node(id="A"), Node(id="B"),  # Left partition
                Node(id="X"), Node(id="Y"), Node(id="Z")  # Right partition
            ],
            edges=[
                Edge(source="A", target="X", weight=1.0),
                Edge(source="A", target="Y", weight=2.0),
                Edge(source="A", target="Z", weight=3.0),
                Edge(source="B", target="X", weight=4.0),
                Edge(source="B", target="Y", weight=5.0),
                Edge(source="B", target="Z", weight=6.0)
            ]
        )
        result = find_mst(graph)
        assert result.is_mst == True
        assert len(result.edges) == 4  # n-1 = 5-1 = 4
    
    def test_graph_with_parallel_edges(self):
        """Test graph with parallel edges (same endpoints, different weights)."""
        # Note: multigraph support would handle this differently
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[
                Edge(source="A", target="B", weight=1.0),
                Edge(source="A", target="B", weight=5.0),  # Parallel edge
                Edge(source="B", target="C", weight=2.0)
            ]
        )
        result = find_mst(graph)
        # Should use lighter edge
        assert result.total_weight == 3.0  # 1 + 2
    
    def test_floating_point_weights(self):
        """Test graph with floating point weights."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[
                Edge(source="A", target="B", weight=0.1),
                Edge(source="B", target="C", weight=0.2),
                Edge(source="A", target="C", weight=0.25)
            ]
        )
        result = find_mst(graph)
        assert result.is_mst == True
        assert abs(result.total_weight - 0.3) < 1e-9
    
    def test_zero_weight_edges(self):
        """Test graph with zero weight edges."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[
                Edge(source="A", target="B", weight=0.0),
                Edge(source="B", target="C", weight=0.0),
                Edge(source="A", target="C", weight=1.0)
            ]
        )
        result = find_mst(graph)
        assert result.is_mst == True
        assert result.total_weight == 0.0  # Two zero-weight edges


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and stress tests."""
    
    def test_large_graph_kruskal(self, large_graph):
        """Test Kruskal's on larger graph."""
        edges, weight, connected, alg = compute_mst(large_graph, "kruskal")
        assert connected == True
        assert len(edges) == 19  # n-1 for 20 nodes
    
    def test_large_graph_prim(self, large_graph):
        """Test Prim's on larger graph."""
        edges, weight, connected, alg = compute_mst(large_graph, "prim")
        assert connected == True
        assert len(edges) == 19
    
    def test_algorithms_produce_same_weight_large(self, large_graph):
        """Test both algorithms produce same weight on large graph."""
        _, weight_k, _, _ = compute_mst(large_graph, "kruskal")
        _, weight_p, _, _ = compute_mst(large_graph, "prim")
        assert weight_k == weight_p


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_full_workflow(self, classic_mst_graph):
        """Test complete MST workflow."""
        # 1. Check connectivity
        assert is_graph_connected(classic_mst_graph) == True
        
        # 2. Compute MST
        result = find_mst(classic_mst_graph)
        assert result.is_mst == True
        
        # 3. Verify the result
        verification = verify_mst(classic_mst_graph, result.edges)
        assert verification.is_mst == True
        
        # 4. Get visualization
        viz = get_mst_visualization(classic_mst_graph, result.edges)
        assert len(viz.highlight_edges) == 5
        
        # 5. Get animation
        steps = get_mst_animation_steps(classic_mst_graph, "kruskal")
        assert len(steps) > 0
    
    def test_student_submission_workflow(self, k4_weighted_graph):
        """Test student submission evaluation workflow."""
        # Student submits their MST
        student_mst = [("A", "B"), ("B", "C"), ("A", "D")]
        
        # Evaluate submission
        result = evaluate_mst_submission(k4_weighted_graph, student_mst)
        
        # Check result
        assert result.is_mst == True
        assert result.total_weight == 6.0
    
    def test_incorrect_submission_feedback(self, triangle_graph):
        """Test that incorrect submissions are properly identified."""
        # Student submits non-minimum spanning tree
        wrong_mst = [("A", "B"), ("A", "C")]  # Weight 4 instead of 3
        
        result = evaluate_mst_submission(triangle_graph, wrong_mst)
        
        assert result.is_spanning_tree == True
        assert result.is_mst == False
        assert result.total_weight == 4.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
