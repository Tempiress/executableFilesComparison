"""
Cached precomputation wrapper for function data.

PrecomputedFunc stores parsed blocks and block-link graph for a function,
reusing cached results when the same (func_data, config) pair is requested.
"""

from src.core.instruction_parser import parse_function_blocks
from src.core.block_links import compute_block_links


class PrecomputedFunc:
    """Lazily-parsed function data with per-config caching.

    On first access, parses the function's CFG into normalised blocks and
    computes the intra-function block-link graph.  Subsequent requests with
    the same *func_data* object id and config are served from cache.
    """

    _cache = {}

    def __new__(cls, name: str, func_data: dict, config):
        cache_key = (id(func_data), config.hash_type, config.instructions_mode)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        instance = super().__new__(cls)
        instance.name = name
        instance.data = parse_function_blocks(func_data, config=config)
        instance.block_links = compute_block_links(instance.data)
        cls._cache[cache_key] = instance
        return instance

    def __init__(self, name: str, func_data: dict, config):
        # Initialisation is handled in __new__ to avoid re-parsing on cache hits
        pass
