import unittest

from .evaluation import evaluation_function
from .schemas.graph import Graph, Node, Edge
from .schemas.request import Response, Answer
from .schemas.params import EvaluationParams


class TestEvaluationFunction(unittest.TestCase):
    """
    TestCase Class used to test the algorithm.
    ---
    Tests are used here to check that the algorithm written
    is working as it should.

    It's best practise to write these tests first to get a
    kind of 'specification' for how your algorithm should
    work, and you should run these tests before committing
    your code to AWS.

    Read the docs on how to use unittest here:
    https://docs.python.org/3/library/unittest.html

    Use evaluation_function() to check your algorithm works
    as it should.
    """

    def test_graph_match_correct(self):
        """Test correct graph matching with feedback."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )
        
        response = Response(graph=graph)
        answer = Answer(graph=graph)
        params = EvaluationParams(evaluation_type="graph_match", feedback_level="standard", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertTrue(result["is_correct"])
        self.assertIn("Correct", result["feedback"])

    def test_graph_match_missing_nodes_feedback(self):
        """Test graph matching provides feedback for missing nodes."""
        response_graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[Edge(source="A", target="B")],
            directed=True
        )
        
        answer_graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )
        
        response = Response(graph=response_graph)
        answer = Answer(graph=answer_graph)
        params = EvaluationParams(evaluation_type="graph_match", feedback_level="standard", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertIn("Missing nodes", result["feedback"])
        self.assertIn("C", result["feedback"])

    def test_boolean_answer_incorrect_feedback(self):
        """Test boolean answer provides detailed feedback."""
        response = Response(is_bipartite=False)
        answer = Answer(is_bipartite=True)
        params = EvaluationParams(feedback_level="standard", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertIn("Bipartite", result["feedback"])
        self.assertIn("No", result["feedback"])
        self.assertIn("Yes", result["feedback"])

    def test_path_invalid_edge_feedback(self):
        """Test path validation provides feedback for invalid edges."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B")],
            directed=True
        )
        
        response = Response(path=["A", "B", "C"])  # B→C doesn't exist
        answer = Answer(graph=graph)
        params = EvaluationParams(feedback_level="standard", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertIn("does not exist", result["feedback"])

    def test_coloring_conflict_feedback(self):
        """Test graph coloring provides feedback for conflicts."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=False
        )
        
        response = Response(coloring={"A": 0, "B": 0, "C": 1})  # A and B adjacent with same color
        answer = Answer(graph=graph)
        params = EvaluationParams(feedback_level="standard", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertIn("Color conflict", result["feedback"])
        self.assertIn("A", result["feedback"])
        self.assertIn("B", result["feedback"])

    def test_feedback_level_minimal(self):
        """Test minimal feedback level provides minimal output."""
        response = Response(is_connected=False)
        answer = Answer(is_connected=True)
        params = EvaluationParams(feedback_level="minimal", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertEqual(result["feedback"], "Incorrect")

    def test_feedback_level_detailed(self):
        """Test detailed feedback level provides hints."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[],
            directed=False
        )
        
        response = Response(path=["A", "B"])
        answer = Answer(graph=graph)
        params = EvaluationParams(feedback_level="detailed", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertIn("Hints:", result["feedback"])

    def test_spanning_tree_cycle_feedback(self):
        """Test spanning tree validation provides feedback for cycles."""
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[
                Edge(source="A", target="B"),
                Edge(source="B", target="C"),
                Edge(source="A", target="C")
            ],
            directed=False
        )
        
        response = Response(spanning_tree=[
            Edge(source="A", target="B"),
            Edge(source="B", target="C"),
            Edge(source="A", target="C")  # Creates cycle
        ])
        answer = Answer(graph=graph)
        params = EvaluationParams(feedback_level="standard", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertIn("cycle", result["feedback"])

    def test_numeric_answer_feedback(self):
        """Test numeric answer provides specific values in feedback."""
        response = Response(chromatic_number=4)
        answer = Answer(chromatic_number=3)
        params = EvaluationParams(feedback_level="standard", tolerance=1e-9)
        
        result = evaluation_function(response, answer, params).to_dict()
        
        self.assertFalse(result["is_correct"])
        self.assertIn("4", result["feedback"])
        self.assertIn("3", result["feedback"])

