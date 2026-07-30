"""
Comparison module: function matching between binaries.

Provides:
  - match_functions_custom  — graph/hash-based CPU matching
  - match_functions_gpu     — asm2vec GPU embedding matching
"""

from src.comparison.function_comparator import match_functions_custom, match_functions_gpu
