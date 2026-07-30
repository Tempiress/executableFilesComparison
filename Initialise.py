"""
Initialization / sweep runner for batch file comparisons.

Compares every file in one directory against its counterpart in another,
logging fuzzy-hash (ppdeep, tlsh) and program-level scores.
"""

import concurrent.futures
import datetime
import os
import threading
import time

import ppdeep
import tlsh

from src.batch import run


# ---------------------------------------------------------------------------
# Fuzzy-hash helpers
# ---------------------------------------------------------------------------

def ppdeep_compare(file_a: str, file_b: str) -> float:
    """Return ppdeep similarity (0–1) for two files."""
    hash_a = ppdeep.hash_from_file(file_a)
    hash_b = ppdeep.hash_from_file(file_b)
    return ppdeep.compare(hash_a, hash_b) / 100.0


# ---------------------------------------------------------------------------
# Single-pair processor
# ---------------------------------------------------------------------------

_lock = threading.Lock()


def process_single_pair(
    file_a: str,
    file_b: str,
    filename: str,
    l1_dir: str,
    l2_dir0: str,
    l2_dir: str,
    output_handle,
):
    """Compare one pair and append a CSV line to the output file."""
    try:
        prog_start = time.time()
        prog_score = run(file_a, file_b)
        prog_elapsed = round(time.time() - prog_start, 1)
        print(f"RES: {round(prog_score, 5)} Time: {prog_elapsed}")

        ppdeep_start = time.time()
        ppdeep_score = ppdeep_compare(file_a, file_b)
        ppdeep_elapsed = round(time.time() - ppdeep_start, 1)

        size_a = round(os.path.getsize(file_a) / 1024, 1)
        size_b = round(os.path.getsize(file_b) / 1024, 1)

        tlsh_start = time.time()
        with open(file_a, 'rb') as fa, open(file_b, 'rb') as fb:
            tlsh_diff = tlsh.diff(tlsh.hash(fa.read()), tlsh.hash(fb.read()))
        tlsh_elapsed = round(time.time() - tlsh_start, 1)

        result_line = (
            f"{l1_dir}/{l2_dir0}/{filename};{l1_dir}/{l2_dir}/{filename};"
            f"{size_a};{size_b};{round(prog_score, 4)};{ppdeep_score};{tlsh_diff};"
            f"{prog_elapsed};{ppdeep_elapsed};{tlsh_elapsed}\n"
        )

        with _lock:
            output_handle.write(result_line)
            output_handle.flush()

    except Exception as exc:
        print(f"Error processing {file_a} and {file_b}: {exc}")
        with open(f"error_log{time.time()}.txt", "a") as f:
            f.write(f"Error analysing {file_a} and {file_b}: {exc}\n")


# ---------------------------------------------------------------------------
# Main sweep runner
# ---------------------------------------------------------------------------

def start_sweep(hash_type: str = 'ssdeep'):
    """Sweep all files under coreutils-polybench-hashcat subdirectories."""
    filenames = os.listdir('./coreutils-polybench-hashcat/aoc/Os/')
    filenames.remove('2mm')

    level1_dirs = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, ...

    timestamp = f"{datetime.datetime.now().hour}{datetime.datetime.now().minute}"
    output_path = f"./Debugging./dbg{timestamp}.txt"

    with open(output_path, mode="a") as out_f:
        out_f.write(
            "файл1;файл2;вес1;вес2;рез_программы;рез_ppdeep;рез_tlsh;"
            "время_сравн_прогр;время_сравн_ppdeep;время_сравн_tlsh\n"
        )
        out_f.flush()

        overall_start = time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                futures = []
                for filename in filenames:
                    for l1_dir in level1_dirs:
                        level2_dirs = os.listdir(f'./coreutils-polybench-hashcat/{l1_dir}')

                        for l2_dir in level2_dirs[1:]:
                            file_a = f'./coreutils-polybench-hashcat/{l1_dir}/{level2_dirs[0]}/{filename}'
                            file_b = f'./coreutils-polybench-hashcat/{l1_dir}/{l2_dir}/{filename}'

                            futures.append(
                                executor.submit(
                                    process_single_pair,
                                    file_a, file_b, filename,
                                    l1_dir, level2_dirs[0], l2_dir, out_f,
                                )
                            )

                for future in concurrent.futures.as_completed(futures):
                    future.result()

        except KeyboardInterrupt:
            print("UserInterrupt")
        finally:
            elapsed = time.time() - overall_start
            print(f"Total time: {round(elapsed, 1)} seconds")
            out_f.close()
            print("File closed")


if __name__ == '__main__':
    try:
        start_sweep()
    except KeyboardInterrupt:
        print("Keyboard interrupt")
