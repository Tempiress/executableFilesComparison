"""
Call-graph incidence matrix construction and two-program linking.

Key functions:
  - build_incidence_matrix(call_graph, function_names)
  - link_two_programs(functions_a, functions_b, call_graph_a, call_graph_b, config)
"""

import copy

import numpy as np

from src.comparison.function_comparator import match_functions_custom, match_functions_gpu
from src.core.matching import evaluate_matching


# ---------------------------------------------------------------------------
# Incidence matrix builder
# ---------------------------------------------------------------------------

def build_incidence_matrix(call_graph: list, function_names: list) -> np.ndarray:
    """Build an (N+1)×(N+1) incidence matrix from a call graph.

    Row/col 0 holds function name labels.
    Cell [i+1, j+1] is 1 if function i imports function j.
    """
    name_list = [item["name"] for item in call_graph]
    n = len(name_list)
    matrix = np.zeros((n + 1, n + 1), dtype='object')
    matrix[1:, 0] = name_list
    matrix[0, 1:] = name_list

    for i, item in enumerate(call_graph):
        imports = set(item.get("imports", {}))
        for j, name in enumerate(name_list):
            if name != item["name"] and name in imports:
                matrix[i + 1, j + 1] = 1

    return matrix


# ---------------------------------------------------------------------------
# Matrix helpers
# ---------------------------------------------------------------------------

def _swap_columns(matrix, col_a: int, col_b: int):
    for row in matrix:
        row[col_a], row[col_b] = row[col_b], row[col_a]


def _swap_rows(matrix, row_a: int, row_b: int):
    matrix[row_a], matrix[row_b] = copy.copy(matrix[row_b]), copy.copy(matrix[row_a])


# ---------------------------------------------------------------------------
# Two-program linker
# ---------------------------------------------------------------------------

def link_two_programs(
    functions_a: dict,
    functions_b: dict,
    call_graph_a: list,
    call_graph_b: list,
    config,
):
    """Build incidence matrices and match functions between two programs.

    Returns:
        (matrix_a, matrix_b, matched_a, matched_b)
    """
    # Filter call graphs to functions present in *functions_*
    call_graph_a = [item for item in call_graph_a if item["name"] in functions_a]
    call_graph_b = [item for item in call_graph_b if item["name"] in functions_b]

    matrix_a = build_incidence_matrix(call_graph_a, list(functions_a.keys()))
    matrix_b = build_incidence_matrix(call_graph_b, list(functions_b.keys()))

    # Match functions
    if config.compare_mode == 'GPU':
        matched_a, matched_b = match_functions_gpu(
            matrix_a, matrix_b, functions_a, functions_b, config=config
        )
        matching_eval = evaluate_matching(matched_a, matched_b, total_p1=len(functions_a))
        print(
            f"GPU: correct: {matching_eval['correct']} "
            f"total_matched: {matching_eval['total_matched']} "
            f"precision: {matching_eval['precision']} "
            f"recall: {matching_eval['recall']}"
        )
    elif config.compare_mode == 'custom':
        matched_a, matched_b = match_functions_custom(
            matrix_a, matrix_b, functions_a, functions_b, config=config
        )
    else:
        raise NotImplementedError(f"Unknown compare mode: {config.compare_mode}")

    # Reorder matrices so matched functions appear first
    for node in matched_a:
        node['new_label'] = 1
        if node['old_label'] in matrix_a[0]:
            col_idx = np.where(matrix_a[0] == node['old_label'])[0][0]
            if col_idx != node['new_label']:
                _swap_columns(matrix_a, col_idx, node['new_label'] + 1)
                _swap_rows(matrix_a, col_idx, node['new_label'] + 1)

    for node in matched_b:
        node['new_label'] = 1
        if node['old_label'] in matrix_b[0]:
            col_idx = np.where(matrix_b[0] == node['old_label'])[0][0]
            if col_idx != node['new_label']:
                _swap_columns(matrix_b, col_idx, node['new_label'] + 1)
                _swap_rows(matrix_b, col_idx, node['new_label'] + 1)

    return matrix_a, matrix_b, matched_a, matched_b
