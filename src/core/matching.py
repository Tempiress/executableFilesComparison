"""
Function-pair matching evaluation metrics.
"""


def evaluate_matching(
    matched_nodes_p1: list, matched_nodes_p2: list, total_p1: int = None
) -> dict:
    """Compute precision/recall for a function-pair matching.

    Each pair (matched_nodes_p1[i], matched_nodes_p2[i]) is treated as
    a correct match if their ``old_label`` values are equal.

    Args:
        matched_nodes_p1: Matched functions from the first program.
        matched_nodes_p2: Matched functions from the second program.
        total_p1: Total number of functions in the first program (for recall).

    Returns:
        dict with keys: correct, total_matched, precision, recall
    """
    total_matched = len(matched_nodes_p1)
    correct = 0

    for n1, n2 in zip(matched_nodes_p1, matched_nodes_p2):
        if n1['old_label'] == n2['old_label']:
            correct += 1

    precision = round(correct / total_matched, 4) if total_matched else 0.0

    if total_p1 is not None:
        recall = round(correct / total_p1, 4)
    else:
        raise NotImplementedError("total_p1 count is required")

    return {
        "correct": correct,
        "total_matched": total_matched,
        "precision": precision,
        "recall": recall,
    }
