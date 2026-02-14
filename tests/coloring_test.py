"""
Unit Tests for Graph Coloring Algorithms

This module contains comprehensive tests for:
- k-coloring verification
- Greedy coloring algorithm
- DSatur algorithm
- Chromatic number computation
- Edge coloring
- Coloring conflict detection

Test graph types include:
- Empty graphs
- Single vertex graphs
- Complete graphs (Kn)
- Bipartite graphs
- Cycle graphs
- Tree graphs
- Petersen graph
- General graphs
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation_function.schemas.graph import Graph, Node, Edge
from evaluation_function.algorithms.coloring import (
    verify_vertex_coloring,
    verify_edge_coloring,
    detect_coloring_conflicts,
    detect_edge_coloring_conflicts,
    greedy_coloring,
    dsatur_coloring,
    greedy_edge_coloring,
    compute_chromatic_number,
    compute_chromatic_index,
    build_adjacency_list,
    color_graph,
    color_edges,
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
def two_vertex_edge_graph():
    """Graph with two vertices connected by an edge."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B")],
        edges=[Edge(source="A", target="B")]
    )


@pytest.fixture
def triangle_graph():
    """Complete graph K3 (triangle)."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
        edges=[
            Edge(source="A", target="B"),
            Edge(source="B", target="C"),
            Edge(source="A", target="C")
        ]
    )


@pytest.fixture
def k4_graph():
    """Complete graph K4."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B"),
            Edge(source="A", target="C"),
            Edge(source="A", target="D"),
            Edge(source="B", target="C"),
            Edge(source="B", target="D"),
            Edge(source="C", target="D")
        ]
    )


@pytest.fixture
def k5_graph():
    """Complete graph K5."""
    nodes = [Node(id=str(i)) for i in range(5)]
    edges = []
    for i in range(5):
        for j in range(i + 1, 5):
            edges.append(Edge(source=str(i), target=str(j)))
    return Graph(nodes=nodes, edges=edges)


@pytest.fixture
def bipartite_graph():
    """A bipartite graph (K2,3)."""
    return Graph(
        nodes=[
            Node(id="A", partition=0),
            Node(id="B", partition=0),
            Node(id="X", partition=1),
            Node(id="Y", partition=1),
            Node(id="Z", partition=1)
        ],
        edges=[
            Edge(source="A", target="X"),
            Edge(source="A", target="Y"),
            Edge(source="A", target="Z"),
            Edge(source="B", target="X"),
            Edge(source="B", target="Y"),
            Edge(source="B", target="Z")
        ]
    )


@pytest.fixture
def complete_bipartite_k33():
    """Complete bipartite graph K3,3."""
    return Graph(
        nodes=[
            Node(id="A1"), Node(id="A2"), Node(id="A3"),
            Node(id="B1"), Node(id="B2"), Node(id="B3")
        ],
        edges=[
            Edge(source="A1", target="B1"),
            Edge(source="A1", target="B2"),
            Edge(source="A1", target="B3"),
            Edge(source="A2", target="B1"),
            Edge(source="A2", target="B2"),
            Edge(source="A2", target="B3"),
            Edge(source="A3", target="B1"),
            Edge(source="A3", target="B2"),
            Edge(source="A3", target="B3")
        ]
    )


@pytest.fixture
def cycle_c4():
    """Cycle graph C4 (square)."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B"),
            Edge(source="B", target="C"),
            Edge(source="C", target="D"),
            Edge(source="D", target="A")
        ]
    )


@pytest.fixture
def cycle_c5():
    """Cycle graph C5 (pentagon) - odd cycle."""
    return Graph(
        nodes=[Node(id=str(i)) for i in range(5)],
        edges=[
            Edge(source="0", target="1"),
            Edge(source="1", target="2"),
            Edge(source="2", target="3"),
            Edge(source="3", target="4"),
            Edge(source="4", target="0")
        ]
    )


@pytest.fixture
def path_graph():
    """Path graph P4."""
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B"),
            Edge(source="B", target="C"),
            Edge(source="C", target="D")
        ]
    )


@pytest.fixture
def star_graph():
    """Star graph S4 (one center connected to 4 leaves)."""
    return Graph(
        nodes=[
            Node(id="center"),
            Node(id="leaf1"), Node(id="leaf2"), 
            Node(id="leaf3"), Node(id="leaf4")
        ],
        edges=[
            Edge(source="center", target="leaf1"),
            Edge(source="center", target="leaf2"),
            Edge(source="center", target="leaf3"),
            Edge(source="center", target="leaf4")
        ]
    )


@pytest.fixture
def tree_graph():
    """A simple tree graph."""
    return Graph(
        nodes=[
            Node(id="root"),
            Node(id="L"), Node(id="R"),
            Node(id="LL"), Node(id="LR")
        ],
        edges=[
            Edge(source="root", target="L"),
            Edge(source="root", target="R"),
            Edge(source="L", target="LL"),
            Edge(source="L", target="LR")
        ]
    )


@pytest.fixture
def petersen_graph():
    """The Petersen graph - a well-known graph with chromatic number 3."""
    outer = [Node(id=f"o{i}") for i in range(5)]
    inner = [Node(id=f"i{i}") for i in range(5)]
    nodes = outer + inner
    
    edges = []
    # Outer pentagon
    for i in range(5):
        edges.append(Edge(source=f"o{i}", target=f"o{(i+1)%5}"))
    # Inner pentagram (star)
    for i in range(5):
        edges.append(Edge(source=f"i{i}", target=f"i{(i+2)%5}"))
    # Spokes connecting outer to inner
    for i in range(5):
        edges.append(Edge(source=f"o{i}", target=f"i{i}"))
    
    return Graph(nodes=nodes, edges=edges)


@pytest.fixture
def disconnected_graph():
    """A disconnected graph with two components."""
    return Graph(
        nodes=[
            Node(id="A"), Node(id="B"), Node(id="C"),  # Component 1: triangle
            Node(id="X"), Node(id="Y")  # Component 2: edge
        ],
        edges=[
            Edge(source="A", target="B"),
            Edge(source="B", target="C"),
            Edge(source="A", target="C"),
            Edge(source="X", target="Y")
        ]
    )


@pytest.fixture
def wheel_graph():
    """Wheel graph W5 (center + cycle C5)."""
    return Graph(
        nodes=[
            Node(id="center"),
            Node(id="0"), Node(id="1"), Node(id="2"), 
            Node(id="3"), Node(id="4")
        ],
        edges=[
            # Outer cycle
            Edge(source="0", target="1"),
            Edge(source="1", target="2"),
            Edge(source="2", target="3"),
            Edge(source="3", target="4"),
            Edge(source="4", target="0"),
            # Spokes
            Edge(source="center", target="0"),
            Edge(source="center", target="1"),
            Edge(source="center", target="2"),
            Edge(source="center", target="3"),
            Edge(source="center", target="4")
        ]
    )


# =============================================================================
# VERTEX COLORING VERIFICATION TESTS
# =============================================================================

class TestVerifyVertexColoring:
    """Tests for verify_vertex_coloring function."""
    
    def test_valid_coloring_triangle(self, triangle_graph):
        """Test valid 3-coloring of a triangle."""
        coloring = {"A": 0, "B": 1, "C": 2}
        result = verify_vertex_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3
        assert result.conflicts is None
    
    def test_invalid_coloring_triangle(self, triangle_graph):
        """Test invalid coloring with conflict."""
        coloring = {"A": 0, "B": 0, "C": 1}  # A and B both have color 0
        result = verify_vertex_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is False
        assert len(result.conflicts) == 1
        assert ("A", "B") in result.conflicts or ("B", "A") in result.conflicts
    
    def test_valid_2_coloring_bipartite(self, bipartite_graph):
        """Test valid 2-coloring of bipartite graph."""
        coloring = {"A": 0, "B": 0, "X": 1, "Y": 1, "Z": 1}
        result = verify_vertex_coloring(bipartite_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 2
    
    def test_k_coloring_constraint_violated(self, triangle_graph):
        """Test k-coloring constraint violation."""
        coloring = {"A": 0, "B": 1, "C": 2}
        result = verify_vertex_coloring(triangle_graph, coloring, k=2)
        
        assert result.is_valid_coloring is False  # Uses 3 colors but k=2
        assert result.num_colors_used == 3
    
    def test_k_coloring_constraint_satisfied(self, triangle_graph):
        """Test k-coloring constraint satisfied."""
        coloring = {"A": 0, "B": 1, "C": 2}
        result = verify_vertex_coloring(triangle_graph, coloring, k=3)
        
        assert result.is_valid_coloring is True
    
    def test_uncolored_vertices(self, triangle_graph):
        """Test detection of uncolored vertices."""
        coloring = {"A": 0, "B": 1}  # C is not colored
        result = verify_vertex_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is False
        assert any("C" in conflict for conflict in result.conflicts)
    
    def test_empty_graph(self, empty_graph):
        """Test coloring of empty graph."""
        coloring = {}
        result = verify_vertex_coloring(empty_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 0
    
    def test_single_vertex(self, single_vertex_graph):
        """Test coloring of single vertex graph."""
        coloring = {"A": 0}
        result = verify_vertex_coloring(single_vertex_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 1


class TestDetectColoringConflicts:
    """Tests for detect_coloring_conflicts function."""
    
    def test_no_conflicts(self, triangle_graph):
        """Test no conflicts in valid coloring."""
        coloring = {"A": 0, "B": 1, "C": 2}
        conflicts = detect_coloring_conflicts(triangle_graph, coloring)
        
        assert conflicts == []
    
    def test_multiple_conflicts(self, k4_graph):
        """Test detection of multiple conflicts."""
        coloring = {"A": 0, "B": 0, "C": 0, "D": 1}  # A, B, C all same color
        conflicts = detect_coloring_conflicts(k4_graph, coloring)
        
        assert len(conflicts) == 3  # A-B, A-C, B-C all conflict


# =============================================================================
# GREEDY COLORING TESTS
# =============================================================================

class TestGreedyColoring:
    """Tests for greedy_coloring function."""
    
    def test_empty_graph(self, empty_graph):
        """Test greedy coloring of empty graph."""
        coloring = greedy_coloring(empty_graph)
        assert coloring == {}
    
    def test_single_vertex(self, single_vertex_graph):
        """Test greedy coloring of single vertex."""
        coloring = greedy_coloring(single_vertex_graph)
        
        assert coloring == {"A": 0}
    
    def test_two_vertices(self, two_vertex_edge_graph):
        """Test greedy coloring of two connected vertices."""
        coloring = greedy_coloring(two_vertex_edge_graph)
        
        assert len(coloring) == 2
        assert coloring["A"] != coloring["B"]
    
    def test_triangle(self, triangle_graph):
        """Test greedy coloring produces valid coloring for triangle."""
        coloring = greedy_coloring(triangle_graph)
        result = verify_vertex_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3
    
    def test_bipartite(self, bipartite_graph):
        """Test greedy coloring of bipartite graph."""
        coloring = greedy_coloring(bipartite_graph)
        result = verify_vertex_coloring(bipartite_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used <= 3  # Could be optimal 2 or suboptimal
    
    def test_cycle_c4(self, cycle_c4):
        """Test greedy coloring of even cycle."""
        coloring = greedy_coloring(cycle_c4)
        result = verify_vertex_coloring(cycle_c4, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used <= 3
    
    def test_path(self, path_graph):
        """Test greedy coloring of path graph."""
        coloring = greedy_coloring(path_graph)
        result = verify_vertex_coloring(path_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 2  # Path is bipartite
    
    def test_custom_order(self, triangle_graph):
        """Test greedy coloring with custom vertex order."""
        order = ["C", "B", "A"]
        coloring = greedy_coloring(triangle_graph, order=order)
        
        assert coloring["C"] == 0  # First vertex gets color 0
        result = verify_vertex_coloring(triangle_graph, coloring)
        assert result.is_valid_coloring is True
    
    def test_disconnected_graph(self, disconnected_graph):
        """Test greedy coloring handles disconnected graphs."""
        coloring = greedy_coloring(disconnected_graph)
        result = verify_vertex_coloring(disconnected_graph, coloring)
        
        assert result.is_valid_coloring is True


# =============================================================================
# DSATUR COLORING TESTS
# =============================================================================

class TestDSaturColoring:
    """Tests for dsatur_coloring function."""
    
    def test_empty_graph(self, empty_graph):
        """Test DSatur coloring of empty graph."""
        coloring = dsatur_coloring(empty_graph)
        assert coloring == {}
    
    def test_single_vertex(self, single_vertex_graph):
        """Test DSatur coloring of single vertex."""
        coloring = dsatur_coloring(single_vertex_graph)
        assert coloring == {"A": 0}
    
    def test_triangle(self, triangle_graph):
        """Test DSatur coloring of triangle."""
        coloring = dsatur_coloring(triangle_graph)
        result = verify_vertex_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3
    
    def test_bipartite_optimal(self, bipartite_graph):
        """Test DSatur produces optimal 2-coloring for bipartite graph."""
        coloring = dsatur_coloring(bipartite_graph)
        result = verify_vertex_coloring(bipartite_graph, coloring)
        
        assert result.is_valid_coloring is True
        # DSatur should find optimal 2-coloring
        assert result.num_colors_used == 2
    
    def test_cycle_c4_optimal(self, cycle_c4):
        """Test DSatur produces optimal coloring for C4."""
        coloring = dsatur_coloring(cycle_c4)
        result = verify_vertex_coloring(cycle_c4, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 2  # C4 is bipartite
    
    def test_cycle_c5_optimal(self, cycle_c5):
        """Test DSatur produces optimal 3-coloring for C5."""
        coloring = dsatur_coloring(cycle_c5)
        result = verify_vertex_coloring(cycle_c5, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3  # C5 has chromatic number 3
    
    def test_k4_optimal(self, k4_graph):
        """Test DSatur produces optimal 4-coloring for K4."""
        coloring = dsatur_coloring(k4_graph)
        result = verify_vertex_coloring(k4_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 4
    
    def test_petersen_graph(self, petersen_graph):
        """Test DSatur colors Petersen graph with 3 colors."""
        coloring = dsatur_coloring(petersen_graph)
        result = verify_vertex_coloring(petersen_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3  # Petersen graph has χ = 3
    
    def test_dsatur_better_than_greedy(self):
        """Test DSatur produces better or equal coloring than greedy on Crown graph."""
        # Crown graph Sn° - often shows difference between greedy and DSatur
        # Using a 6-vertex crown (bipartite)
        graph = Graph(
            nodes=[Node(id=f"A{i}") for i in range(3)] + [Node(id=f"B{i}") for i in range(3)],
            edges=[
                Edge(source="A0", target="B1"),
                Edge(source="A0", target="B2"),
                Edge(source="A1", target="B0"),
                Edge(source="A1", target="B2"),
                Edge(source="A2", target="B0"),
                Edge(source="A2", target="B1")
            ]
        )
        
        dsatur_coloring_result = dsatur_coloring(graph)
        dsatur_result = verify_vertex_coloring(graph, dsatur_coloring_result)
        
        # DSatur should find optimal 2-coloring for bipartite graph
        assert dsatur_result.is_valid_coloring is True
        assert dsatur_result.num_colors_used == 2


# =============================================================================
# CHROMATIC NUMBER TESTS
# =============================================================================

class TestChromaticNumber:
    """Tests for compute_chromatic_number function."""
    
    def test_empty_graph(self, empty_graph):
        """Test chromatic number of empty graph is 0."""
        chi = compute_chromatic_number(empty_graph)
        assert chi == 0
    
    def test_single_vertex(self, single_vertex_graph):
        """Test chromatic number of single vertex is 1."""
        chi = compute_chromatic_number(single_vertex_graph)
        assert chi == 1
    
    def test_two_vertices_with_edge(self, two_vertex_edge_graph):
        """Test chromatic number of K2 is 2."""
        chi = compute_chromatic_number(two_vertex_edge_graph)
        assert chi == 2
    
    def test_triangle(self, triangle_graph):
        """Test chromatic number of K3 is 3."""
        chi = compute_chromatic_number(triangle_graph)
        assert chi == 3
    
    def test_k4(self, k4_graph):
        """Test chromatic number of K4 is 4."""
        chi = compute_chromatic_number(k4_graph)
        assert chi == 4
    
    def test_k5(self, k5_graph):
        """Test chromatic number of K5 is 5."""
        chi = compute_chromatic_number(k5_graph)
        assert chi == 5
    
    def test_bipartite(self, bipartite_graph):
        """Test chromatic number of bipartite graph is 2."""
        chi = compute_chromatic_number(bipartite_graph)
        assert chi == 2
    
    def test_cycle_c4(self, cycle_c4):
        """Test chromatic number of C4 is 2."""
        chi = compute_chromatic_number(cycle_c4)
        assert chi == 2
    
    def test_cycle_c5(self, cycle_c5):
        """Test chromatic number of C5 is 3."""
        chi = compute_chromatic_number(cycle_c5)
        assert chi == 3
    
    def test_path(self, path_graph):
        """Test chromatic number of path is 2."""
        chi = compute_chromatic_number(path_graph)
        assert chi == 2
    
    def test_star(self, star_graph):
        """Test chromatic number of star is 2."""
        chi = compute_chromatic_number(star_graph)
        assert chi == 2
    
    def test_petersen(self, petersen_graph):
        """Test chromatic number of Petersen graph is 3."""
        chi = compute_chromatic_number(petersen_graph)
        assert chi == 3
    
    def test_wheel_w5(self, wheel_graph):
        """Test chromatic number of W5 (odd wheel) is 4."""
        chi = compute_chromatic_number(wheel_graph)
        assert chi == 4
    
    def test_disconnected(self, disconnected_graph):
        """Test chromatic number of disconnected graph."""
        chi = compute_chromatic_number(disconnected_graph)
        # Max chromatic number of components: triangle (3) and edge (2)
        assert chi == 3
    
    def test_large_graph_returns_none(self):
        """Test that large graphs return None."""
        nodes = [Node(id=str(i)) for i in range(15)]
        edges = [Edge(source="0", target=str(i)) for i in range(1, 15)]
        graph = Graph(nodes=nodes, edges=edges)
        
        chi = compute_chromatic_number(graph, max_nodes=10)
        assert chi is None


# =============================================================================
# EDGE COLORING TESTS
# =============================================================================

class TestEdgeColoring:
    """Tests for edge coloring functions."""
    
    def test_empty_graph(self, empty_graph):
        """Test edge coloring of empty graph."""
        coloring = greedy_edge_coloring(empty_graph)
        assert coloring == {}
    
    def test_single_edge(self, two_vertex_edge_graph):
        """Test edge coloring of single edge."""
        coloring = greedy_edge_coloring(two_vertex_edge_graph)
        
        assert len(coloring) == 1
        assert list(coloring.values())[0] == 0
    
    def test_triangle_edges(self, triangle_graph):
        """Test edge coloring of triangle (3 edges)."""
        coloring = greedy_edge_coloring(triangle_graph)
        result = verify_edge_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3  # Each edge needs different color
    
    def test_star_edges(self, star_graph):
        """Test edge coloring of star graph."""
        coloring = greedy_edge_coloring(star_graph)
        result = verify_edge_coloring(star_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 4  # Δ = 4, all edges share center
    
    def test_path_edges(self, path_graph):
        """Test edge coloring of path graph."""
        coloring = greedy_edge_coloring(path_graph)
        result = verify_edge_coloring(path_graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 2  # Path edges can alternate colors
    
    def test_cycle_c4_edges(self, cycle_c4):
        """Test edge coloring of C4."""
        coloring = greedy_edge_coloring(cycle_c4)
        result = verify_edge_coloring(cycle_c4, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 2  # C4 edges can be 2-colored


class TestVerifyEdgeColoring:
    """Tests for verify_edge_coloring function."""
    
    def test_valid_edge_coloring(self, triangle_graph):
        """Test valid edge coloring verification."""
        # Triangle needs 3 colors for edges
        coloring = {"e0": 0, "e1": 1, "e2": 2}
        result = verify_edge_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is True
    
    def test_invalid_edge_coloring(self, triangle_graph):
        """Test invalid edge coloring with conflict."""
        # Two edges sharing a vertex with same color
        coloring = {"e0": 0, "e1": 0, "e2": 1}  # e0 and e1 might conflict
        result = verify_edge_coloring(triangle_graph, coloring)
        
        # Edges e0 (A-B) and e1 (B-C) share vertex B, so they conflict
        assert result.is_valid_coloring is False
    
    def test_uncolored_edges(self, triangle_graph):
        """Test detection of uncolored edges."""
        coloring = {"e0": 0, "e1": 1}  # e2 not colored
        result = verify_edge_coloring(triangle_graph, coloring)
        
        assert result.is_valid_coloring is False


class TestChromaticIndex:
    """Tests for compute_chromatic_index function."""
    
    def test_empty_graph(self, empty_graph):
        """Test chromatic index of empty graph is 0."""
        chi_prime = compute_chromatic_index(empty_graph)
        assert chi_prime == 0
    
    def test_single_edge(self, two_vertex_edge_graph):
        """Test chromatic index of single edge is 1."""
        chi_prime = compute_chromatic_index(two_vertex_edge_graph)
        assert chi_prime == 1
    
    def test_triangle(self, triangle_graph):
        """Test chromatic index of triangle is 3."""
        # Triangle: Δ = 2, but χ' = 3 (Class 2)
        chi_prime = compute_chromatic_index(triangle_graph)
        assert chi_prime == 3
    
    def test_path(self, path_graph):
        """Test chromatic index of path."""
        # Path: Δ = 2, χ' = 2 (Class 1)
        chi_prime = compute_chromatic_index(path_graph)
        assert chi_prime == 2
    
    def test_star(self, star_graph):
        """Test chromatic index of star is Δ."""
        # Star: Δ = 4, χ' = 4 (Class 1 - bipartite)
        chi_prime = compute_chromatic_index(star_graph)
        assert chi_prime == 4
    
    def test_cycle_c4(self, cycle_c4):
        """Test chromatic index of C4 is 2."""
        chi_prime = compute_chromatic_index(cycle_c4)
        assert chi_prime == 2
    
    def test_k4(self, k4_graph):
        """Test chromatic index of K4."""
        # K4: Δ = 3, χ' = 3 (Class 1)
        chi_prime = compute_chromatic_index(k4_graph)
        assert chi_prime == 3
    
    def test_large_graph_returns_none(self):
        """Test that graphs with many edges return None."""
        # Create K6 which has 15 edges
        nodes = [Node(id=str(i)) for i in range(6)]
        edges = []
        for i in range(6):
            for j in range(i + 1, 6):
                edges.append(Edge(source=str(i), target=str(j)))
        graph = Graph(nodes=nodes, edges=edges)
        
        chi_prime = compute_chromatic_index(graph, max_edges=10)
        assert chi_prime is None


# =============================================================================
# HIGH-LEVEL FUNCTION TESTS
# =============================================================================

class TestColorGraph:
    """Tests for the high-level color_graph function."""
    
    def test_auto_algorithm(self, triangle_graph):
        """Test auto algorithm selection."""
        result = color_graph(triangle_graph, algorithm="auto")
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3
    
    def test_greedy_algorithm(self, triangle_graph):
        """Test greedy algorithm."""
        result = color_graph(triangle_graph, algorithm="greedy")
        
        assert result.is_valid_coloring is True
    
    def test_dsatur_algorithm(self, triangle_graph):
        """Test DSatur algorithm."""
        result = color_graph(triangle_graph, algorithm="dsatur")
        
        assert result.is_valid_coloring is True
    
    def test_with_k_constraint(self, triangle_graph):
        """Test k-coloring constraint."""
        result = color_graph(triangle_graph, k=2)
        
        assert result.is_valid_coloring is False  # Can't color K3 with 2 colors
    
    def test_invalid_algorithm(self, triangle_graph):
        """Test that invalid algorithm raises error."""
        with pytest.raises(ValueError):
            color_graph(triangle_graph, algorithm="invalid")


class TestColorEdges:
    """Tests for the high-level color_edges function."""
    
    def test_color_edges_triangle(self, triangle_graph):
        """Test edge coloring of triangle."""
        result = color_edges(triangle_graph)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3
    
    def test_color_edges_star(self, star_graph):
        """Test edge coloring of star."""
        result = color_edges(star_graph)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 4


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestBuildAdjacencyList:
    """Tests for build_adjacency_list helper function."""
    
    def test_empty_graph(self, empty_graph):
        """Test adjacency list for empty graph."""
        adj = build_adjacency_list(empty_graph)
        assert adj == {}
    
    def test_single_vertex(self, single_vertex_graph):
        """Test adjacency list for single vertex."""
        adj = build_adjacency_list(single_vertex_graph)
        assert adj == {"A": set()}
    
    def test_two_vertices(self, two_vertex_edge_graph):
        """Test adjacency list for two connected vertices."""
        adj = build_adjacency_list(two_vertex_edge_graph)
        
        assert adj["A"] == {"B"}
        assert adj["B"] == {"A"}
    
    def test_directed_graph(self):
        """Test adjacency list for directed graph."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[Edge(source="A", target="B")],
            directed=True
        )
        adj = build_adjacency_list(graph)
        
        assert adj["A"] == {"B"}
        assert adj["B"] == set()  # No edge from B to A


# =============================================================================
# EDGE CASES AND STRESS TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_isolated_vertices(self):
        """Test graph with isolated vertices."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B")]
        )
        
        coloring = dsatur_coloring(graph)
        result = verify_vertex_coloring(graph, coloring)
        
        assert result.is_valid_coloring is True
        assert "C" in coloring
    
    def test_self_loop_detection(self):
        """Test handling of self-loops (if present)."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[
                Edge(source="A", target="B"),
                Edge(source="A", target="A")  # Self-loop
            ]
        )
        
        coloring = greedy_coloring(graph)
        # Self-loops should ideally be ignored or handled gracefully
        assert "A" in coloring
        assert "B" in coloring
    
    def test_large_complete_graph(self):
        """Test coloring of K10 (at the limit)."""
        n = 10
        nodes = [Node(id=str(i)) for i in range(n)]
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                edges.append(Edge(source=str(i), target=str(j)))
        graph = Graph(nodes=nodes, edges=edges)
        
        chi = compute_chromatic_number(graph)
        assert chi == 10
    
    def test_multiple_components_coloring(self):
        """Test coloring of multiple disconnected components."""
        graph = Graph(
            nodes=[
                Node(id="A1"), Node(id="A2"),  # Component 1: edge
                Node(id="B1"), Node(id="B2"), Node(id="B3"),  # Component 2: triangle
                Node(id="C1")  # Component 3: isolated
            ],
            edges=[
                Edge(source="A1", target="A2"),
                Edge(source="B1", target="B2"),
                Edge(source="B2", target="B3"),
                Edge(source="B1", target="B3")
            ]
        )
        
        coloring = dsatur_coloring(graph)
        result = verify_vertex_coloring(graph, coloring)
        
        assert result.is_valid_coloring is True
        assert result.num_colors_used == 3  # Triangle needs 3 colors


# =============================================================================
# COMPARISON TESTS
# =============================================================================

class TestAlgorithmComparison:
    """Tests comparing different algorithms."""
    
    def test_dsatur_never_worse_than_greedy(self, petersen_graph):
        """Test that DSatur produces coloring no worse than greedy."""
        greedy_col = greedy_coloring(petersen_graph)
        dsatur_col = dsatur_coloring(petersen_graph)
        
        greedy_colors = len(set(greedy_col.values()))
        dsatur_colors = len(set(dsatur_col.values()))
        
        # DSatur should be at least as good as greedy
        assert dsatur_colors <= greedy_colors
        
        # Both should be valid
        assert verify_vertex_coloring(petersen_graph, greedy_col).is_valid_coloring
        assert verify_vertex_coloring(petersen_graph, dsatur_col).is_valid_coloring


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
