"""
Batch module: parallel binary comparison with checkpoint support.

Provides:
  - extract_features  — CFG + call graph extraction for a pair
  - run_comparison    — full two-program comparison pipeline
  - run               — single-pair convenience entry point
  - process_file_pair_worker  — multiprocessing worker
  - main              — CLI for batch processing
"""

from src.batch.batch_processor import (
    extract_features,
    run_comparison,
    run,
    process_file_pair_worker,
    main,
)
