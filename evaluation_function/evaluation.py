from __future__ import annotations

from typing import Any, Optional

from lf_toolkit.evaluation import Result, Params
from pydantic import ValidationError

from evaluation_function.algorithms import (
    bipartite_info,
    clique_number,
    connectivity_info,
    cycle_info,
    degree_sequence,
    has_hamiltonian_cycle,
    has_hamiltonian_path,
    is_complete,
    is_dag,
    is_eulerian,
    is_forest,
    is_n_colorable,
    is_planar,
    is_regular,
    is_semi_eulerian,
    is_subgraph,
    is_tree,
    isomorphism_info,
)
from evaluation_function.schemas import Answer, EvaluationParams, Graph, Response


def evaluation_function(
    response: Any,
    answer: Any,
    params: Params,
) -> Result:
    """
    Function used to evaluate a student response.
    ---
    The handler function passes three arguments to evaluation_function():

    - `response` which are the answers provided by the student.
    - `answer` which are the correct answers to compare against.
    - `params` which are any extra parameters that may be useful,
        e.g., error tolerances.

    The output of this function is what is returned as the API response
    and therefore must be JSON-encodable. It must also conform to the
    response schema.

    Any standard python library may be used, as well as any package
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or
    split into many) is entirely up to you. All that matters are the
    return types and that evaluation_function() is the main function used
    to output the evaluation response.
    """

    # ── helpers ──────────────────────────────────────────────────────────

    def _to_dictish(obj: Any) -> Any:
        if obj is None:
            return None
        if isinstance(obj, (dict, list, str, int, float, bool)):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return obj

    def _ok() -> Result:
        return Result(is_correct=True)

    def _err(msg: str) -> Result:
        return Result(is_correct=False, feedback_items=[("error", msg)])

    # ── parse & validate inputs ──────────────────────────────────────────

    try:
        resp = Response.model_validate(_to_dictish(response) or {})
    except ValidationError as e:
        return _err(f"Invalid response schema: {e}")

    try:
        ans = Answer.model_validate(_to_dictish(answer) or {})
    except ValidationError as e:
        return _err(f"Invalid answer schema: {e}")

    raw_params = _to_dictish(params) or {}
    try:
        p = EvaluationParams.model_validate(raw_params)
    except ValidationError as e:
        return _err(
            "Invalid params schema. Expected e.g. "
            "{'evaluation_type': 'connectivity'|'bipartite'|'graph_coloring'|...}. "
            f"Error: {e}"
        )

    # ── resolve graphs ───────────────────────────────────────────────────
    # expected_graph: the authoritative / question graph (usually answer.graph)
    # student_graph:  the student-submitted graph (usually response.graph)
    expected_graph: Optional[Graph] = ans.graph or resp.graph
    student_graph: Optional[Graph] = resp.graph or ans.graph

    eval_type = p.evaluation_type

    # ── helper: grade a simple boolean property ──────────────────────────
    def _grade_bool(
        label: str,
        expected: Optional[bool],
        student: Optional[bool],
        compute_fn,  # callable(Graph) -> bool
        *,
        graph_for_expected: Optional[Graph] = expected_graph,
        graph_for_student: Optional[Graph] = student_graph,
    ) -> Result:
        if graph_for_expected is None or graph_for_student is None:
            return _err("No graph provided in either response.graph or answer.graph.")
        exp = expected if expected is not None else compute_fn(graph_for_expected)
        stu = student if student is not None else compute_fn(graph_for_student)
        if bool(stu) == bool(exp):
            return _ok()
        return _err(f"{label}: expected={exp}, got={stu}.")

    # ── CONNECTIVITY ─────────────────────────────────────────────────────
    if eval_type == "connectivity":
        if expected_graph is None or student_graph is None:
            return _err("No graph provided in either response.graph or answer.graph.")

        conn_params = p.connectivity
        check_type = conn_params.check_type if conn_params else "connected"

        expected = ans.is_connected
        if expected is None:
            expected = connectivity_info(
                expected_graph, connectivity_type=check_type, return_components=False
            ).is_connected

        student_value = resp.is_connected
        if student_value is None:
            student_value = connectivity_info(
                student_graph, connectivity_type=check_type, return_components=False
            ).is_connected

        is_correct = bool(student_value) == bool(expected)
        if is_correct:
            return _ok()

        details = connectivity_info(student_graph, connectivity_type=check_type, return_components=True)
        fb = f"Connectivity ({check_type}): expected={expected}, got={student_value}."
        if details.components is not None:
            fb += f" Components={details.components}."
        return _err(fb)

    # ── BIPARTITE ────────────────────────────────────────────────────────
    if eval_type == "bipartite":
        if expected_graph is None or student_graph is None:
            return _err("No graph provided in either response.graph or answer.graph.")

        b_params = p.bipartite
        want_parts = bool(b_params.return_partitions) if b_params else False
        want_odd = bool(b_params.return_odd_cycle) if b_params else False

        expected = ans.is_bipartite
        if expected is None:
            expected = bipartite_info(expected_graph).is_bipartite

        student_value = resp.is_bipartite
        if student_value is None:
            student_value = bipartite_info(student_graph).is_bipartite

        is_correct = bool(student_value) == bool(expected)
        if is_correct:
            return _ok()

        details = bipartite_info(student_graph, return_partitions=want_parts, return_odd_cycle=want_odd)
        fb = f"Bipartite: expected={expected}, got={student_value}."
        if want_parts and details.partitions is not None:
            fb += f" Partitions={details.partitions}."
        if want_odd and details.odd_cycle is not None:
            fb += f" Odd cycle={details.odd_cycle}."
        return _err(fb)

    # ── CYCLE DETECTION ──────────────────────────────────────────────────
    if eval_type == "cycle_detection":
        if expected_graph is None or student_graph is None:
            return _err("No graph provided in either response.graph or answer.graph.")

        expected = ans.has_cycle
        if expected is None:
            expected = cycle_info(expected_graph).has_cycle

        student_value = resp.has_cycle
        if student_value is None:
            student_value = cycle_info(student_graph).has_cycle

        is_correct = bool(student_value) == bool(expected)
        if is_correct:
            return _ok()

        details = cycle_info(student_graph)
        fb = f"Cycle detection: expected={expected}, got={student_value}."
        if details.cycle is not None:
            fb += f" Cycle found={details.cycle}."
        return _err(fb)

    # ── GRAPH COLORING ───────────────────────────────────────────────────
    if eval_type == "graph_coloring":
        if expected_graph is None or student_graph is None:
            return _err("No graph provided in either response.graph or answer.graph.")

        gc_params = p.graph_coloring
        num_colors = gc_params.num_colors if (gc_params and gc_params.num_colors is not None) else ans.num_colors
        if num_colors is None:
            return _err("Missing num_colors: provide in params.graph_coloring.num_colors or answer.num_colors.")

        # Expected colorability
        expected = ans.is_colorable
        if expected is None:
            expected = is_n_colorable(expected_graph, num_colors).is_colorable

        # Student answer
        student_value = resp.is_colorable
        student_coloring = resp.coloring

        # If student supplied an explicit coloring, validate it
        if student_coloring is not None:
            # Verify the student's coloring is a proper coloring
            adj: dict[str, set[str]] = {n.id: set() for n in student_graph.nodes}
            for e in student_graph.edges:
                adj[e.source].add(e.target)
                adj[e.target].add(e.source)

            valid_coloring = True
            invalid_reason = ""
            node_ids = {n.id for n in student_graph.nodes}
            for nid in node_ids:
                if nid not in student_coloring:
                    valid_coloring = False
                    invalid_reason = f"Node '{nid}' has no color assigned."
                    break
            if valid_coloring:
                for nid, color in student_coloring.items():
                    if color < 0 or color >= num_colors:
                        valid_coloring = False
                        invalid_reason = f"Node '{nid}' has color {color}, but only {num_colors} colors (0..{num_colors - 1}) are allowed."
                        break
                    for nb in adj.get(nid, set()):
                        if student_coloring.get(nb) == color:
                            valid_coloring = False
                            invalid_reason = f"Adjacent nodes '{nid}' and '{nb}' share color {color}."
                            break
                    if not valid_coloring:
                        break

            if not valid_coloring:
                return _err(f"Graph coloring ({num_colors}-coloring): invalid coloring. {invalid_reason}")

            # Coloring is valid ⇒ the graph is colorable; check vs expected
            if not expected:
                return _err(
                    f"Graph coloring ({num_colors}-coloring): student provided a valid coloring, "
                    f"but the expected answer says the graph is NOT {num_colors}-colorable."
                )
            return _ok()

        # No explicit coloring — grade the boolean
        if student_value is None:
            student_value = is_n_colorable(student_graph, num_colors).is_colorable

        is_correct = bool(student_value) == bool(expected)
        if is_correct:
            return _ok()

        fb = f"Graph coloring ({num_colors}-coloring): expected={expected}, got={student_value}."
        ref = is_n_colorable(student_graph, num_colors)
        if ref.coloring is not None:
            fb += f" A valid coloring exists: {ref.coloring}."
        return _err(fb)

    # ── ISOMORPHISM ──────────────────────────────────────────────────────
    if eval_type == "isomorphism":
        if ans.graph is None or resp.graph is None:
            return _err("Isomorphism requires both answer.graph and response.graph.")

        expected = ans.is_isomorphic
        student_value = resp.is_isomorphic

        result = isomorphism_info(ans.graph, resp.graph)

        if expected is None:
            expected = result.is_isomorphic
        if student_value is None:
            student_value = result.is_isomorphic

        is_correct = bool(student_value) == bool(expected)
        if is_correct:
            return _ok()

        fb = f"Isomorphism: expected={expected}, got={student_value}."
        if result.node_mapping is not None:
            fb += f" Mapping={result.node_mapping}."
        return _err(fb)

    # ── PLANARITY ────────────────────────────────────────────────────────
    if eval_type == "planarity":
        return _grade_bool(
            "Planarity",
            ans.is_planar,
            resp.is_planar,
            is_planar,
        )

    # ── TREE ─────────────────────────────────────────────────────────────
    if eval_type == "tree":
        return _grade_bool(
            "Tree",
            ans.is_tree,
            resp.is_tree,
            is_tree,
        )

    # ── FOREST ───────────────────────────────────────────────────────────
    if eval_type == "forest":
        return _grade_bool(
            "Forest",
            ans.is_forest,
            resp.is_forest,
            is_forest,
        )

    # ── DAG ──────────────────────────────────────────────────────────────
    if eval_type == "dag":
        return _grade_bool(
            "DAG",
            ans.is_dag,
            resp.is_dag,
            is_dag,
        )

    # ── EULERIAN ─────────────────────────────────────────────────────────
    if eval_type == "eulerian":
        return _grade_bool(
            "Eulerian circuit",
            ans.is_eulerian,
            resp.is_eulerian,
            is_eulerian,
        )

    # ── SEMI-EULERIAN ────────────────────────────────────────────────────
    if eval_type == "semi_eulerian":
        return _grade_bool(
            "Semi-Eulerian (Euler path)",
            ans.is_semi_eulerian,
            resp.is_semi_eulerian,
            is_semi_eulerian,
        )

    # ── REGULAR ──────────────────────────────────────────────────────────
    if eval_type == "regular":
        return _grade_bool(
            "Regular",
            ans.is_regular,
            resp.is_regular,
            is_regular,
        )

    # ── COMPLETE ─────────────────────────────────────────────────────────
    if eval_type == "complete":
        return _grade_bool(
            "Complete",
            ans.is_complete,
            resp.is_complete,
            is_complete,
        )

    # ── DEGREE SEQUENCE ──────────────────────────────────────────────────
    if eval_type == "degree_sequence":
        if expected_graph is None or student_graph is None:
            return _err("No graph provided in either response.graph or answer.graph.")

        expected_seq = ans.degree_sequence
        if expected_seq is None:
            expected_seq = degree_sequence(expected_graph)

        student_seq = resp.degree_sequence
        if student_seq is None:
            student_seq = degree_sequence(student_graph)

        # Normalise both to descending order for comparison
        expected_sorted = sorted(expected_seq, reverse=True)
        student_sorted = sorted(student_seq, reverse=True)

        if expected_sorted == student_sorted:
            return _ok()
        return _err(
            f"Degree sequence: expected={expected_sorted}, got={student_sorted}."
        )

    # ── SUBGRAPH ─────────────────────────────────────────────────────────
    if eval_type == "subgraph":
        if ans.graph is None or resp.graph is None:
            return _err("Subgraph check requires both answer.graph (parent) and response.graph (candidate).")

        result = is_subgraph(resp.graph, ans.graph)
        if result:
            return _ok()
        return _err("Subgraph: response.graph is NOT a subgraph of answer.graph.")

    # ── HAMILTONIAN PATH ─────────────────────────────────────────────────
    if eval_type == "hamiltonian_path":
        return _grade_bool(
            "Hamiltonian path",
            ans.has_hamiltonian_path,
            resp.has_hamiltonian_path,
            has_hamiltonian_path,
        )

    # ── HAMILTONIAN CYCLE ────────────────────────────────────────────────
    if eval_type == "hamiltonian_cycle":
        return _grade_bool(
            "Hamiltonian cycle",
            ans.has_hamiltonian_cycle,
            resp.has_hamiltonian_cycle,
            has_hamiltonian_cycle,
        )

    # ── CLIQUE NUMBER ────────────────────────────────────────────────────
    if eval_type == "clique_number":
        if expected_graph is None or student_graph is None:
            return _err("No graph provided in either response.graph or answer.graph.")

        expected_cn = ans.clique_number
        if expected_cn is None:
            expected_cn = clique_number(expected_graph)

        student_cn = resp.clique_number
        if student_cn is None:
            student_cn = clique_number(student_graph)

        if student_cn == expected_cn:
            return _ok()
        return _err(f"Clique number: expected={expected_cn}, got={student_cn}.")

    # ── UNSUPPORTED ──────────────────────────────────────────────────────
    return _err(f"Unsupported evaluation_type: '{eval_type}'.")