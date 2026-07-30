"""
Core modules: configuration, hashing, instruction parsing,
block similarity matching, and similarity computation engine.
"""

from src.core.config import AnalysisConfig, safe_load_json
from src.core.hashing import create_hasher, cached_ppdeep_compare, cached_levenshtein
from src.core.instruction_parser import (
    GroupInstructions,
    generalize_instruction,
    parse_function_blocks,
    match_similar_blocks,
)
from src.core.precomputed_func import PrecomputedFunc
from src.core.matching import evaluate_matching
from src.core.block_links import compute_block_links
from src.core.block_renamer import rename_blocks
from src.core.similarity_engine import (
    compute_program_similarity,
    compute_function_similarity,
    fast_similarity,
    build_cfg_matrices,
    _block_content_similarity,
    MIN_BLOCKS_FOR_GRAPH,
)
