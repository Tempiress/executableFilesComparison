"""
GPU-aware multiprocessing batch comparison with checkpoint support.
Delegates to src.batch.batch_processor.

Usage: python run_batch_final.py --workers 3 --test
       python run_batch_final.py --workers 4 --batch-size 8
"""

import multiprocessing
import sys
import datetime
from line_profiler_pycharm import profile

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
