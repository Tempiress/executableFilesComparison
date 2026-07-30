"""
Batch processing: parallel binary comparison with checkpoint support.

Key functions:
  - extract_features(p1_path, p2_path) -> functions, call_graphs
  - run_comparison(functions_a, functions_b, call_graph_a, call_graph_b, config) -> score, matched
  - process_file_pair(args) -> results  (worker entry point for multiprocessing)
"""

import argparse
import concurrent.futures
import csv
import datetime
import os
import signal
import sys
import threading
import time
from multiprocessing import Manager
from pathlib import Path

import torch

from src.cfg import CfgAnalyzer, link_two_programs
from src.core import AnalysisConfig, evaluate_matching
from src.core.similarity_engine import compute_program_similarity
from src.comparison.function_comparator import _gpu_compare_cache
from src.core.precomputed_func import PrecomputedFunc


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(binary_path_a: Path, binary_path_b: Path):
    """Extract CFGs and call graphs for two binaries."""
    cfg_analyzer = CfgAnalyzer()
    functions_a = cfg_analyzer.analyze_executable(str(binary_path_a))
    functions_b = cfg_analyzer.analyze_executable(str(binary_path_b))

    call_graph_a = cfg_analyzer.extract_call_graph(str(binary_path_a))
    call_graph_b = cfg_analyzer.extract_call_graph(str(binary_path_b))

    # Augment call graph with any functions missed by Radare2's agCj
    existing_names = {item["name"] for item in call_graph_a}
    for func_data in functions_a.values():
        name = func_data['cfg'][0]['name'] if func_data.get('cfg') and func_data['cfg'] else func_data.get('name', '')
        if name and name not in existing_names:
            call_graph_a.append({
                "name": name,
                "size": func_data['cfg'][0].get('size', 0) if func_data.get('cfg') else 0,
                "imports": {},
            })
            existing_names.add(name)

    existing_names = {item["name"] for item in call_graph_b}
    for func_data in functions_b.values():
        name = func_data['cfg'][0]['name'] if func_data.get('cfg') and func_data['cfg'] else func_data.get('name', '')
        if name and name not in existing_names:
            call_graph_b.append({
                "name": name,
                "size": func_data['cfg'][0].get('size', 0) if func_data.get('cfg') else 0,
                "imports": {},
            })
            existing_names.add(name)

    return functions_a, functions_b, call_graph_a, call_graph_b


# ---------------------------------------------------------------------------
# Comparison runner
# ---------------------------------------------------------------------------

def run_comparison(
    functions_a: dict,
    functions_b: dict,
    call_graph_a: list,
    call_graph_b: list,
    config: AnalysisConfig,
):
    """Run a full comparison between two programs.

    Returns:
        (score, matched_nodes_a, matched_nodes_b)
    """
    matrix_a, matrix_b, matched_a, matched_b = link_two_programs(
        functions_a, functions_b, call_graph_a, call_graph_b, config=config
    )

    if len(matrix_a) < len(matrix_b):
        score = compute_program_similarity(
            matrix_a, matrix_b,
            max(len(matrix_a), len(matrix_b)),
            functions_a, functions_b,
            config=config,
        )
    else:
        score = compute_program_similarity(
            matrix_b, matrix_a,
            max(len(matrix_a), len(matrix_b)),
            functions_b, functions_a,
            config=config,
        )

    return score, matched_a, matched_b


# ---------------------------------------------------------------------------
# Single run (convenience)
# ---------------------------------------------------------------------------

def run(binary_path_a: str, binary_path_b: str, config: AnalysisConfig = None):
    """Convenience: extract features and compare two binaries."""
    if config is None:
        config = AnalysisConfig()
    path_a, path_b = Path(binary_path_a), Path(binary_path_b)
    funcs_a, funcs_b, cg_a, cg_b = extract_features(path_a, path_b)
    return run_comparison(funcs_a, funcs_b, cg_a, cg_b, config)


# ---------------------------------------------------------------------------
# Batch worker
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    'timestamp', 'program', 'obfuscation', 'engine',
    'hash_type', 'instructions_mode', 'compare_mode',
    'score', 'precision', 'recall', 'correct', 'total_matched',
    'total_p1', 'total_p2', 'error',
]


def _get_processed_pairs(checkpoint_path: Path) -> set:
    """Read already-processed config tuples from checkpoint CSV."""
    processed = set()
    if not checkpoint_path.exists():
        return processed

    try:
        with open(checkpoint_path, "r", encoding="utf-8", newline="") as f:
            first_line = f.readline()
            if not first_line:
                return processed
            f.seek(0)
            delimiter = ";" if ";" in first_line else ","
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                program = row.get("program", "")
                obf = row.get("obfuscation", "")
                engine = row.get("engine", "")
                h_type = row.get("hash_type", "")
                i_mode = row.get("instructions_mode", "")
                c_mode = row.get("compare_mode", "")
                if program and obf and engine and h_type and i_mode and c_mode:
                    processed.add((program, obf, engine, h_type, i_mode, c_mode))
    except Exception:
        # Fallback: try old format
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "filename:" not in line:
                        continue
                    parts = line.strip().split("//")
                    if len(parts) >= 4:
                        filename = parts[0].replace("filename:", "").strip()
                        h_type = parts[1].replace("h_type:", "").strip()
                        i_mode = parts[2].replace("i_mode:", "").strip()
                        c_mode = parts[3].replace("c_mode:", "").strip()
                        processed.add((filename, "all_obf", "cfg_hash", h_type, i_mode, c_mode))
        except Exception:
            pass

    return processed


def process_file_pair_worker(args):
    """Worker: extract features once, then evaluate all config combos."""
    (
        path_a, path_b, configs_to_run,
        checkpoint_path, gpu_semaphore, write_lock,
        completed_counter, total_planned, task_completed_dict,
    ) = args

    # Clear caches at start of each pair
    PrecomputedFunc._cache.clear()
    _gpu_compare_cache.clear()

    program_name = Path(path_a).name
    obfuscation_name = Path(path_b).parent.name
    engine_name = "cfg_hash"

    # Feature extraction (Radare2 called exactly once)
    try:
        cfg_analyzer = CfgAnalyzer()
        functions_a, call_graph_a = cfg_analyzer.load_analyzers(str(path_a))
        functions_b, call_graph_b = cfg_analyzer.load_analyzers(str(path_b))
    except Exception as exc:
        error_msg = f"Feature extraction failed: {exc}"
        with write_lock:
            completed_counter.value += len(configs_to_run)
            is_empty = not os.path.exists(checkpoint_path) or os.path.getsize(checkpoint_path) == 0
            with open(checkpoint_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, delimiter=";")
                if is_empty:
                    writer.writeheader()
                for h_type, i_mode, c_mode in configs_to_run:
                    writer.writerow({
                        'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                        'program': program_name,
                        'obfuscation': obfuscation_name,
                        'engine': engine_name,
                        'hash_type': h_type,
                        'instructions_mode': i_mode,
                        'compare_mode': c_mode,
                        'error': error_msg,
                    })
                f.flush()
        return []

    # Run each config
    completed_keys = []
    for h_type, i_mode, c_mode in configs_to_run:
        try:
            config = AnalysisConfig(
                hash_type=h_type,
                instructions_mode=i_mode,
                compare_mode=c_mode,
                bin1_path=str(path_a),
                bin2_path=str(path_b),
            )

            if c_mode == 'GPU':
                with gpu_semaphore:
                    score, matched_a, matched_b = run_comparison(
                        functions_a, functions_b, call_graph_a, call_graph_b, config=config,
                    )
            else:
                score, matched_a, matched_b = run_comparison(
                    functions_a, functions_b, call_graph_a, call_graph_b, config=config,
                )

            eval_result = evaluate_matching(matched_a, matched_b, total_p1=len(functions_a))

            row = {
                'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                'program': program_name,
                'obfuscation': obfuscation_name,
                'engine': engine_name,
                'hash_type': h_type,
                'instructions_mode': i_mode,
                'compare_mode': c_mode,
                'score': round(float(score), 6),
                'precision': round(float(eval_result.get('precision', 0.0)), 4),
                'recall': round(float(eval_result.get('recall', 0.0)), 4),
                'correct': eval_result.get('correct', 0),
                'total_matched': eval_result.get('total_matched', 0),
                'total_p1': len(functions_a),
                'total_p2': len(functions_b),
                'error': '',
            }
        except Exception as exc:
            row = {
                'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                'program': program_name,
                'obfuscation': obfuscation_name,
                'engine': engine_name,
                'hash_type': h_type,
                'instructions_mode': i_mode,
                'compare_mode': c_mode,
                'error': str(exc),
            }

        with write_lock:
            completed_counter.value += 1
            curr = completed_counter.value
            is_empty = not os.path.exists(checkpoint_path) or os.path.getsize(checkpoint_path) == 0
            with open(checkpoint_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, delimiter=";")
                if is_empty:
                    writer.writeheader()
                writer.writerow(row)
                f.flush()

            if row.get('error'):
                print(f"[{curr}/{total_planned}] Error: {program_name} / {obfuscation_name} / {h_type} / {i_mode} / {c_mode}: {row.get('error')}")
            else:
                print(f"[{curr}/{total_planned}] {program_name} / {obfuscation_name} / {h_type} / {i_mode} / {c_mode}: {row.get('score')} (P: {row.get('precision')})")

        completed_keys.append((h_type, i_mode, c_mode))
        task_completed_dict[(program_name, obfuscation_name)] = completed_keys

    return completed_keys


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def main():
    try:
        import multiprocessing
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    parser = argparse.ArgumentParser(description='GPU-aware batch binary comparison')
    #parser.add_argument('--batch-size', type=int, default=2)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--log-file', type=str, default='./results/logs/resource_os.log')
    parser.add_argument('--checkpoint-file', type=str, default='./results/logs/checkpoint_os.log')
    parser.add_argument('--comparison-log', type=str, default='./results/logs/batch_results_os.log')
    parser.add_argument('--test', action='store_true', help='Run on small test set')

    args = parser.parse_args()
    print(args.checkpoint_file)

    # Ensure log dirs exist
    for d in [os.path.dirname(args.log_file), os.path.dirname(args.checkpoint_file)]:
        if d:
            os.makedirs(d, exist_ok=True)

    print(f"GPU available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}, count: {torch.cuda.device_count()}")

    hash_types = ['ssdeep', 'nilsimsa']
    instructions_modes = ['none', 'generalize', 'group', 'group_only', 'both']
    compare_modes = ['GPU', 'custom']

    # Build file pairs
    if args.test:
        pairs = [
            (Path("./coreutils-polybench-hashcat/aoc/Os/basename"),
             Path("./OBF/coreutils-polybench-hashcat-obf/bcf/basename")),
            (Path("./coreutils-polybench-hashcat/aoc/Os/combinatorX"),
             Path("./OBF/coreutils-polybench-hashcat-obf/bcf/combinatorX")),
        ]
    else:
        clear_dir = Path("./coreutils-polybench-hashcat/aoc/Os/")
        obf_base = Path("./OBF/coreutils-polybench-hashcat-obf/")

        if not obf_base.exists():
            print(f"Error: obfuscated dir {obf_base} does not exist")
            return

        obf_techs = [d.name for d in obf_base.iterdir() if d.is_dir() and d.name != "all"]
        clear_files = sorted(f for f in os.listdir(clear_dir) if (clear_dir / f).is_file())

        pairs = []
        for filename in clear_files:
            for tech in sorted(obf_techs):
                tech_dir = obf_base / tech
                if (tech_dir / filename).is_file():
                    pairs.append((clear_dir / filename, tech_dir / filename))

    print(f"Total pairs: {len(pairs)}")

    processed_set = _get_processed_pairs(Path(args.checkpoint_file))
    if processed_set:
        print(f"Skipping {len(processed_set)} already-processed configurations")

    start_time = time.time()

    shutdown_event = threading.Event()

    def _signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down immediately...")
        os._exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Group tasks
    tasks = []
    total_configs_planned = 0

    for path_a, path_b in pairs:
        pair_configs = []
        for h_type in hash_types:
            for i_mode in instructions_modes:
                for c_mode in compare_modes:
                    key = (path_a.name, path_b.parent.name, "cfg_hash", h_type, i_mode, c_mode)
                    if key in processed_set:
                        continue
                    pair_configs.append((h_type, i_mode, c_mode))
        if pair_configs:
            total_configs_planned += len(pair_configs)

    total_to_show = len(processed_set) + total_configs_planned

    manager = Manager()
    gpu_semaphore = manager.Semaphore(1)
    write_lock = manager.Lock()
    completed_counter = manager.Value('i', len(processed_set))
    task_completed_dict = manager.dict()

    for path_a, path_b in pairs:
        pair_configs = []
        for h_type in hash_types:
            for i_mode in instructions_modes:
                for c_mode in compare_modes:
                    key = (path_a.name, path_b.parent.name, "cfg_hash", h_type, i_mode, c_mode)
                    if key in processed_set:
                        continue
                    pair_configs.append((h_type, i_mode, c_mode))
        if pair_configs:
            tasks.append((
                path_a, path_b, pair_configs,
                args.checkpoint_file, gpu_semaphore, write_lock,
                completed_counter, total_to_show, task_completed_dict,
            ))

    print(f"Total configs to process: {total_configs_planned} (in {len(tasks)} tasks)")

    if not tasks:
        print("Nothing to process.")
        return

    ctx = multiprocessing.get_context('spawn')
    future_to_task = {}

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as executor:
        for task in tasks:
            if shutdown_event.is_set():
                break
            future = executor.submit(process_file_pair_worker, task)
            future_to_task[future] = task

        for future in concurrent.futures.as_completed(future_to_task):
            if shutdown_event.is_set():
                break
            task = future_to_task[future]
            path_a, path_b, _, _, _, _, _, _, _ = task[:9]

            try:
                future.result(timeout=300)
            except (concurrent.futures.TimeoutError, Exception) as exc:
                is_timeout = isinstance(exc, concurrent.futures.TimeoutError)
                err_msg = 'Timeout after 300 seconds' if is_timeout else f'Process crashed: {exc}'
                print(f"[Error] {err_msg} for {path_a.name} with {path_b.parent.name}")

                # Write errors for remaining configs
                completed_for_task = task_completed_dict.get((path_a.name, path_b.parent.name), [])
                completed_set = set(completed_for_task)
                with write_lock:
                    is_empty = not os.path.exists(args.checkpoint_file) or os.path.getsize(args.checkpoint_file) == 0
                    with open(args.checkpoint_file, "a", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, delimiter=";")
                        if is_empty:
                            writer.writeheader()
                        for h_type, i_mode, c_mode in task[2]:
                            if (h_type, i_mode, c_mode) not in completed_set:
                                completed_counter.value += 1
                                writer.writerow({
                                    'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                                    'program': path_a.name,
                                    'obfuscation': path_b.parent.name,
                                    'engine': 'cfg_hash',
                                    'hash_type': h_type,
                                    'instructions_mode': i_mode,
                                    'compare_mode': c_mode,
                                    'error': err_msg,
                                })
                        f.flush()

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.2f}s")


if __name__ == '__main__':
    main()
