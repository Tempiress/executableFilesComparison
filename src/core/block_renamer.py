"""
Block renaming for cross-function comparison.

Given two sets of parsed blocks and a similarity matching,
renames block ids in the second function so they align with the first.
"""


def rename_blocks(blocks_a: dict, blocks_b: dict, similarity_matches: dict):
    """Copy and rename block ids in *blocks_b* to match *blocks_a*.

    Blocks matched by *similarity_matches* receive the matching block's id
    from *blocks_a*. Unmatched blocks receive the next available id.

    Args:
        blocks_a: Parsed blocks of the first function.
        blocks_b: Parsed blocks of the second function (will be copied).
        similarity_matches: Output of match_similar_blocks.

    Returns:
        (renamed_blocks, [len(blocks_a), len(renamed_blocks)])
    """
    blocks_b_copy = {k: v.copy() for k, v in blocks_b.items()}
    used_ids = set()

    # Reset all ids
    for block_data in blocks_b_copy.values():
        block_data["id"] = -1

    # Assign matched ids
    for match in similarity_matches.values():
        blocks_b_copy[match["similar_to"]]["id"] = match["block"]
        used_ids.add(int(match["block"]))

    # Fill remaining with available ids
    available_ids = [i for i in range(1, len(blocks_b_copy) + 1) if i not in used_ids]
    available_idx = 0

    for block_data in blocks_b_copy.values():
        if block_data["id"] != -1:
            continue
        if available_idx < len(available_ids):
            block_data["id"] = available_ids[available_idx]
            used_ids.add(available_ids[available_idx])
            available_idx += 1

    return blocks_b_copy, [len(blocks_a), len(blocks_b_copy)]
