import unittest

from .preview import Params, preview_function, ValidationError
from .schemas.graph import Graph, Node, Edge
from .schemas.request import Response


class TestPreviewFunction(unittest.TestCase):
    """
    TestCase Class used to test the algorithm.
    ---
    Tests are used here to check that the algorithm written
    is working as it should.

    It's best practice to write these tests first to get a
    kind of 'specification' for how your algorithm should
    work, and you should run these tests before committing
    your code to AWS.

    Read the docs on how to use unittest here:
    https://docs.python.org/3/library/unittest.html

    Use preview_function() to check your algorithm works
    as it should.
    """

    def test_preview_simple_string(self):
        """Test preview with simple string response."""
        response, params = "A", Params()
        result = preview_function(response, params)

        self.assertIn("preview", result)
        self.assertIsNotNone(result["preview"])

    def test_preview_graph(self):
        """Test preview with a graph structure."""
        graph = Graph(
            nodes=[
                Node(id="A", label="Node A"),
                Node(id="B", label="Node B"),
                Node(id="C", label="Node C"),
            ],
            edges=[
                Edge(source="A", target="B", weight=5),
                Edge(source="B", target="C", weight=3),
                Edge(source="A", target="C", weight=7),
            ],
            directed=False,
            weighted=True,
            name="Triangle Graph"
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], True)
        self.assertEqual(sympy_data["num_nodes"], 3)
        self.assertEqual(sympy_data["num_edges"], 3)
        self.assertEqual(sympy_data["directed"], False)
        self.assertEqual(sympy_data["weighted"], True)
        self.assertEqual(sympy_data["graph_name"], "Triangle Graph")

    def test_preview_path_answer(self):
        """Test preview with a path answer."""
        response = Response(
            path=["A", "B", "C", "D"],
            distance=10.5
        )
        result = preview_function(response, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], True)
        self.assertEqual(sympy_data["errors"], [])
        
        # Feedback should contain the path info
        self.assertIn("feedback", preview)
        self.assertIn("valid", preview["feedback"].lower())

    def test_preview_boolean_answer(self):
        """Test preview with boolean answers."""
        response = Response(
            is_connected=True,
            is_bipartite=False,
            has_cycle=True
        )
        result = preview_function(response, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], True)
        self.assertEqual(sympy_data["errors"], [])

    def test_preview_graph_and_answers(self):
        """Test preview with both graph and answers."""
        graph = Graph(
            nodes=[Node(id="1"), Node(id="2"), Node(id="3")],
            edges=[Edge(source="1", target="2"), Edge(source="2", target="3")],
            directed=True
        )
        
        response = Response(
            graph=graph,
            is_dag=True,
            topological_order=["1", "2", "3"]
        )
        result = preview_function(response, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], True)
        self.assertEqual(sympy_data["directed"], True)
        self.assertEqual(sympy_data["num_nodes"], 3)
        self.assertEqual(sympy_data["num_edges"], 2)

    def test_preview_coloring(self):
        """Test preview with graph coloring."""
        response = Response(
            coloring={"A": 0, "B": 1, "C": 0, "D": 2},
            chromatic_number=3
        )
        result = preview_function(response, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], True)
        self.assertEqual(sympy_data["errors"], [])

    def test_preview_sets(self):
        """Test preview with set-based answers."""
        response = Response(
            components=[["A", "B", "C"], ["D", "E"]],
            vertex_cover=["A", "C", "D"]
        )
        result = preview_function(response, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], True)

    def test_preview_empty_response(self):
        """Test preview with empty response."""
        result = preview_function(None, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format for error
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], False)
        self.assertEqual(sympy_data["parse_error"], True)
        self.assertIn("errors", sympy_data)

    def test_preview_directed_weighted_graph(self):
        """Test preview with directed weighted graph."""
        graph = Graph(
            nodes=[
                Node(id="s", label="Source"),
                Node(id="t", label="Target"),
            ],
            edges=[
                Edge(source="s", target="t", weight=10, capacity=15, flow=8),
            ],
            directed=True,
            weighted=True
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        self.assertIn("preview", result)
        preview = result["preview"]
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Check structured JSON format
        self.assertIsInstance(sympy_data, dict)
        self.assertEqual(sympy_data["valid"], True)
        self.assertEqual(sympy_data["directed"], True)
        self.assertEqual(sympy_data["weighted"], True)
        self.assertEqual(sympy_data["num_nodes"], 2)
        self.assertEqual(sympy_data["num_edges"], 1)
        self.assertIn("flow_info", sympy_data)
        self.assertEqual(sympy_data["flow_info"]["has_capacities"], True)
        self.assertEqual(sympy_data["flow_info"]["has_flows"], True)
        
        self.assertIn("feedback", preview)
        self.assertIn("valid", preview["feedback"].lower())

    def test_validation_duplicate_nodes(self):
        """Test validation catches duplicate node IDs."""
        graph = Graph(
            nodes=[
                Node(id="A"),
                Node(id="B"),
                Node(id="A"),  # Duplicate!
            ],
            edges=[],
            directed=False
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("Duplicate node IDs", preview["feedback"])
        self.assertIn("issue", preview["feedback"].lower())

    def test_validation_invalid_edge_source(self):
        """Test validation catches edges with non-existent source nodes."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[Edge(source="X", target="B")],  # X doesn't exist!
            directed=True
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("does not exist", preview["feedback"])

    def test_validation_invalid_edge_target(self):
        """Test validation catches edges with non-existent target nodes."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[Edge(source="A", target="Z")],  # Z doesn't exist!
            directed=True
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("does not exist", preview["feedback"])

    def test_validation_duplicate_edges(self):
        """Test validation catches duplicate edges in non-multigraph."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[
                Edge(source="A", target="B"),
                Edge(source="A", target="B"),  # Duplicate!
            ],
            directed=True,
            multigraph=False
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("Duplicate edge", preview["feedback"])

    def test_validation_missing_weights(self):
        """Test validation catches missing weights in weighted graph."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[Edge(source="A", target="B", weight=None)],  # Missing weight!
            directed=False,
            weighted=True
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("weight", preview["feedback"].lower())

    def test_validation_flow_exceeds_capacity(self):
        """Test validation catches flow exceeding capacity."""
        graph = Graph(
            nodes=[Node(id="s"), Node(id="t")],
            edges=[Edge(source="s", target="t", capacity=10, flow=15)],  # Flow > capacity!
            directed=True
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("exceeds", preview["feedback"].lower())

    def test_warning_isolated_node(self):
        """Test warning for isolated nodes."""
        graph = Graph(
            nodes=[
                Node(id="A"),
                Node(id="B"),
                Node(id="C"),  # Isolated node!
            ],
            edges=[Edge(source="A", target="B")],
            directed=False
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("sympy", preview)
        sympy_data = preview["sympy"]
        
        # Should be valid but with warnings
        self.assertEqual(sympy_data["valid"], True)
        self.assertGreater(len(sympy_data["warnings"]), 0)
        self.assertIn("isolated", sympy_data["warnings"][0]["message"].lower())
        
        # Feedback should mention it's valid
        self.assertIn("valid", preview["feedback"].lower())

    def test_warning_self_loop(self):
        """Test warning for self-loops."""
        graph = Graph(
            nodes=[Node(id="A")],
            edges=[Edge(source="A", target="A")],  # Self-loop!
            directed=True
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("self-loop", preview["feedback"].lower())

    def test_validation_invalid_path_nodes(self):
        """Test validation of path referencing non-existent nodes."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )
        
        response = Response(
            graph=graph,
            path=["A", "B", "X"]  # X doesn't exist!
        )
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("non-existent", preview["feedback"].lower())

    def test_valid_graph_with_success_message(self):
        """Test that valid graphs get success feedback."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[
                Edge(source="A", target="B", weight=5),
                Edge(source="B", target="C", weight=3),
            ],
            directed=False,
            weighted=True
        )
        
        response = Response(graph=graph)
        result = preview_function(response, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("valid", preview["feedback"].lower())
        self.assertIn("ready", preview["feedback"].lower())
        
    def test_empty_response(self):
        """Test handling of empty response."""
        result = preview_function(None, Params())
        
        preview = result["preview"]
        self.assertIn("feedback", preview)
        self.assertIn("No response", preview["feedback"])
