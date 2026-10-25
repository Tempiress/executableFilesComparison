"""
ResearchWorkCUDA — Obfuscation Resilience Batch Runner.

Conducts full-scale static binary comparison of Clean (P_orig) vs Deobfuscated (P_deobf) binaries:
  Clean directory:  ./coreutils-polybench-hashcat/aoc/Os/
  Target directory: ./OBF/polybench-hashcat-deo/
  Checkpoint log:   ./results/logs/checkpoint_deo.log
  Resource log:     ./results/logs/resource_deo.log
  Comparison log:   ./results/logs/batch_results_deo.log

Features:
  - 18-parameter evaluation basis (SSDeep + Nilsimsa across 5 instruction modes, custom & GPU).
  - Parallel multiprocessing with GPU VRAM semaphore protection.
  - Automatic checkpoint resumption (skips already-completed configurations).
  - LanceDB vector embedding cache + .r2_cache CFG cache for maximum throughput.

Usage:
  python run_batch_resilience.py --workers 4
  python run_batch_resilience.py --test
  python run_batch_resilience.py --workers 4 --obfuscations bcf cff bcf-cff sub
  python run_batch_resilience.py --workers 4 --programs 2mm atax
"""

import datetime
import multiprocessing
import os
import sys
from pathlib import Path

# Ensure process spawning is safe on Windows
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

# Ensure working directory is set to project root
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.batch.batch_processor import main


if __name__ == '__main__':
    start_time = datetime.datetime.now()

    cli_args = sys.argv[1:]

    # Supply default flags for the Resilience study unless explicitly provided
    defaults = {
        '--target-dir': './OBF/polybench-hashcat-deo/',
        '--checkpoint-file': './results/logs/checkpoint_deo.log',
        '--log-file': './results/logs/resource_deo.log',
        '--comparison-log': './results/logs/batch_results_deo.log',
        '--workers': '4',
    }

    merged_args = []
    for flag, default_val in defaults.items():
        if flag not in cli_args:
            merged_args.extend([flag, default_val])

    # CLI args override defaults
    merged_args.extend(cli_args)

    print("=" * 80)
    print(" RESEARCHWORKCUDA: OBFUSCATION RESILIENCE BATCH EVALUATION ")
    print("=" * 80)
    print(f"Start time:        {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target directory:  ./OBF/polybench-hashcat-deo/")
    print(f"Clean directory:   ./coreutils-polybench-hashcat/aoc/Os/")
    print(f"Checkpoint log:    ./results/logs/checkpoint_deo.log")
    print("=" * 80)

    main(args=merged_args)

    end_time = datetime.datetime.now()
    elapsed = end_time - start_time
    print("\n" + "=" * 80)
    print(f"Resilience batch evaluation finished.")
    print(f"Total execution time: {elapsed}")
    print("=" * 80)
