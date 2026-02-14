from __future__ import annotations

from typing import Any, Optional

from lf_toolkit.evaluation import Result, Params
from pydantic import ValidationError

from evaluation_function.algorithms import bipartite_info, connectivity_info, cycle_info, shortest_path_info
from evaluation_function.algorithms.shortest_path import NegativeCycleError
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
        # lf_toolkit.Result does not take `feedback=...`; it takes feedback_items.
        return Result(is_correct=False, feedback_items=[("error", msg)])

    try:
        resp = Response.model_validate(_to_dictish(response) or {})
    except ValidationError as e:
        return _err(f"Invalid response schema: {e}")

    try:
        ans = Answer.model_validate(_to_dictish(answer) or {})
    except ValidationError as e:
        return _err(f"Invalid answer schema: {e}")

    # lf_toolkit Params may not be a plain dict; best-effort coercion
    raw_params = _to_dictish(params) or {}
    try:
        p = EvaluationParams.model_validate(raw_params)
    except ValidationError as e:
        return _err(
            "Invalid params schema. Expected e.g. "
            "{evaluation_type: 'connectivity'|'shortest_path'|'bipartite', ...}. "
            f"Error: {e}"
        )

    # Graph selection:
    # - If the task is 'compute a property', the graph is typically in answer.graph (question graph).
    # - If the task is 'build a graph with a property', the graph is typically in response.graph.
    expected_graph: Optional[Graph] = ans.graph or resp.graph
    student_graph: Optional[Graph] = resp.graph or ans.graph

    if expected_graph is None or student_graph is None:
        return _err("No graph provided in either response.graph or answer.graph.")

    eval_type = p.evaluation_type

    if eval_type == "connectivity":
        conn_params = p.connectivity
        check_type = conn_params.check_type if conn_params else "connected"
        want_components = bool(conn_params.return_components) if conn_params else False

        expected = ans.is_connected
        if expected is None:
            expected = connectivity_info(expected_graph, connectivity_type=check_type, return_components=False).is_connected

        # If student explicitly provided a boolean answer, grade that; otherwise grade the graph property.
        student_value = resp.is_connected
        if student_value is None:
            student_value = connectivity_info(student_graph, connectivity_type=check_type, return_components=False).is_connected

        details = connectivity_info(student_graph, connectivity_type=check_type, return_components=want_components)
        is_correct = bool(student_value) == bool(expected)
        fb = f"Connectivity ({check_type}): expected={expected}, got={student_value}."
        if want_components and details.components is not None:
            fb += f" components={details.components}"
        return _ok() if is_correct else _err(fb)

    if eval_type == "bipartite":
        b_params = p.bipartite
        want_parts = bool(b_params.return_partitions) if b_params else False
        want_odd = bool(b_params.return_odd_cycle) if b_params else False

        expected = ans.is_bipartite
        if expected is None:
            expected = bipartite_info(expected_graph).is_bipartite

        student_value = resp.is_bipartite
        if student_value is None:
            student_value = bipartite_info(student_graph).is_bipartite

        details = bipartite_info(student_graph, return_partitions=want_parts, return_odd_cycle=want_odd)
        is_correct = bool(student_value) == bool(expected)
        fb = f"Bipartite: expected={expected}, got={student_value}."
        if want_parts and details.partitions is not None:
            fb += f" partitions={details.partitions}"
        if want_odd and details.odd_cycle is not None:
            fb += f" odd_cycle={details.odd_cycle}"
        return _ok() if is_correct else _err(fb)

    if eval_type in {"cycle_detection", "find_all_cycles"}:
        c_params = p.cycle_detection
        find_all = True if eval_type == "find_all_cycles" else bool(c_params.find_all) if c_params else False
        min_len = int(c_params.min_length) if c_params else 3
        max_len = c_params.max_length if c_params else None
        max_nodes = int(c_params.max_nodes) if c_params else 15
        max_cycles = int(c_params.max_cycles) if c_params else 1000
        want_cycles = bool(c_params.return_cycles) if c_params else True

        expected = ans.has_cycle
        if expected is None:
            expected = cycle_info(
                expected_graph,
                find_all=False,
                return_cycles=False,
                return_girth=False,
                return_shortest_cycle=False,
            ).has_cycle

        student_value = resp.has_cycle
        if student_value is None:
            student_value = cycle_info(
                student_graph,
                find_all=False,
                return_cycles=False,
                return_girth=False,
                return_shortest_cycle=False,
            ).has_cycle

        details = cycle_info(
            student_graph,
            find_all=find_all,
            min_length=min_len,
            max_length=max_len,
            max_nodes=max_nodes,
            max_cycles=max_cycles,
            return_cycles=want_cycles,
            return_girth=False,
            return_shortest_cycle=False,
        )

        is_correct = bool(student_value) == bool(expected)
        fb = f"Cycle detection: expected={expected}, got={student_value}."
        if want_cycles and details.cycles is not None:
            fb += f" cycles_found={len(details.cycles)}"
        return _ok() if is_correct else _err(fb)

    if eval_type == "shortest_cycle":
        c_params = p.cycle_detection
        min_len = int(c_params.min_length) if c_params else 3
        max_len = c_params.max_length if c_params else None

        expected_girth = ans.girth
        if expected_girth is None:
            expected_girth = cycle_info(
                expected_graph,
                find_all=False,
                min_length=min_len,
                max_length=max_len,
                return_cycles=False,
                return_girth=True,
                return_shortest_cycle=False,
            ).girth

        student_girth = resp.girth
        if student_girth is None:
            student_girth = cycle_info(
                student_graph,
                find_all=False,
                min_length=min_len,
                max_length=max_len,
                return_cycles=False,
                return_girth=True,
                return_shortest_cycle=False,
            ).girth

        # Treat acyclic graphs as girth=None
        is_correct = student_girth == expected_girth
        fb = f"Shortest cycle (girth): expected={expected_girth}, got={student_girth}."
        return _ok() if is_correct else _err(fb)

    if eval_type == "negative_cycle":
        n_params = p.negative_cycle
        want_cycle = bool(n_params.return_cycle) if n_params else True
        source_node = n_params.source_node if n_params else None

        expected_neg = cycle_info(
            expected_graph,
            detect_negative_cycle=True,
            return_negative_cycle=False,
            negative_cycle_source_node=source_node,
            return_cycles=False,
            return_girth=False,
            return_shortest_cycle=False,
        ).has_negative_cycle
        expected_neg_bool = bool(expected_neg)

        details = cycle_info(
            student_graph,
            detect_negative_cycle=True,
            return_negative_cycle=want_cycle,
            negative_cycle_source_node=source_node,
            return_cycles=False,
            return_girth=False,
            return_shortest_cycle=False,
        )
        student_neg_bool = bool(details.has_negative_cycle)

        is_correct = student_neg_bool == expected_neg_bool
        fb = f"Negative cycle: expected={expected_neg_bool}, got={student_neg_bool}."
        if want_cycle and details.negative_cycle is not None:
            fb += f" negative_cycle={details.negative_cycle}"
        return _ok() if is_correct else _err(fb)

    if eval_type == "shortest_path":
        sp = p.shortest_path
        if sp is None:
            return _err("Missing params.shortest_path for evaluation_type='shortest_path'.")

        try:
            expected_info = shortest_path_info(
                expected_graph,
                source=sp.source_node,
                target=sp.target_node,
                algorithm=sp.algorithm if sp.algorithm != "auto" else "auto",
            )
        except NegativeCycleError as e:
            return _err(f"Expected graph has a negative cycle: {e}")

        try:
            student_info = shortest_path_info(
                student_graph,
                source=sp.source_node,
                target=sp.target_node,
                algorithm=sp.algorithm if sp.algorithm != "auto" else "auto",
                supplied_path=resp.path,
            )
        except NegativeCycleError as e:
            return _err(f"Student graph has a negative cycle: {e}")
        except ValueError as e:
            return _err(str(e))

        # Determine expected distance:
        expected_distance = ans.shortest_distance if ans.shortest_distance is not None else ans.distance
        if expected_distance is None:
            expected_distance = expected_info.distance

        # Determine student distance:
        student_distance = resp.distance if resp.distance is not None else student_info.distance

        if expected_distance is None:
            return _err("Could not determine expected shortest distance.")
        if student_distance is None:
            return _err("Could not determine student's shortest distance (distance/path).")

        tol = ans.tolerance if hasattr(ans, "tolerance") else 1e-9
        is_correct = abs(float(student_distance) - float(expected_distance)) <= float(tol)

        fb = (
            f"Shortest path {sp.source_node}->{sp.target_node}: "
            f"expected_distance={expected_distance}, got_distance={student_distance}, "
            f"algorithm_used={student_info.algorithm_used}."
        )
        if resp.path is not None:
            fb += (
                f" supplied_path_valid={student_info.supplied_path_is_valid},"
                f" supplied_path_weight={student_info.supplied_path_weight},"
                f" supplied_path_is_shortest={student_info.supplied_path_is_shortest}."
            )

        return _ok() if is_correct else _err(fb)

    return _err(f"Unsupported evaluation_type: {eval_type}")