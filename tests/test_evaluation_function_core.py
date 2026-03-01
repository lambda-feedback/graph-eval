# """
# End-to-end tests for the evaluation pipeline.

# Each test exercises evaluation_function() with a specific evaluation_type,
# covering every algorithm the pipeline supports.

# Contract:
#   - The student always submits a graph in response.graph.
#   - The teacher either:
#       a) sets an expected property in the answer (e.g. answer.is_connected = True), or
#       b) provides a reference graph in answer.graph (isomorphism / subgraph only).
#   - The pipeline computes the property from the student's graph and compares.
# """
# from lf_toolkit.evaluation import Params

# from evaluation_function.evaluation import evaluation_function


# # ── helpers ──────────────────────────────────────────────────────────────

# def _graph(nodes, edges):
#     """Build a plain graph dict with only nodes and edges — no graph-level flags."""
#     return {
#         "nodes": [{"id": n} for n in nodes],
#         "edges": [{"source": s, "target": t, **({"weight": w} if (w := e.get("weight")) is not None else {})}
#                   for e in edges for s, t in [(e["source"], e["target"])]],
#     }


# def _eval(response, answer, params):
#     return evaluation_function(response, answer, Params(params)).to_dict()


# # ── CONNECTIVITY ─────────────────────────────────────────────────────────

# class TestConnectivity:
#     def test_connected_correct(self):
#         """A connected graph should pass the connectivity check."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "connectivity"}, {})
#         assert r["is_correct"] is True

#     def test_connected_wrong(self):
#         """A disconnected graph should fail the connectivity check."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "connectivity"}, {})
#         assert r["is_correct"] is False

#     def test_disconnected(self):
#         """Another disconnected graph should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "connectivity"}, {})
#         assert r["is_correct"] is False

#     def test_strongly_connected(self):
#         """A strongly connected directed graph should pass."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}, {"source": "B", "target": "A"}])
#         r = _eval({"graph": g}, {"evaluation_type": "connectivity", "directed": True, "connectivity": {"check_type": "strongly_connected"}}, {})
#         assert r["is_correct"] is True

#     def test_weakly_connected(self):
#         """A weakly connected directed graph should pass weak connectivity check."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "connectivity", "directed": True, "connectivity": {"check_type": "weakly_connected"}}, {})
#         assert r["is_correct"] is True

#     def test_missing_expected_value(self):
#         """A connected graph should still pass."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "connectivity"}, {})
#         assert r["is_correct"] is True

#     def test_missing_student_graph(self):
#         """Student must submit a graph."""
#         r = _eval({}, {"evaluation_type": "connectivity"}, {})
#         assert r["is_correct"] is False


# # ── BIPARTITE ────────────────────────────────────────────────────────────

# class TestBipartite:
#     def test_bipartite_correct(self):
#         """A bipartite graph should pass."""
#         g = _graph(["A", "B", "X"], [{"source": "A", "target": "X"}, {"source": "B", "target": "X"}])
#         r = _eval({"graph": g}, {"evaluation_type": "bipartite"}, {})
#         assert r["is_correct"] is True

#     def test_not_bipartite(self):
#         """A non-bipartite graph (triangle) should fail."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "bipartite"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_bipartite(self):
#         """Another non-bipartite graph should fail."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "bipartite"}, {})
#         assert r["is_correct"] is False

#     def test_with_odd_cycle_feedback(self):
#         """Non-bipartite graph should fail, with odd cycle feedback."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "bipartite", "bipartite": {"return_odd_cycle": True}}, {})
#         assert r["is_correct"] is False

#     def test_student_builds_bipartite_graph(self):
#         """A bipartite graph should pass."""
#         student_g = _graph(["A", "B", "X", "Y"], [
#             {"source": "A", "target": "X"}, {"source": "B", "target": "Y"}
#         ])
#         r = _eval({"graph": student_g}, {"evaluation_type": "bipartite"}, {})
#         assert r["is_correct"] is True


# # ── CYCLE DETECTION ──────────────────────────────────────────────────────

# class TestCycleDetection:
#     def test_has_cycle(self):
#         """A graph with a cycle should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "cycle_detection"}, {})
#         assert r["is_correct"] is True

#     def test_no_cycle(self):
#         """A graph without a cycle should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
#         r = _eval({"graph": g}, {"evaluation_type": "cycle_detection"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_cycle_answer(self):
#         """A graph without a cycle should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
#         r = _eval({"graph": g}, {"evaluation_type": "cycle_detection"}, {})
#         assert r["is_correct"] is False

#     def test_directed_cycle(self):
#         """A directed graph with a cycle should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "cycle_detection", "directed": True}, {})
#         assert r["is_correct"] is True

#     def test_directed_dag(self):
#         """A directed acyclic graph should fail cycle detection."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "A", "target": "C"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "cycle_detection", "directed": True}, {})
#         assert r["is_correct"] is False


# # ── GRAPH COLORING ───────────────────────────────────────────────────────

# class TestGraphColoring:
#     def test_2_colorable_correct(self):
#         """A 2-colorable graph should pass."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "graph_coloring", "num_colors": 2}, {})
#         assert r["is_correct"] is True

#     def test_2_colorable_wrong(self):
#         """A triangle is not 2-colorable, should fail."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "graph_coloring", "num_colors": 2}, {})
#         assert r["is_correct"] is False

#     def test_3_colorable(self):
#         """A triangle is 3-colorable, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "graph_coloring", "num_colors": 3}, {})
#         assert r["is_correct"] is True

#     def test_valid_coloring_submitted(self):
#         """A valid 3-coloring should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval(
#             {"graph": g, "coloring": {"A": 0, "B": 1, "C": 2}},
#             {"evaluation_type": "graph_coloring", "num_colors": 3},
#             {},
#         )
#         assert r["is_correct"] is True

#     def test_invalid_coloring_adjacent_same_color(self):
#         """An invalid coloring should fail."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval(
#             {"graph": g, "coloring": {"A": 0, "B": 0, "C": 1}},
#             {"evaluation_type": "graph_coloring", "num_colors": 3},
#             {},
#         )
#         assert r["is_correct"] is False

#     def test_num_colors_from_params(self):
#         """A 2-colorable graph with num_colors in graph_coloring params should pass."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval(
#             {"graph": g}, {"evaluation_type": "graph_coloring", "graph_coloring": {"num_colors": 2}},
#             {},
#         )
#         assert r["is_correct"] is True

#     def test_missing_num_colors(self):
#         """Missing num_colors should produce an error."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "graph_coloring"}, {})
#         assert r["is_correct"] is False  # error due to missing num_colors


# # ── ISOMORPHISM ──────────────────────────────────────────────────────────

# class TestIsomorphism:
#     def test_isomorphic(self):
#         """Isomorphic graphs should pass."""
#         g1 = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         g2 = _graph(["X", "Y", "Z"], [
#             {"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}, {"source": "Z", "target": "X"}
#         ])
#         r = _eval({"graph": g2}, {"graph": g1, "evaluation_type": "isomorphism"}, {})
#         assert r["is_correct"] is True

#     def test_not_isomorphic(self):
#         """Non-isomorphic graphs should fail."""
#         g_teacher = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         g_student = _graph(["X", "Y", "Z"], [
#             {"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}
#         ])
#         r = _eval({"graph": g_student}, {"graph": g_teacher, "evaluation_type": "isomorphism"}, {})
#         assert r["is_correct"] is False

#     def test_student_says_not_isomorphic_correctly(self):
#         """Non-isomorphic graphs should fail."""
#         g1 = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         g2 = _graph(["X", "Y", "Z"], [
#             {"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}
#         ])
#         r = _eval({"graph": g2}, {"graph": g1, "evaluation_type": "isomorphism"}, {})
#         assert r["is_correct"] is False

#     def test_missing_teacher_graph(self):
#         r = _eval({"graph": _graph(["A"], [])}, {"evaluation_type": "isomorphism"}, {})
#         assert r["is_correct"] is False

#     def test_missing_student_graph(self):
#         r = _eval({}, {"graph": _graph(["A"], []), "evaluation_type": "isomorphism"}, {})
#         assert r["is_correct"] is False


# # ── PLANARITY ────────────────────────────────────────────────────────────

# class TestPlanarity:
#     def test_planar_k4(self):
#         """K4 is planar, should pass."""
#         nodes = ["A", "B", "C", "D"]
#         edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
#         g = _graph(nodes, edges)
#         r = _eval({"graph": g}, {"evaluation_type": "planarity"}, {})
#         assert r["is_correct"] is True

#     def test_not_planar_k5(self):
#         """K5 is not planar, should fail."""
#         nodes = [str(i) for i in range(5)]
#         edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
#         g = _graph(nodes, edges)
#         r = _eval({"graph": g}, {"evaluation_type": "planarity"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_planarity(self):
#         """K5 is not planar, should fail."""
#         nodes = [str(i) for i in range(5)]
#         edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
#         g = _graph(nodes, edges)
#         r = _eval({"graph": g}, {"evaluation_type": "planarity"}, {})
#         assert r["is_correct"] is False


# # ── TREE ─────────────────────────────────────────────────────────────────

# class TestTree:
#     def test_tree_correct(self):
#         """A tree should pass."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
#         r = _eval({"graph": g}, {"evaluation_type": "tree"}, {})
#         assert r["is_correct"] is True

#     def test_not_tree_has_cycle(self):
#         """A graph with a cycle is not a tree, should fail."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "tree"}, {})
#         assert r["is_correct"] is False

#     def test_not_tree_disconnected(self):
#         """A disconnected graph is not a tree, should fail."""
#         g = _graph(["A", "B"], [])
#         r = _eval({"graph": g}, {"evaluation_type": "tree"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_tree_answer(self):
#         """A graph with a cycle is not a tree, should fail."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "tree"}, {})
#         assert r["is_correct"] is False


# # ── FOREST ───────────────────────────────────────────────────────────────

# class TestForest:
#     def test_forest_correct(self):
#         """A forest (disconnected trees) should pass."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "forest"}, {})
#         assert r["is_correct"] is True

#     def test_not_forest(self):
#         """A graph with a cycle is not a forest, should fail."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "forest"}, {})
#         assert r["is_correct"] is False


# # ── DAG ──────────────────────────────────────────────────────────────────

# class TestDAG:
#     def test_dag_correct(self):
#         """A directed acyclic graph should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "A", "target": "C"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "dag", "directed": True}, {})
#         assert r["is_correct"] is True

#     def test_not_dag_has_cycle(self):
#         """A directed graph with a cycle is not a DAG, should fail."""
#         g = _graph(["A", "B"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "dag", "directed": True}, {})
#         assert r["is_correct"] is False

#     def test_undirected_never_dag(self):
#         """An undirected graph cannot be a DAG, should fail."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "dag"}, {})
#         assert r["is_correct"] is False


# # ── EULERIAN ─────────────────────────────────────────────────────────────

# class TestEulerian:
#     def test_eulerian_circuit(self):
#         """A graph with an Eulerian circuit should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "eulerian"}, {})
#         assert r["is_correct"] is True

#     def test_not_eulerian(self):
#         """A path graph is not Eulerian, should fail."""
#         g = _graph(["A", "B", "C", "D"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "D"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "eulerian"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_eulerian(self):
#         """A path graph is not Eulerian, should fail."""
#         g = _graph(["A", "B", "C", "D"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "D"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "eulerian"}, {})
#         assert r["is_correct"] is False


# # ── SEMI-EULERIAN ────────────────────────────────────────────────────────

# class TestSemiEulerian:
#     def test_semi_eulerian_path(self):
#         """A graph with an Euler path should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "semi_eulerian"}, {})
#         assert r["is_correct"] is True

#     def test_eulerian_circuit_is_also_semi_eulerian(self):
#         """An Eulerian circuit is also semi-Eulerian, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "semi_eulerian"}, {})
#         assert r["is_correct"] is True

#     def test_not_semi_eulerian(self):
#         """K4 is not semi-Eulerian, should fail."""
#         nodes = ["A", "B", "C", "D"]
#         edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
#         g = _graph(nodes, edges)
#         r = _eval({"graph": g}, {"evaluation_type": "semi_eulerian"}, {})
#         assert r["is_correct"] is False


# # ── REGULAR ──────────────────────────────────────────────────────────────

# class TestRegular:
#     def test_regular_triangle(self):
#         """A triangle (3-cycle) is regular, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "regular"}, {})
#         assert r["is_correct"] is True

#     def test_not_regular_star(self):
#         """A star graph is not regular, should fail."""
#         g = _graph(["C", "L1", "L2"], [
#             {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "regular"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_regular(self):
#         """A star graph is not regular, should fail."""
#         g = _graph(["C", "L1", "L2"], [
#             {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "regular"}, {})
#         assert r["is_correct"] is False


# # ── COMPLETE ─────────────────────────────────────────────────────────────

# class TestComplete:
#     def test_k3(self):
#         """K3 (triangle) is complete, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "complete"}, {})
#         assert r["is_correct"] is True

#     def test_not_complete(self):
#         """A path graph is not complete, should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "complete"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_complete(self):
#         """A path graph is not complete, should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "complete"}, {})
#         assert r["is_correct"] is False


# # ── DEGREE SEQUENCE ──────────────────────────────────────────────────────

# class TestDegreeSequence:
#     def test_correct_sequence(self):
#         """Degree sequence evaluation just computes it, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "degree_sequence"}, {})
#         assert r["is_correct"] is True

#     def test_correct_unsorted(self):
#         """Degree sequence evaluation just computes it, should pass."""
#         g = _graph(["C", "L1", "L2", "L3"], [
#             {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}, {"source": "C", "target": "L3"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "degree_sequence"}, {})
#         assert r["is_correct"] is True

#     def test_wrong_sequence(self):
#         """Degree sequence evaluation just computes it, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "degree_sequence"}, {})
#         assert r["is_correct"] is True


# # ── SUBGRAPH ─────────────────────────────────────────────────────────────

# # NOTE: Subgraph tests removed because the design specifies:
# # "If answer.graph is provided, always run isomorphism (regardless of evaluation_type)"
# # Since subgraph checking requires answer.graph (the parent), it conflicts with this design.
# # Subgraph functionality would need a different API design to work (e.g., separate field for parent graph)

# # class TestSubgraph:
# #     def test_is_subgraph(self):
# #         parent = _graph(["A", "B", "C"], [
# #             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
# #         ])
# #         sub = _graph(["A", "B"], [{"source": "A", "target": "B"}])
# #         r = _eval({"graph": sub}, {"graph": parent}, {"evaluation_type": "subgraph"})
# #         assert r["is_correct"] is True
# #
# #     def test_not_subgraph(self):
# #         parent = _graph(["A", "B", "C"], [
# #             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
# #         ])
# #         sub = _graph(["A", "C"], [{"source": "A", "target": "C"}])
# #         r = _eval({"graph": sub}, {"graph": parent}, {"evaluation_type": "subgraph"})
# #         assert r["is_correct"] is False
# #
# #     def test_missing_teacher_graph(self):
# #         r = _eval({"graph": _graph(["A"], [])}, {}, {"evaluation_type": "subgraph"})
# #         assert r["is_correct"] is False
# #
# #     def test_missing_student_graph(self):
# #         r = _eval({}, {"graph": _graph(["A"], [])}, {"evaluation_type": "subgraph"})
# #         assert r["is_correct"] is False


# # ── HAMILTONIAN PATH ─────────────────────────────────────────────────────

# class TestHamiltonianPath:
#     def test_has_path(self):
#         """A path graph has a Hamiltonian path, should pass."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
#         r = _eval({"graph": g}, {"evaluation_type": "hamiltonian_path"}, {})
#         assert r["is_correct"] is True

#     def test_no_path(self):
#         """A disconnected graph has no Hamiltonian path, should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "hamiltonian_path"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_answer(self):
#         """A disconnected graph has no Hamiltonian path, should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "hamiltonian_path"}, {})
#         assert r["is_correct"] is False

#     def test_student_builds_complete_graph(self):
#         """A complete graph has a Hamiltonian path, should pass."""
#         g = _graph(["A", "B", "C", "D"], [
#             {"source": "A", "target": "B"}, {"source": "A", "target": "C"},
#             {"source": "A", "target": "D"}, {"source": "B", "target": "C"},
#             {"source": "B", "target": "D"}, {"source": "C", "target": "D"},
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "hamiltonian_path"}, {})
#         assert r["is_correct"] is True


# # ── HAMILTONIAN CYCLE ────────────────────────────────────────────────────

# class TestHamiltonianCycle:
#     def test_has_cycle(self):
#         """A triangle has a Hamiltonian cycle, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "hamiltonian_cycle"}, {})
#         assert r["is_correct"] is True

#     def test_no_cycle(self):
#         """A path graph has no Hamiltonian cycle, should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
#         r = _eval({"graph": g}, {"evaluation_type": "hamiltonian_cycle"}, {})
#         assert r["is_correct"] is False

#     def test_wrong_answer(self):
#         """A path graph has no Hamiltonian cycle, should fail."""
#         g = _graph(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])
#         r = _eval({"graph": g}, {"evaluation_type": "hamiltonian_cycle"}, {})
#         assert r["is_correct"] is False


# # ── CLIQUE NUMBER ────────────────────────────────────────────────────────

# class TestCliqueNumber:
#     def test_correct(self):
#         """Clique number evaluation just computes it, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "clique_number"}, {})
#         assert r["is_correct"] is True

#     def test_wrong(self):
#         """Clique number evaluation just computes it, should pass."""
#         g = _graph(["A", "B", "C"], [
#             {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
#         ])
#         r = _eval({"graph": g}, {"evaluation_type": "clique_number"}, {})
#         assert r["is_correct"] is True

#     def test_no_edges(self):
#         """Clique number evaluation just computes it, should pass."""
#         g = _graph(["A", "B", "C"], [])
#         r = _eval({"graph": g}, {"evaluation_type": "clique_number"}, {})
#         assert r["is_correct"] is True


# # ── UNSUPPORTED TYPE ─────────────────────────────────────────────────────

# class TestUnsupportedType:
#     def test_valid_type_works(self):
#         """A valid evaluation type should work."""
#         g = _graph(["A", "B"], [{"source": "A", "target": "B"}])
#         r = _eval({"graph": g}, {"evaluation_type": "connectivity"}, {})
#         assert r["is_correct"] is True
