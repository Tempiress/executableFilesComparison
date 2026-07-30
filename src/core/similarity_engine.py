"""
Core similarity computation engine.
"""

import sys
import time

import numpy as np

from src.core.config import safe_load_json
from src.core.instruction_parser import match_similar_blocks
from src.core.block_renamer import rename_blocks
from src.core.block_links import compute_block_links
from src.core.precomputed_func import PrecomputedFunc

MIN_BLOCKS_FOR_GRAPH = 4


def _block_content_similarity(blocks_a: dict, blocks_b: dict, config) -> float:
    """Content-only similarity for functions too small for graph analysis."""
    similarity_matches = match_similar_blocks(blocks_a, blocks_b, config=config)
    if not similarity_matches:
        return 0.0
    total = 0.0
    for match in similarity_matches.values():
        if match.get('simequal', 0) == 1:
            total += 1.0
        else:
            total += match.get('simcount', 0) / 100.0
    return total / max(len(blocks_a), len(blocks_b))


def build_cfg_matrices(links_a: dict, links_b: dict):
    """Build (N x N) adjacency matrices from two block-link graphs."""
    max_block_id = 0
    for links in (links_a, links_b):
        for block_data in links.values():
            max_block_id = max(
                max_block_id,
                int(block_data.get("NumBlock", 0)),
                int(block_data.get("NumBlockLinks", 0)),
                int(block_data.get("NumBlockFail", 0)),
            )
    matrix_size = max_block_id + 2
    matrix_a = np.zeros((matrix_size, matrix_size), dtype=np.int8)
    matrix_b = np.zeros((matrix_size, matrix_size), dtype=np.int8)

    indices_a = [(int(b["NumBlock"]), int(b["NumBlockLinks"])) for b in links_a.values()]
    indices_a_fail = [
        (int(b["NumBlock"]), int(b["NumBlockFail"]))
        for b in links_a.values() if int(b["NumBlockFail"]) >= 0
    ]
    indices_b = [(int(b["NumBlock"]), int(b["NumBlockLinks"])) for b in links_b.values()]
    indices_b_fail = [
        (int(b["NumBlock"]), int(b["NumBlockFail"]))
        for b in links_b.values() if int(b["NumBlockFail"]) >= 0
    ]

    if indices_a:
        rows, cols = zip(*indices_a)
        matrix_a[rows, cols] = 1
    if indices_a_fail:
        rows, cols = zip(*indices_a_fail)
        matrix_a[rows, cols] = 1
    if indices_b:
        rows, cols = zip(*indices_b)
        matrix_b[rows, cols] = 1
    if indices_b_fail:
        rows, cols = zip(*indices_b_fail)
        matrix_b[rows, cols] = 1

    return matrix_a, matrix_b


def fast_similarity(pref_a, pref_b, config):
    """Compute structural similarity between two precomputed functions."""
    try:
        similarity_matches = match_similar_blocks(pref_a.data, pref_b.data, config=config)
        renamed_blocks_b, diff = rename_blocks(pref_a.data, pref_b.data, similarity_matches)
        renamed_links_b = compute_block_links(renamed_blocks_b)
        matrix_a, matrix_b = build_cfg_matrices(pref_a.block_links, renamed_links_b)

        matrix_size = min(len(pref_a.data), len(pref_b.data)) + 1
        max_matrix_size = max(len(pref_a.data), len(pref_b.data)) + 1
        actual_size = min(matrix_size, matrix_a.shape[0])

        sim_weights = np.zeros(matrix_size, dtype=np.float32)
        for match in similarity_matches.values():
            try:
                idx = int(match.get('block', -1))
                if 0 < idx < matrix_size:
                    sim_weights[idx] = (
                        1.0 if match.get('simequal', 0) == 1
                        else match.get('simcount', 0) / 100.0
                    )
            except (ValueError, TypeError):
                continue

        core_a = matrix_a[1:actual_size, 1:actual_size]
        core_b = matrix_b[1:actual_size, 1:actual_size]
        edge_match = 1 ^ (core_a ^ core_b)
        weight_slice = sim_weights[1:actual_size]
        weight_sum = weight_slice[:, np.newaxis] + weight_slice

        numerator = float(np.sum(edge_match * weight_sum))
        if max_matrix_size <= 1:
            return 0.0, diff

        score = float(numerator) / ((max_matrix_size - 1) * (max_matrix_size - 1) * 2)
        return score, diff

    except Exception:
        return 0.0, 0


def compute_function_similarity(func_name_a, func_name_b, functions_a, functions_b, config):
    """Compute similarity between two named functions."""
    if func_name_a not in functions_a or func_name_b not in functions_b:
        return 0.0, 0
    pref_a = PrecomputedFunc(func_name_a, functions_a[func_name_a], config)
    pref_b = PrecomputedFunc(func_name_b, functions_b[func_name_b], config)
    return fast_similarity(pref_a, pref_b, config)


def compute_program_similarity(
    call_graph_matrix_a, call_graph_matrix_b,
    max_program_size: int, functions_a: dict, functions_b: dict, config,
) -> float:
    """Compute overall similarity between two programs."""
    def _extract_labels(matrix):
        if hasattr(matrix, 'shape'):
            if matrix.shape[0] > 0 and matrix.shape[1] > 1:
                return matrix[0, 1:]
        elif len(matrix) > 0 and len(matrix[0]) > 1:
            return matrix[0][1:]
        return []

    labels_a = _extract_labels(call_graph_matrix_a)
    labels_b = _extract_labels(call_graph_matrix_b)
    if len(labels_a) == 0 or len(labels_b) == 0:
        return 0.0

    cache_a, cache_b = {}, {}
    for name in set(labels_a):
        if name in functions_a:
            cache_a[name] = PrecomputedFunc(name, functions_a[name], config)
    for name in set(labels_b):
        if name in functions_b:
            cache_b[name] = PrecomputedFunc(name, functions_b[name], config)

    matrix_size = len(call_graph_matrix_a)
    if matrix_size <= 1:
        return 0.0

    max_k = min(len(labels_a), len(labels_b), matrix_size - 1)
    sim_array = np.zeros(max_k, dtype=np.float32)

    for k in range(max_k):
        name_a, name_b = labels_a[k], labels_b[k]
        sim_val = 0.0
        if name_a in cache_a and name_b in cache_b:
            na, nb = len(cache_a[name_a].data), len(cache_b[name_b].data)
            if na >= MIN_BLOCKS_FOR_GRAPH and nb >= MIN_BLOCKS_FOR_GRAPH:
                sim_val, _ = fast_similarity(cache_a[name_a], cache_b[name_b], config=config)
            else:
                sim_val = _block_content_similarity(cache_a[name_a].data, cache_b[name_b].data, config)
        sim_array[k] = sim_val

    try:
        if hasattr(call_graph_matrix_a, 'astype'):
            core_a = call_graph_matrix_a[1:max_k+1, 1:max_k+1].astype(np.float32).astype(np.int8)
            core_b = call_graph_matrix_b[1:max_k+1, 1:max_k+1].astype(np.float32).astype(np.int8)
        else:
            core_a = np.zeros((max_k, max_k), dtype=np.int8)
            core_b = np.zeros((max_k, max_k), dtype=np.int8)
            for i in range(max_k):
                for j in range(max_k):
                    try: core_a[i, j] = int(call_graph_matrix_a[i+1][j+1])
                    except: pass
                    try: core_b[i, j] = int(call_graph_matrix_b[i+1][j+1])
                    except: pass
    except:
        core_a = np.zeros((max_k, max_k), dtype=np.int8)
        core_b = np.zeros((max_k, max_k), dtype=np.int8)

    edge_match = 1 ^ (core_a ^ core_b)
    weight_sum = sim_array[:, np.newaxis] + sim_array
    numerator = float(np.sum(edge_match * weight_sum))

    if max_program_size <= 1:
        return 0.0
    return float(numerator) / ((max_program_size - 1) * (max_program_size - 1) * 2)
