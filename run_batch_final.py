"""
GPU-aware multiprocessing batch comparison with checkpoint support.
Delegates to src.batch.batch_processor.

Usage: python run_batch_final.py --workers 3 --test
       python run_batch_final.py --workers 4 --batch-size 8
"""

import multiprocessing
import os
import sys
import datetime
from pathlib import Path

# Ensure working directory is set to project root
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from line_profiler_pycharm import profile
except ImportError:
    pass

try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

from src.batch.batch_processor import main

if __name__ == '__main__':
    start_time = datetime.datetime.now()

    main()
    end_time = datetime.datetime.now()
    print(f" === time_of_working:  {end_time - start_time} ====")
