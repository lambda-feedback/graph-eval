#!/usr/bin/env python3
"""
Demonstration of the feedback system for graph-eval.

This script shows how different types of errors generate specific feedback messages.
"""

# Mock the lf_toolkit classes for demonstration
from typing import Any
from dataclasses import dataclass


@dataclass
class Params:
    """Mock Params for demo."""
    pass


@dataclass
class Result:
    """Mock Result for demo."""
    is_correct: bool
    feedback: str
    
    def to_dict(self):
        return {"is_correct": self.is_correct, "feedback": self.feedback}


# Mock lf_toolkit
import sys
sys.modules['lf_toolkit'] = type(sys)('lf_toolkit')
sys.modules['lf_toolkit.evaluation'] = type(sys)('lf_toolkit.evaluation')
sys.modules['lf_toolkit.evaluation'].Result = Result
sys.modules['lf_toolkit.evaluation'].Params = Params

from evaluation_function.evaluation import evaluation_function
from evaluation_function.schemas.graph import Graph, Node, Edge
from evaluation_function.schemas.request import Response, Answer
from evaluation_function.schemas.params import EvaluationParams


def print_example(title: str, response: Response, answer: Answer, params: EvaluationParams):
    """Helper to print evaluation results."""
    print(f"\n{'='*80}")
    print(f"📝 {title}")
    print('='*80)
    
    result = evaluation_function(response, answer, params).to_dict()
    
    status = "✅ CORRECT" if result["is_correct"] else "❌ INCORRECT"
    print(f"\nStatus: {status}")
    print(f"\nFeedback:\n{result['feedback']}")


def main():
    print("🎯 Graph-Eval Feedback System Demonstration")
    print("="*80)
    
    # Example 1: Missing nodes feedback
    print_example(
        "Example 1: Graph with Missing Nodes",
        response=Response(graph=Graph(
            nodes=[Node(id="A"), Node(id="B")],
            edges=[Edge(source="A", target="B")],
            directed=True
        )),
        answer=Answer(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )),
        params=EvaluationParams(evaluation_type="graph_match", feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 2: Extra edges feedback
    print_example(
        "Example 2: Graph with Extra Edges",
        response=Response(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[
                Edge(source="A", target="B"),
                Edge(source="B", target="C"),
                Edge(source="A", target="C"),  # Extra!
                Edge(source="C", target="A")   # Extra!
            ],
            directed=True
        )),
        answer=Answer(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )),
        params=EvaluationParams(evaluation_type="graph_match", feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 3: Invalid path (edge doesn't exist)
    print_example(
        "Example 3: Path with Non-Existent Edge",
        response=Response(path=["A", "B", "D"]),
        answer=Answer(
            graph=Graph(
                nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
                edges=[
                    Edge(source="A", target="B"),
                    Edge(source="B", target="C"),
                    Edge(source="C", target="D")
                ],
                directed=True
            )
        ),
        params=EvaluationParams(feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 4: Invalid graph coloring (color conflict)
    print_example(
        "Example 4: Invalid Graph Coloring (Adjacent Nodes Same Color)",
        response=Response(coloring={"A": 0, "B": 0, "C": 1, "D": 1}),
        answer=Answer(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
            edges=[
                Edge(source="A", target="B"),  # Both have color 0 - conflict!
                Edge(source="B", target="C"),
                Edge(source="C", target="D")   # Both have color 1 - conflict!
            ],
            directed=False
        )),
        params=EvaluationParams(feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 5: Wrong boolean answer
    print_example(
        "Example 5: Incorrect Boolean Answer (Standard Feedback)",
        response=Response(is_bipartite=False),
        answer=Answer(is_bipartite=True),
        params=EvaluationParams(feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 6: Same with minimal feedback
    print_example(
        "Example 6: Incorrect Boolean Answer (Minimal Feedback)",
        response=Response(is_bipartite=False),
        answer=Answer(is_bipartite=True),
        params=EvaluationParams(feedback_level="minimal", tolerance=1e-9)
    )
    
    # Example 7: Same with detailed feedback
    print_example(
        "Example 7: Path Error (Detailed Feedback with Hints)",
        response=Response(path=["A", "C"]),
        answer=Answer(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )),
        params=EvaluationParams(feedback_level="detailed", tolerance=1e-9)
    )
    
    # Example 8: Wrong numeric answer
    print_example(
        "Example 8: Incorrect Numeric Answer",
        response=Response(chromatic_number=5),
        answer=Answer(chromatic_number=3),
        params=EvaluationParams(feedback_level="detailed", tolerance=1e-9)
    )
    
    # Example 9: Spanning tree with cycle
    print_example(
        "Example 9: Spanning Tree Contains a Cycle",
        response=Response(spanning_tree=[
            Edge(source="A", target="B"),
            Edge(source="B", target="C"),
            Edge(source="C", target="A")  # Creates a cycle
        ]),
        answer=Answer(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[
                Edge(source="A", target="B"),
                Edge(source="B", target="C"),
                Edge(source="C", target="A")
            ],
            directed=False
        )),
        params=EvaluationParams(feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 10: Spanning tree wrong number of edges
    print_example(
        "Example 10: Spanning Tree with Wrong Number of Edges",
        response=Response(spanning_tree=[
            Edge(source="A", target="B")
            # Missing edges!
        ]),
        answer=Answer(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
            edges=[
                Edge(source="A", target="B"),
                Edge(source="B", target="C"),
                Edge(source="C", target="D"),
                Edge(source="A", target="D")
            ],
            directed=False
        )),
        params=EvaluationParams(feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 11: Correct answer with standard feedback
    print_example(
        "Example 11: Correct Graph Match",
        response=Response(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )),
        answer=Answer(graph=Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
            edges=[Edge(source="A", target="B"), Edge(source="B", target="C")],
            directed=True
        )),
        params=EvaluationParams(evaluation_type="graph_match", feedback_level="standard", tolerance=1e-9)
    )
    
    # Example 12: Set answer with missing elements
    print_example(
        "Example 12: Vertex Cover Missing Elements",
        response=Response(vertex_cover=["A", "B"]),
        answer=Answer(vertex_cover=["A", "B", "C", "D"]),
        params=EvaluationParams(feedback_level="standard", tolerance=1e-9)
    )
    
    print("\n" + "="*80)
    print("✅ Feedback demonstration complete!")
    print("="*80)
    print("\n📚 Summary of Feedback Features:")
    print("  • Specific error messages (missing nodes, extra edges, conflicts)")
    print("  • Three feedback levels: minimal, standard, detailed")
    print("  • Context-aware hints for common mistakes")
    print("  • Clear indication of expected vs actual values")
    print("  • Validation of graph structures, paths, colorings, and more")
    print("="*80)


if __name__ == "__main__":
    main()
