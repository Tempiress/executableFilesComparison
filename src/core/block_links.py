"""
Block-link graph construction for a single function.

Given parsed blocks (from parse_function_blocks), builds a dict mapping
each block id to its successor (jump) and fall-through (fail) targets.
"""


def compute_block_links(parsed_blocks: dict) -> dict:
    """Build the intra-procedural block-link graph.

    Malformed jump/fail data from Radare2 is silently skipped.
    """
    links = {}

    addr_to_block_id = {
        block_data["block"]: block_key
        for block_key, block_data in parsed_blocks.items()
    }

    for block_key, block_data in parsed_blocks.items():
        successor_addr = 0
        successor_id = 0
        fail_block_id = -1
        fail_addr = ''

        # Linear fall-through when no jump
        if not block_data.get("jumps"):
            next_key = int(block_key) + 1
            if next_key <= len(parsed_blocks):
                links[block_key] = {
                    "block": block_data["block"],
                    "NumBlock": block_data["id"],
                    "links": parsed_blocks[next_key]["block"],
                    "NumBlockLinks": parsed_blocks[next_key]["id"],
                    "fail": '',
                    "NumBlockFail": -1,
                }
            continue

        # Parse jump target address
        try:
            target_addr = int(block_data["jumps"].rstrip('; '))
        except ValueError:
            continue

        # Parse fail (fall-through) target address
        if block_data.get("fails", '') != '':
            try:
                fail_addr = int(block_data["fails"].rstrip('; '))
            except ValueError:
                continue

        # O(1) lookup of jump successor
        if target_addr in addr_to_block_id:
            found_key = addr_to_block_id[target_addr]
            if block_key != found_key:
                successor_addr = target_addr
                successor_id = found_key

        links[block_key] = {
            "block": block_data["block"],
            "NumBlock": block_data["id"],
            "links": successor_addr,
            "NumBlockLinks": successor_id,
            "fail": fail_addr,
            "NumBlockFail": fail_block_id,
        }

        # O(1) lookup of fail successor
        if fail_addr != '' and fail_addr in addr_to_block_id:
            found_key = addr_to_block_id[fail_addr]
            if block_key != found_key:
                links[block_key]["fail"] = fail_addr
                links[block_key]["NumBlockFail"] = parsed_blocks[found_key]["id"]

    return links
