"""
CFG module: CFG extraction and call-graph linking.

Provides:
  - CfgAnalyzer       — binary → CFG + call graph
  - build_incidence_matrix  — call graph → adjacency matrix
  - link_two_programs       — two-program matching and matrix assembly
"""

from src.cfg.cfg_analyzer import CfgAnalyzer
from src.cfg.call_graph_linker import build_incidence_matrix, link_two_programs
