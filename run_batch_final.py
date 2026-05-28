"""
GPU-aware multiprocessing wrapper with checkpoint support.
Processes file pairs in batches with proper GPU resource management.
"""

import concurrent.futures
import csv
import datetime
import os
import signal
import sys
import threading
import time
from multiprocessing import Manager, Semaphore
from pathlib import Path

import torch

sys.path.append(str(Path(__file__).parent.resolve()))

from batch_comparison_wrapper import get_num_gpus, gpu_wait, run_batch_comparison
from memory_cfg_from_exe_generator import CFGAnalyzer


def extract_features_for_pair(args):
    """Extract features for a single file pair."""
    p1_path, p2_path = args
    p1, p2 = str(p1_path), str(p2_path)
    
    cfg_analyzer = CFGAnalyzer()
    p1_funcs = cfg_analyzer.analyze_executable(p1)
    p2_funcs = cfg_analyzer.analyze_executable(p2)
    
    lks1 = cfg_analyzer.get_call_graph(p1)
    lks2 = cfg_analyzer.get_call_graph(p2)
    
    return p1_funcs, p2_funcs, lks1, lks2


def matrix_from_configs(lks1, lks2, p1_funcs, p2_funcs):
    """Generate incidence matrices from call graphs."""
    import numpy as np
    
    def incidence_matr_gen(lks, name_list):
        names = [item["name"] for item in lks]
        matr = np.zeros((len(names) + 1, len(names) + 1), dtype='object')
        matr[1:, 0] = names
        matr[0, 1:] = names
        
        for i, item in enumerate(lks):
            imports = set(item["imports"])
            for j, name in enumerate(names):
                if name != item["name"] and name in imports:
                    matr[i + 1, j + 1] = 1
        return matr
    
    matrix1 = incidence_matr_gen(lks1, [n for n in p1_funcs])
    matrix2 = incidence_matr_gen(lks2, [n for n in p2_funcs])
    
    return matrix1, matrix2


def get_processed_pairs(checkpoint_file):
    """Load already processed pairs from checkpoint file using csv.DictReader."""
    processed = set()
    checkpoint_path = Path(checkpoint_file)
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
    except Exception as e:
        # Fallback build of simple line parser in case the CSV is corrupted
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("timestamp"):
                        continue
                    parts = line.split(";") if ";" in line else line.split(",")
                    if len(parts) >= 7:
                        try:
                            # Skip very old format headers
                            if "filename:" in line:
                                continue
                            if len(parts) >= 10 and len(parts) <= 11 and "cfg_hash" not in line:
                                # Old semi-colon format
                                program = parts[0].strip()
                                h_type = parts[1].strip()
                                i_mode = parts[2].strip()
                                c_mode = parts[3].strip()
                                processed.add((program, "all_obf", "cfg_hash", h_type, i_mode, c_mode))
                            else:
                                # Standard columns matching pilot_results.csv
                                program = parts[1].strip()
                                obf = parts[2].strip()
                                engine = parts[3].strip()
                                h_type = parts[4].strip()
                                i_mode = parts[5].strip()
                                c_mode = parts[6].strip()
                                processed.add((program, obf, engine, h_type, i_mode, c_mode))
                        except Exception:
                            pass
        except Exception as fallback_e:
            print(f"[Warning] Failed to read checkpoint file: {fallback_e}")
    return processed


def get_config_combinations():
    """Generate all configuration combinations."""
    hash_types = ['ssdeep', 'nilsimsa']
    instructions_modes = ['none', 'generalize', 'group', 'group_only', 'both']
    compare_modes = ['GPU', 'custom']
    return hash_types, instructions_modes, compare_modes


def process_file_pair_comprehensive(args):
    """
    Process a file pair, extract features EXACTLY ONCE via Radare2,
    and evaluate all specified configuration combinations in memory.
    """
    p1_path, p2_path, configs_to_run, checkpoint_file = args
    
    program = Path(p1_path).name
    obfuscation = Path(p2_path).parent.name
    engine = "cfg_hash"
    
    results = []
    
    # 1. Feature Extraction (spawns Radare2 exactly once per pair)
    try:
        cfg_analyzer = CFGAnalyzer()
        p1_funcs = cfg_analyzer.analyze_executable(str(p1_path))
        p2_funcs = cfg_analyzer.analyze_executable(str(p2_path))
        lks1 = cfg_analyzer.get_call_graph(str(p1_path))
        lks2 = cfg_analyzer.get_call_graph(str(p2_path))
    except Exception as e:
        error_msg = f'Feature extraction failed: {e}'
        for h_type, i_mode, c_mode in configs_to_run:
            results.append({
                'program': program,
                'obfuscation': obfuscation,
                'engine': engine,
                'hash_type': h_type,
                'instructions_mode': i_mode,
                'compare_mode': c_mode,
                'score': '', 'precision': '', 'recall': '', 'correct': '', 'total_matched': '',
                'error': error_msg
            })
        return results
    
    from config import AnalysisConfig
    from run import run_with_features
    from similarity import evaluate_matching
    
    # 2. Run similarity comparisons in memory
    for h_type, i_mode, c_mode in configs_to_run:
        try:
            config = AnalysisConfig(
                hash_type=h_type,
                instructions_mode=i_mode,
                compare_mode=c_mode,
                bin1_path=str(p1_path),
                bin2_path=str(p2_path)
            )
            res, p1_nodes, p2_nodes = run_with_features(p1_funcs, p2_funcs, lks1, lks2, config=config)
            e_m = evaluate_matching(p1_nodes, p2_nodes)
            
            results.append({
                'program': program,
                'obfuscation': obfuscation,
                'engine': engine,
                'hash_type': h_type,
                'instructions_mode': i_mode,
                'compare_mode': c_mode,
                'score': round(float(res), 6),
                'precision': round(float(e_m.get('precision', 0.0)), 4),
                'recall': round(float(e_m.get('recall', 0.0)), 4),
                'correct': e_m.get('correct', 0),
                'total_matched': e_m.get('total_matched', 0),
                'error': ''
            })
        except Exception as e:
            results.append({
                'program': program,
                'obfuscation': obfuscation,
                'engine': engine,
                'hash_type': h_type,
                'instructions_mode': i_mode,
                'compare_mode': c_mode,
                'score': '', 'precision': '', 'recall': '', 'correct': '', 'total_matched': '',
                'error': str(e)
            })
            
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GPU-aware batch comparison with checkpoint')
    parser.add_argument('--batch-size', type=int, default=2, help='Batch size')
    parser.add_argument('--workers', type=int, default=2, help='Number of workers')
    parser.add_argument('--log-file', type=str, default='results/logs/resource.log', help='Resource log')
    parser.add_argument('--checkpoint-file', type=str, default='results/logs/checkpoint.log', help='Checkpoint file')
    parser.add_argument('--comparison-log', type=str, default='results/logs/batch_results.log', help='Results log')
    parser.add_argument('--test', action='store_true', help='Run on test set')
    
    args = parser.parse_args()
    
    log_dir = os.path.dirname(args.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    checkpoint_dir = os.path.dirname(args.checkpoint_file)
    if checkpoint_dir:
        if checkpoint_dir.exists() == False:
            os.makedirs(checkpoint_dir)
    
    print(f"GPU available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}, count: {get_num_gpus()}")
    
    hash_types, instructions_modes, compare_modes = get_config_combinations()
    
    if args.test:
        pairs = [
            (Path("./coreutils-polybench-hashcat/aoc/O0/3mm"), Path("./coreutils-polybench-hashcat/aoc/O2/3mm")),
            (Path("./coreutils-polybench-hashcat/aoc/O0/combinatorX"), Path("./coreutils-polybench-hashcat/aoc/O2/combinatorX")),
        ]
    else:
        clear_files_dir = Path("./coreutils-polybench-hashcat/aoc/O0/")
        obf_base_dir = Path("./OBF/coreutils-polybench-hashcat-obf/")
        
        if not obf_base_dir.exists():
            print(f"Error: Obfuscated files directory {obf_base_dir} does not exist.")
            return
            
        obf_techs = [d.name for d in obf_base_dir.iterdir() if d.is_dir() and d.name != "all"]
        clear_files = set(f for f in os.listdir(clear_files_dir) if (clear_files_dir / f).is_file())
        
        pairs = []
        for tech in sorted(obf_techs):
            tech_dir = obf_base_dir / tech
            for f in sorted(os.listdir(tech_dir)):
                if f in clear_files and (tech_dir / f).is_file():
                    pairs.append((clear_files_dir / f, tech_dir / f))
    
    print(f"Total pairs to process: {len(pairs)}")
    
    processed = get_processed_pairs(Path(args.checkpoint_file))
    processed_before = len(processed)
    if processed_before > 0:
        print(f"Skipping already processed configurations (found {processed_before} in checkpoint)")
    
    start_time = time.time()
    
    shutdown_event = threading.Event()
    
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        shutdown_event.set()
        print("Waiting for workers to finish...")
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Group configurations by file pair
    tasks_to_submit = []
    total_configs_planned = 0
    
    for p1, p2 in pairs:
        program = p1.name
        obfuscation = p2.parent.name
        engine = "cfg_hash"
        
        pair_configs_to_run = []
        for h_type in hash_types:
            for i_mode in instructions_modes:
                for c_mode in compare_modes:
                    pair_key = (program, obfuscation, engine, h_type, i_mode, c_mode)
                    if pair_key in processed:
                        continue
                    pair_configs_to_run.append((h_type, i_mode, c_mode))
        
        if pair_configs_to_run:
            total_configs_planned += len(pair_configs_to_run)
            tasks_to_submit.append((p1, p2, pair_configs_to_run, args.checkpoint_file))
            
    print(f"Total configurations to process: {total_configs_planned} (grouped into {len(tasks_to_submit)} tasks)")
    
    if not tasks_to_submit:
        print("No new configurations to process. Batch completed.")
        return
        
    CSV_FIELDS = [
        'timestamp', 'program', 'obfuscation', 'engine',
        'hash_type', 'instructions_mode', 'compare_mode',
        'score', 'precision', 'recall', 'correct', 'total_matched', 'error'
    ]
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for task in tasks_to_submit:
            if shutdown_event.is_set():
                print("Shutdown requested, stopping...")
                break
            future = executor.submit(process_file_pair_comprehensive, task)
            futures.append(future)
        
        completed_configs = 0
        for future in concurrent.futures.as_completed(futures):
            if shutdown_event.is_set():
                break
            results = future.result()
            
            # Semicolon CSV Writing
            is_empty = not os.path.exists(args.checkpoint_file) or os.path.getsize(args.checkpoint_file) == 0
            with open(args.checkpoint_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, delimiter=";")
                if is_empty:
                    writer.writeheader()
                
                for result in results:
                    completed_configs += 1
                    
                    if result.get('error'):
                        print(f"[{completed_configs}/{total_configs_planned}] Error: {result.get('program')} / {result.get('obfuscation')} / {result.get('hash_type')}: {result.get('error')}")
                    else:
                        score_str = result.get('score', '')
                        p_str = result.get('precision', '')
                        print(f"[{completed_configs}/{total_configs_planned}] {result.get('program')} / {result.get('obfuscation')} / {result.get('hash_type')} / {result.get('instructions_mode')} / {result.get('compare_mode')}: {score_str} (P: {p_str})")
                    
                    row = {
                        'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                        'program': result.get('program', ''),
                        'obfuscation': result.get('obfuscation', ''),
                        'engine': result.get('engine', ''),
                        'hash_type': result.get('hash_type', ''),
                        'instructions_mode': result.get('instructions_mode', ''),
                        'compare_mode': result.get('compare_mode', ''),
                        'score': result.get('score', ''),
                        'precision': result.get('precision', ''),
                        'recall': result.get('recall', ''),
                        'correct': result.get('correct', ''),
                        'total_matched': result.get('total_matched', ''),
                        'error': result.get('error', '')
                    }
                    writer.writerow(row)
                f.flush()
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.2f}s")


if __name__ == '__main__':
    main()