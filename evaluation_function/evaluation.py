from __future__ import annotations

from typing import Any, Callable, Optional

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
    # student_graph (resp.graph) is always present — the student submits a graph.
    # ans.graph is only present for isomorphism / subgraph checks where the
    # teacher provides a reference graph.  For all other eval types the teacher
    # sets the expected property value directly in the answer (e.g. ans.is_connected).
    student_graph: Graph = resp.graph
    if student_graph is None:
        return _err("response.graph is required — the student must submit a graph.")

    # ── helper: grade a simple boolean property ──────────────────────────
    def _grade_bool(
        label: str,
        expected: Optional[bool],
        compute_fn: Callable[[Graph], bool],
    ) -> Result:
        if expected is None:
            return _err(f"{label}: expected value not set by the teacher in the answer.")
        stu = compute_fn(student_graph)
        if bool(stu) == bool(expected):
            return _ok()
        return _err(f"{label}: expected={expected}, got={stu}.")

    # ── evaluation-type handlers ─────────────────────────────────────────

    def _eval_connectivity() -> Result:
        conn_params = p.connectivity
        check_type = conn_params.check_type if conn_params else "connected"

        expected = ans.is_connected
        if expected is None:
            return _err("Connectivity: expected value (answer.is_connected) not set by the teacher.")

        student_value = connectivity_info(
            student_graph, connectivity_type=check_type, return_components=False
        ).is_connected

        if bool(student_value) == bool(expected):
            return _ok()

        details = connectivity_info(student_graph, connectivity_type=check_type, return_components=True)
        fb = f"Connectivity ({check_type}): expected={expected}, got={student_value}."
        if details.components is not None:
            fb += f" Components={details.components}."
        return _err(fb)

    def _eval_bipartite() -> Result:
        b_params = p.bipartite
        want_parts = bool(b_params.return_partitions) if b_params else False
        want_odd = bool(b_params.return_odd_cycle) if b_params else False

        expected = ans.is_bipartite
        if expected is None:
            return _err("Bipartite: expected value (answer.is_bipartite) not set by the teacher.")

        student_value = bipartite_info(student_graph).is_bipartite

        if bool(student_value) == bool(expected):
            return _ok()

        details = bipartite_info(student_graph, return_partitions=want_parts, return_odd_cycle=want_odd)
        fb = f"Bipartite: expected={expected}, got={student_value}."
        if want_parts and details.partitions is not None:
            fb += f" Partitions={details.partitions}."
        if want_odd and details.odd_cycle is not None:
            fb += f" Odd cycle={details.odd_cycle}."
        return _err(fb)

    def _eval_cycle_detection() -> Result:
        expected = ans.has_cycle
        if expected is None:
            return _err("Cycle detection: expected value (answer.has_cycle) not set by the teacher.")

        student_value = cycle_info(student_graph).has_cycle

        if bool(student_value) == bool(expected):
            return _ok()

        details = cycle_info(student_graph)
        fb = f"Cycle detection: expected={expected}, got={student_value}."
        if details.cycle is not None:
            fb += f" Cycle found={details.cycle}."
        return _err(fb)

    def _eval_graph_coloring() -> Result:
        gc_params = p.graph_coloring
        num_colors = gc_params.num_colors if (gc_params and gc_params.num_colors is not None) else ans.num_colors
        if num_colors is None:
            return _err("Missing num_colors: provide in params.graph_coloring.num_colors or answer.num_colors.")

        expected = ans.is_colorable
        if expected is None:
            return _err("Graph coloring: expected value (answer.is_colorable) not set by the teacher.")

        student_coloring = resp.coloring

        if student_coloring is not None:
            adj: dict[str, set[str]] = {n.id: set() for n in student_graph.nodes}
            for e in student_graph.edges:
                adj[e.source].add(e.target)
                if not student_graph.directed:
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

            if not expected:
                return _err(
                    f"Graph coloring ({num_colors}-coloring): student provided a valid coloring, "
                    f"but the expected answer says the graph is NOT {num_colors}-colorable."
                )
            return _ok()

        student_value = is_n_colorable(student_graph, num_colors).is_colorable

        if bool(student_value) == bool(expected):
            return _ok()

        fb = f"Graph coloring ({num_colors}-coloring): expected={expected}, got={student_value}."
        ref = is_n_colorable(student_graph, num_colors)
        if ref.coloring is not None:
            fb += f" A valid coloring exists: {ref.coloring}."
        return _err(fb)

    def _eval_isomorphism() -> Result:
        if ans.graph is None:
            return _err("Isomorphism requires answer.graph (the teacher's reference graph).")

        result = isomorphism_info(ans.graph, student_graph)

        # Teacher provides a reference graph; by default the student's graph
        # must be isomorphic to it (expected=True).
        expected = ans.is_isomorphic if ans.is_isomorphic is not None else True

        if bool(result.is_isomorphic) == bool(expected):
            return _ok()

        fb = f"Isomorphism: expected={expected}, got={result.is_isomorphic}."
        if result.node_mapping is not None:
            fb += f" Mapping={result.node_mapping}."
        return _err(fb)

    def _eval_planarity() -> Result:
        return _grade_bool("Planarity", ans.is_planar, is_planar)

    def _eval_tree() -> Result:
        return _grade_bool("Tree", ans.is_tree, is_tree)

    def _eval_forest() -> Result:
        return _grade_bool("Forest", ans.is_forest, is_forest)

    def _eval_dag() -> Result:
        return _grade_bool("DAG", ans.is_dag, is_dag)

    def _eval_eulerian() -> Result:
        return _grade_bool("Eulerian circuit", ans.is_eulerian, is_eulerian)

    def _eval_semi_eulerian() -> Result:
        return _grade_bool("Semi-Eulerian (Euler path)", ans.is_semi_eulerian, is_semi_eulerian)

    def _eval_regular() -> Result:
        return _grade_bool("Regular", ans.is_regular, is_regular)

    def _eval_complete() -> Result:
        return _grade_bool("Complete", ans.is_complete, is_complete)

    def _eval_degree_sequence() -> Result:
        expected_seq = ans.degree_sequence
        if expected_seq is None:
            return _err("Degree sequence: expected value (answer.degree_sequence) not set by the teacher.")

        student_seq = degree_sequence(student_graph)

        expected_sorted = sorted(expected_seq, reverse=True)
        student_sorted = sorted(student_seq, reverse=True)

        if expected_sorted == student_sorted:
            return _ok()
        return _err(
            f"Degree sequence: expected={expected_sorted}, got={student_sorted}."
        )

    def _eval_subgraph() -> Result:
        if ans.graph is None:
            return _err("Subgraph check requires answer.graph (the parent graph from the teacher).")

        result = is_subgraph(student_graph, ans.graph)
        if result:
            return _ok()
        return _err("Subgraph: the student's graph is NOT a subgraph of the teacher's graph.")

    def _eval_hamiltonian_path() -> Result:
        return _grade_bool("Hamiltonian path", ans.has_hamiltonian_path, has_hamiltonian_path)

    def _eval_hamiltonian_cycle() -> Result:
        return _grade_bool("Hamiltonian cycle", ans.has_hamiltonian_cycle, has_hamiltonian_cycle)

    def _eval_clique_number() -> Result:
        expected_cn = ans.clique_number
        if expected_cn is None:
            return _err("Clique number: expected value (answer.clique_number) not set by the teacher.")

        student_cn = clique_number(student_graph)

        if student_cn == expected_cn:
            return _ok()
        return _err(f"Clique number: expected={expected_cn}, got={student_cn}.")

    # ── dispatch ─────────────────────────────────────────────────────────

    dispatch: dict[str, Callable[[], Result]] = {
        "connectivity": _eval_connectivity,
        "bipartite": _eval_bipartite,
        "cycle_detection": _eval_cycle_detection,
        "graph_coloring": _eval_graph_coloring,
        "isomorphism": _eval_isomorphism,
        "planarity": _eval_planarity,
        "tree": _eval_tree,
        "forest": _eval_forest,
        "dag": _eval_dag,
        "eulerian": _eval_eulerian,
        "semi_eulerian": _eval_semi_eulerian,
        "regular": _eval_regular,
        "complete": _eval_complete,
        "degree_sequence": _eval_degree_sequence,
        "subgraph": _eval_subgraph,
        "hamiltonian_path": _eval_hamiltonian_path,
        "hamiltonian_cycle": _eval_hamiltonian_cycle,
        "clique_number": _eval_clique_number,
    }

    handler = dispatch.get(p.evaluation_type)
    if handler is None:
        return _err(f"Unsupported evaluation_type: '{p.evaluation_type}'.")
    return handler()
