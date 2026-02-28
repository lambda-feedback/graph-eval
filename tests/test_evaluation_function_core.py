"""
End-to-end tests for the evaluation pipeline.

Each test exercises evaluation_function() with a specific evaluation_type,
covering every algorithm the pipeline supports.

Contract:
  - The student always submits a graph in response.graph.
  - The teacher either:
      a) sets an expected property in the answer (e.g. answer.is_connected = True), or
      b) provides a reference graph in answer.graph (isomorphism / subgraph only).
  - The pipeline computes the property from the student's graph and compares.
"""
from lf_toolkit.evaluation import Params

from evaluation_function.evaluation import evaluation_function


# ── helpers ──────────────────────────────────────────────────────────────

def _graph(nodes, edges):
    """Build a plain graph dict with only nodes and edges — no graph-level flags."""
    return {
        "nodes": [{"id": n} for n in nodes],
        "edges": [{"source": s, "target": t, **({"weight": w} if (w := e.get("weight")) is not None else {})}
                  for e in edges for s, t in [(e["source"], e["target"])]],
    }


def _eval(response, answer, params):
    return evaluation_function(response, answer, Params(params)).to_dict()


# ── CONNECTIVITY ─────────────────────────────────────────────────────────

class TestConnectivity:
    def test_connected_correct(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_connected": True, "evaluation_type": "connectivity"},
                  {})
        assert r["is_correct"] is True

    def test_connected_wrong(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_connected": True, "evaluation_type": "connectivity"},
                  {})
        assert r["is_correct"] is False

    def test_disconnected(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_connected": False, "evaluation_type": "connectivity"},
                  {})
        assert r["is_correct"] is True

    def test_strongly_connected(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}, {"source": "B", "target": "A"}])
        r = _eval({"graph": g}, {"is_connected": True, "evaluation_type": "connectivity", "directed": True, "connectivity": {"check_type": "strongly_connected"}},
                  {})
        assert r["is_correct"] is True

    def test_weakly_connected(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_connected": True, "evaluation_type": "connectivity", "directed": True, "connectivity": {"check_type": "weakly_connected"}},
                  {})
        assert r["is_correct"] is True

    def test_missing_expected_value(self):
        """Teacher must set answer.is_connected."""
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"evaluation_type": "connectivity"}, {})
        assert r["is_correct"] is False

    def test_missing_student_graph(self):
        """Student must submit a graph."""
        r = _eval({}, {"is_connected": True, "evaluation_type": "connectivity"}, {})
        assert r["is_correct"] is False


# ── BIPARTITE ────────────────────────────────────────────────────────────

class TestBipartite:
    def test_bipartite_correct(self):
        g = _graph(["A", "B", "X"], [{"source": "A", "target": "X"}, {"source": "B", "target": "X"}])
        r = _eval({"graph": g}, {"is_bipartite": True, "evaluation_type": "bipartite"},
                  {})
        assert r["is_correct"] is True

    def test_not_bipartite(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_bipartite": False, "evaluation_type": "bipartite"},
                  {})
        assert r["is_correct"] is True

    def test_wrong_bipartite(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_bipartite": True, "evaluation_type": "bipartite"},
                  {})
        assert r["is_correct"] is False

    def test_with_odd_cycle_feedback(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_bipartite": True, "evaluation_type": "bipartite", "bipartite": {"return_odd_cycle": True}},
                  {})
        assert r["is_correct"] is False

    def test_student_builds_bipartite_graph(self):
        student_g = _graph(["A", "B", "X", "Y"], [
            {"source": "A", "target": "X"}, {"source": "B", "target": "Y"}
        ])
        r = _eval({"graph": student_g}, {"is_bipartite": True, "evaluation_type": "bipartite"},
                  {})
        assert r["is_correct"] is True


# ── CYCLE DETECTION ──────────────────────────────────────────────────────

class TestCycleDetection:
    def test_has_cycle(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"has_cycle": True, "evaluation_type": "cycle_detection"},
                  {})
        assert r["is_correct"] is True

    def test_no_cycle(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
        r = _eval({"graph": g}, {"has_cycle": False, "evaluation_type": "cycle_detection"},
                  {})
        assert r["is_correct"] is True

    def test_wrong_cycle_answer(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
        r = _eval({"graph": g}, {"has_cycle": True, "evaluation_type": "cycle_detection"},
                  {})
        assert r["is_correct"] is False

    def test_directed_cycle(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"has_cycle": True, "evaluation_type": "cycle_detection", "directed": True},
                  {})
        assert r["is_correct"] is True

    def test_directed_dag(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "A", "target": "C"}
        ])
        r = _eval({"graph": g}, {"has_cycle": False, "evaluation_type": "cycle_detection", "directed": True},
                  {})
        assert r["is_correct"] is True


# ── GRAPH COLORING ───────────────────────────────────────────────────────

class TestGraphColoring:
    def test_2_colorable_correct(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_colorable": True, "num_colors": 2, "evaluation_type": "graph_coloring"},
                  {})
        assert r["is_correct"] is True

    def test_2_colorable_wrong(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_colorable": True, "num_colors": 2, "evaluation_type": "graph_coloring"},
                  {})
        assert r["is_correct"] is False

    def test_3_colorable(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_colorable": True, "num_colors": 3, "evaluation_type": "graph_coloring"},
                  {})
        assert r["is_correct"] is True

    def test_valid_coloring_submitted(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval(
            {"graph": g, "coloring": {"A": 0, "B": 1, "C": 2}},
            {"is_colorable": True, "num_colors": 3, "evaluation_type": "graph_coloring"},
            {},
        )
        assert r["is_correct"] is True

    def test_invalid_coloring_adjacent_same_color(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval(
            {"graph": g, "coloring": {"A": 0, "B": 0, "C": 1}},
            {"is_colorable": True, "num_colors": 3, "evaluation_type": "graph_coloring"},
            {},
        )
        assert r["is_correct"] is False

    def test_num_colors_from_params(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval(
            {"graph": g}, {"is_colorable": True, "evaluation_type": "graph_coloring", "graph_coloring": {"num_colors": 2}},
            {},
        )
        assert r["is_correct"] is True

    def test_missing_num_colors(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_colorable": True, "evaluation_type": "graph_coloring"},
                  {})
        assert r["is_correct"] is False  # error due to missing num_colors


# ── ISOMORPHISM ──────────────────────────────────────────────────────────

class TestIsomorphism:
    def test_isomorphic(self):
        g1 = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        g2 = _graph(["X", "Y", "Z"], [
            {"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}, {"source": "Z", "target": "X"}
        ])
        r = _eval({"graph": g2}, {"graph": g1, "evaluation_type": "isomorphism"}, {})
        assert r["is_correct"] is True

    def test_not_isomorphic(self):
        """Student submits a graph that isn't isomorphic to the teacher's."""
        g_teacher = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        g_student = _graph(["X", "Y", "Z"], [
            {"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}
        ])
        r = _eval({"graph": g_student}, {"graph": g_teacher, "evaluation_type": "isomorphism"},
                  {})
        # Graphs are not isomorphic, so the student's graph doesn't match
        assert r["is_correct"] is False

    def test_student_says_not_isomorphic_correctly(self):
        g1 = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        g2 = _graph(["X", "Y", "Z"], [
            {"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}
        ])
        r = _eval({"graph": g2, "is_isomorphic": False}, {"graph": g1, "is_isomorphic": False, "evaluation_type": "isomorphism"},
                  {})
        assert r["is_correct"] is True

    def test_missing_teacher_graph(self):
        r = _eval({"graph": _graph(["A"], [])}, {"evaluation_type": "isomorphism"}, {})
        assert r["is_correct"] is False

    def test_missing_student_graph(self):
        r = _eval({}, {"graph": _graph(["A"], []), "evaluation_type": "isomorphism"}, {})
        assert r["is_correct"] is False


# ── PLANARITY ────────────────────────────────────────────────────────────

class TestPlanarity:
    def test_planar_k4(self):
        nodes = ["A", "B", "C", "D"]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        g = _graph(nodes, edges)
        r = _eval({"graph": g}, {"is_planar": True, "evaluation_type": "planarity"}, {})
        assert r["is_correct"] is True

    def test_not_planar_k5(self):
        nodes = [str(i) for i in range(5)]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        g = _graph(nodes, edges)
        r = _eval({"graph": g}, {"is_planar": False, "evaluation_type": "planarity"}, {})
        assert r["is_correct"] is True

    def test_wrong_planarity(self):
        nodes = [str(i) for i in range(5)]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        g = _graph(nodes, edges)
        r = _eval({"graph": g}, {"is_planar": True, "evaluation_type": "planarity"}, {})
        assert r["is_correct"] is False


# ── TREE ─────────────────────────────────────────────────────────────────

class TestTree:
    def test_tree_correct(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
        r = _eval({"graph": g}, {"is_tree": True, "evaluation_type": "tree"}, {})
        assert r["is_correct"] is True

    def test_not_tree_has_cycle(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_tree": False, "evaluation_type": "tree"}, {})
        assert r["is_correct"] is True

    def test_not_tree_disconnected(self):
        g = _graph(["A", "B"], [])
        r = _eval({"graph": g}, {"is_tree": False, "evaluation_type": "tree"}, {})
        assert r["is_correct"] is True

    def test_wrong_tree_answer(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_tree": True, "evaluation_type": "tree"}, {})
        assert r["is_correct"] is False


# ── FOREST ───────────────────────────────────────────────────────────────

class TestForest:
    def test_forest_correct(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_forest": True, "evaluation_type": "forest"}, {})
        assert r["is_correct"] is True

    def test_not_forest(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_forest": True, "evaluation_type": "forest"}, {})
        assert r["is_correct"] is False


# ── DAG ──────────────────────────────────────────────────────────────────

class TestDAG:
    def test_dag_correct(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "A", "target": "C"}
        ])
        r = _eval({"graph": g}, {"is_dag": True, "evaluation_type": "dag", "directed": True}, {})
        assert r["is_correct"] is True

    def test_not_dag_has_cycle(self):
        g = _graph(["A", "B"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_dag": False, "evaluation_type": "dag", "directed": True}, {})
        assert r["is_correct"] is True

    def test_undirected_never_dag(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_dag": True, "evaluation_type": "dag"}, {})
        assert r["is_correct"] is False


# ── EULERIAN ─────────────────────────────────────────────────────────────

class TestEulerian:
    def test_eulerian_circuit(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_eulerian": True, "evaluation_type": "eulerian"}, {})
        assert r["is_correct"] is True

    def test_not_eulerian(self):
        g = _graph(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "D"}
        ])
        r = _eval({"graph": g}, {"is_eulerian": False, "evaluation_type": "eulerian"}, {})
        assert r["is_correct"] is True

    def test_wrong_eulerian(self):
        g = _graph(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "D"}
        ])
        r = _eval({"graph": g}, {"is_eulerian": True, "evaluation_type": "eulerian"}, {})
        assert r["is_correct"] is False


# ── SEMI-EULERIAN ────────────────────────────────────────────────────────

class TestSemiEulerian:
    def test_semi_eulerian_path(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ])
        r = _eval({"graph": g}, {"is_semi_eulerian": True, "evaluation_type": "semi_eulerian"}, {})
        assert r["is_correct"] is True

    def test_eulerian_circuit_is_also_semi_eulerian(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_semi_eulerian": True, "evaluation_type": "semi_eulerian"}, {})
        assert r["is_correct"] is True

    def test_not_semi_eulerian(self):
        nodes = ["A", "B", "C", "D"]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        g = _graph(nodes, edges)
        r = _eval({"graph": g}, {"is_semi_eulerian": False, "evaluation_type": "semi_eulerian"}, {})
        assert r["is_correct"] is True


# ── REGULAR ──────────────────────────────────────────────────────────────

class TestRegular:
    def test_regular_triangle(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_regular": True, "evaluation_type": "regular"}, {})
        assert r["is_correct"] is True

    def test_not_regular_star(self):
        g = _graph(["C", "L1", "L2"], [
            {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}
        ])
        r = _eval({"graph": g}, {"is_regular": False, "evaluation_type": "regular"}, {})
        assert r["is_correct"] is True

    def test_wrong_regular(self):
        g = _graph(["C", "L1", "L2"], [
            {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}
        ])
        r = _eval({"graph": g}, {"is_regular": True, "evaluation_type": "regular"}, {})
        assert r["is_correct"] is False


# ── COMPLETE ─────────────────────────────────────────────────────────────

class TestComplete:
    def test_k3(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"is_complete": True, "evaluation_type": "complete"}, {})
        assert r["is_correct"] is True

    def test_not_complete(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_complete": False, "evaluation_type": "complete"}, {})
        assert r["is_correct"] is True

    def test_wrong_complete(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_complete": True, "evaluation_type": "complete"}, {})
        assert r["is_correct"] is False


# ── DEGREE SEQUENCE ──────────────────────────────────────────────────────

class TestDegreeSequence:
    def test_correct_sequence(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"degree_sequence": [2, 2, 2], "evaluation_type": "degree_sequence"}, {})
        assert r["is_correct"] is True

    def test_correct_unsorted(self):
        g = _graph(["C", "L1", "L2", "L3"], [
            {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}, {"source": "C", "target": "L3"}
        ])
        r = _eval({"graph": g}, {"degree_sequence": [3, 1, 1, 1], "evaluation_type": "degree_sequence"}, {})
        assert r["is_correct"] is True

    def test_wrong_sequence(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"degree_sequence": [3, 3, 3], "evaluation_type": "degree_sequence"}, {})
        assert r["is_correct"] is False


# ── SUBGRAPH ─────────────────────────────────────────────────────────────

# NOTE: Subgraph tests removed because the design specifies:
# "If answer.graph is provided, always run isomorphism (regardless of evaluation_type)"
# Since subgraph checking requires answer.graph (the parent), it conflicts with this design.
# Subgraph functionality would need a different API design to work (e.g., separate field for parent graph)

# class TestSubgraph:
#     def test_is_subgraph(self):
#         parent = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         sub = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": sub}, {"graph": parent}, {"evaluation_type": "subgraph"})
#         assert r["is_correct"] is True
#
#     def test_not_subgraph(self):
#         parent = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
#         ])
#         sub = _graph(["A", "C"], [{"source": "A", "target": "C"}])
#         r = _eval({"graph": sub}, {"graph": parent}, {"evaluation_type": "subgraph"})
#         assert r["is_correct"] is False
#
#     def test_missing_teacher_graph(self):
#         r = _eval({"graph": _graph(["A"], [])}, {}, {"evaluation_type": "subgraph"})
#         assert r["is_correct"] is False
#
#     def test_missing_student_graph(self):
#         r = _eval({}, {"graph": _graph(["A"], [])}, {"evaluation_type": "subgraph"})
#         assert r["is_correct"] is False


# ── HAMILTONIAN PATH ─────────────────────────────────────────────────────

class TestHamiltonianPath:
    def test_has_path(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
        r = _eval({"graph": g}, {"has_hamiltonian_path": True, "evaluation_type": "hamiltonian_path"}, {})
        assert r["is_correct"] is True

    def test_no_path(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"has_hamiltonian_path": False, "evaluation_type": "hamiltonian_path"}, {})
        assert r["is_correct"] is True

    def test_wrong_answer(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"has_hamiltonian_path": True, "evaluation_type": "hamiltonian_path"}, {})
        assert r["is_correct"] is False

    def test_student_builds_complete_graph(self):
        g = _graph(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "A", "target": "C"},
            {"source": "A", "target": "D"}, {"source": "B", "target": "C"},
            {"source": "B", "target": "D"}, {"source": "C", "target": "D"},
        ])
        r = _eval({"graph": g}, {"has_hamiltonian_path": True, "evaluation_type": "hamiltonian_path"}, {})
        assert r["is_correct"] is True


# ── HAMILTONIAN CYCLE ────────────────────────────────────────────────────

class TestHamiltonianCycle:
    def test_has_cycle(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"has_hamiltonian_cycle": True, "evaluation_type": "hamiltonian_cycle"}, {})
        assert r["is_correct"] is True

    def test_no_cycle(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
        r = _eval({"graph": g}, {"has_hamiltonian_cycle": False, "evaluation_type": "hamiltonian_cycle"}, {})
        assert r["is_correct"] is True

    def test_wrong_answer(self):
        g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
        r = _eval({"graph": g}, {"has_hamiltonian_cycle": True, "evaluation_type": "hamiltonian_cycle"}, {})
        assert r["is_correct"] is False


# ── CLIQUE NUMBER ────────────────────────────────────────────────────────

class TestCliqueNumber:
    def test_correct(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"clique_number": 3, "evaluation_type": "clique_number"}, {})
        assert r["is_correct"] is True

    def test_wrong(self):
        g = _graph(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])
        r = _eval({"graph": g}, {"clique_number": 2, "evaluation_type": "clique_number"}, {})
        assert r["is_correct"] is False

    def test_no_edges(self):
        g = _graph(["A", "B", "C"], [])
        r = _eval({"graph": g}, {"clique_number": 1, "evaluation_type": "clique_number"}, {})
        assert r["is_correct"] is True


# ── UNSUPPORTED TYPE ─────────────────────────────────────────────────────

class TestUnsupportedType:
    def test_valid_type_works(self):
        g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
        r = _eval({"graph": g}, {"is_connected": True, "evaluation_type": "connectivity"}, {})
        assert r["is_correct"] is True
