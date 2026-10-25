"""
Pilot Test Runner for Evaluating Obfuscation Resilience (Стойкость к деобфускации).

Compares:
  1. Clean vs Obfuscated    (P_orig <-> P_obf)   -> Obfuscation Potency
  2. Clean vs Deobfuscated  (P_orig <-> P_deobf) -> Recovery / Resilience
  3. Obfuscated vs Deobf    (P_obf  <-> P_deobf) -> Transformation degree

Outputs detailed 18-dimensional vectors and summary recovery metrics.
"""

import argparse
import csv
import datetime
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 18-parameter basis configuration
HASH_TYPES = ['ssdeep', 'nilsimsa']
INSTRUCTION_MODES = ['none', 'generalize', 'group', 'both', 'group_only']
COMPARE_MODES = ['custom', 'GPU']

CSV_FIELDS = [
    'timestamp',
    'pair_type',     # clean_vs_obf, clean_vs_deobf, obf_vs_deobf
    'program',
    'obfuscation',
    'engine',
    'hash_type',
    'instructions_mode',
    'compare_mode',
    'score',
    'precision',
    'recall',
    'correct',
    'total_matched',
    'total_p1',
    'total_p2',
    'error',
]


def get_18_configurations():
    """Returns the ordered list of 18 (hash_type, instruction_mode, compare_mode) tuples."""
    configs = []
    for h_type in HASH_TYPES:
        for i_mode in INSTRUCTION_MODES:
            if i_mode == 'group_only' and h_type != 'ssdeep':
                continue
            for c_mode in COMPARE_MODES:
                configs.append((h_type, i_mode, c_mode))
    return configs


def evaluate_pair(analyzer, path_a: Path, path_b: Path, configs, pair_type: str, program_name: str, obf_name: str, csv_writer=None, csv_file=None):
    """Evaluates all 18 configurations for a given pair of binaries."""
    from src.batch import run_comparison
    from src.core import AnalysisConfig, evaluate_matching
    from src.core.precomputed_func import PrecomputedFunc
    from src.comparison.function_comparator import _gpu_compare_cache

    PrecomputedFunc._cache.clear()
    _gpu_compare_cache.clear()

    results = {}
    try:
        funcs_a, cg_a = analyzer.load_analyzers(str(path_a))
        funcs_b, cg_b = analyzer.load_analyzers(str(path_b))
    except Exception as exc:
        err = f"Feature extraction failed: {exc}"
        for h_type, i_mode, c_mode in configs:
            col_key = f"{h_type}_{i_mode}_{c_mode}"
            results[col_key] = {'score': 0.0, 'precision': 0.0, 'recall': 0.0, 'error': err}
            if csv_writer:
                csv_writer.writerow({
                    'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                    'pair_type': pair_type,
                    'program': program_name,
                    'obfuscation': obf_name,
                    'engine': 'cfg_hash',
                    'hash_type': h_type,
                    'instructions_mode': i_mode,
                    'compare_mode': c_mode,
                    'error': err,
                })
                if csv_file:
                    csv_file.flush()
        return results

    for h_type, i_mode, c_mode in configs:
        col_key = f"{h_type}_{i_mode}_{c_mode}"
        try:
            cfg = AnalysisConfig(
                hash_type=h_type,
                instructions_mode=i_mode,
                compare_mode=c_mode,
                bin1_path=str(path_a),
                bin2_path=str(path_b),
            )
            score, matched_a, matched_b = run_comparison(funcs_a, funcs_b, cg_a, cg_b, config=cfg)
            eval_res = evaluate_matching(matched_a, matched_b, total_p1=len(funcs_a))
            row_data = {
                'score': float(score),
                'precision': float(eval_res.get('precision', 0.0)),
                'recall': float(eval_res.get('recall', 0.0)),
                'correct': int(eval_res.get('correct', 0)),
                'total_matched': int(eval_res.get('total_matched', 0)),
                'total_p1': len(funcs_a),
                'total_p2': len(funcs_b),
                'error': '',
            }
        except Exception as exc:
            row_data = {
                'score': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'correct': 0,
                'total_matched': 0,
                'total_p1': len(funcs_a),
                'total_p2': len(funcs_b),
                'error': str(exc),
            }

        results[col_key] = row_data

        if csv_writer:
            csv_writer.writerow({
                'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                'pair_type': pair_type,
                'program': program_name,
                'obfuscation': obf_name,
                'engine': 'cfg_hash',
                'hash_type': h_type,
                'instructions_mode': i_mode,
                'compare_mode': c_mode,
                'score': round(row_data['score'], 6),
                'precision': round(row_data['precision'], 4),
                'recall': round(row_data['recall'], 4),
                'correct': row_data.get('correct', 0),
                'total_matched': row_data.get('total_matched', 0),
                'total_p1': row_data.get('total_p1', 0),
                'total_p2': row_data.get('total_p2', 0),
                'error': row_data['error'],
            })
            if csv_file:
                csv_file.flush()

    return results


def run_pilot_resilience_test(
    programs=('2mm', 'atax'),
    obfuscations=('bcf', 'cff', 'bcf-cff'),
    output_log='results/logs/checkpoint_deobf_test.log',
    summary_json='results/deobf_resilience_test_summary.json'
):
    import torch
    from src.cfg import CfgAnalyzer

    print("=" * 80)
    print(" PILOT TEST: EVALUATION OF OBFUSCATION RESILIENCE & RECOVERY ")
    print("=" * 80)
    print(f"Project root:     {PROJECT_ROOT}")
    print(f"Test programs:    {list(programs)}")
    print(f"Test obfuscations:{list(obfuscations)}")
    print(f"GPU available:    {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU device:       {torch.cuda.get_device_name(0)}")

    clean_dir = PROJECT_ROOT / "coreutils-polybench-hashcat" / "aoc" / "Os"
    obf_dir = PROJECT_ROOT / "OBF" / "coreutils-polybench-hashcat-obf"
    deo_dir = PROJECT_ROOT / "OBF" / "polybench-hashcat-deo"

    if not clean_dir.exists():
        raise FileNotFoundError(f"Clean dir not found: {clean_dir}")
    if not obf_dir.exists():
        raise FileNotFoundError(f"Obfuscated dir not found: {obf_dir}")
    if not deo_dir.exists():
        raise FileNotFoundError(f"Deobfuscated dir not found: {deo_dir}")

    configs = get_18_configurations()
    print(f"Evaluating {len(configs)} configuration dimensions per pair...")

    log_path = PROJECT_ROOT / output_log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = PROJECT_ROOT / summary_json
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    is_new_csv = not log_path.exists() or log_path.stat().st_size == 0
    csv_file = open(log_path, "a", encoding="utf-8", newline="")
    csv_writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS, delimiter=";")
    if is_new_csv:
        csv_writer.writeheader()
        csv_file.flush()

    analyzer = CfgAnalyzer()
    pilot_summary = []

    start_total = time.time()

    for prog in programs:
        p_clean = clean_dir / prog
        if not p_clean.exists():
            print(f"[WARN] Clean binary not found: {p_clean}, skipping...")
            continue

        for obf in obfuscations:
            p_obf = obf_dir / obf / prog
            p_deo = deo_dir / obf / prog

            if not p_obf.exists():
                print(f"[WARN] Obfuscated binary not found: {p_obf}, skipping...")
                continue
            if not p_deo.exists():
                print(f"[WARN] Deobfuscated binary not found: {p_deo}, skipping...")
                continue

            print("\n" + "-" * 80)
            print(f">>> Program: {prog} | Obfuscation: {obf}")
            print(f"    Clean:  {p_clean} (size: {p_clean.stat().st_size} B)")
            print(f"    Obf:    {p_obf} (size: {p_obf.stat().st_size} B)")
            print(f"    Deo:    {p_deo} (size: {p_deo.stat().st_size} B)")

            t0 = time.time()
            # 1. Clean vs Obfuscated
            print(f"    [1/3] Comparing Clean <-> Obfuscated (Potency)...")
            res_clean_obf = evaluate_pair(analyzer, p_clean, p_obf, configs, 'clean_vs_obf', prog, obf, csv_writer, csv_file)

            # 2. Clean vs Deobfuscated
            print(f"    [2/3] Comparing Clean <-> Deobfuscated (Resilience)...")
            res_clean_deo = evaluate_pair(analyzer, p_clean, p_deo, configs, 'clean_vs_deobf', prog, obf, csv_writer, csv_file)

            # 3. Obfuscated vs Deobfuscated
            print(f"    [3/3] Comparing Obfuscated <-> Deobfuscated (Transformation)...")
            res_obf_deo = evaluate_pair(analyzer, p_obf, p_deo, configs, 'obf_vs_deobf', prog, obf, csv_writer, csv_file)

            dt = time.time() - t0

            # Compute 18-dim mean values
            scores_clean_obf = [v['score'] for v in res_clean_obf.values() if not v['error']]
            scores_clean_deo = [v['score'] for v in res_clean_deo.values() if not v['error']]
            scores_obf_deo = [v['score'] for v in res_obf_deo.values() if not v['error']]

            mean_s_obf = sum(scores_clean_obf) / len(scores_clean_obf) if scores_clean_obf else 0.0
            mean_s_deo = sum(scores_clean_deo) / len(scores_clean_deo) if scores_clean_deo else 0.0
            mean_s_trans = sum(scores_obf_deo) / len(scores_obf_deo) if scores_obf_deo else 0.0

            prec_clean_obf = [v['precision'] for v in res_clean_obf.values() if not v['error']]
            prec_clean_deo = [v['precision'] for v in res_clean_deo.values() if not v['error']]
            mean_p_obf = sum(prec_clean_obf) / len(prec_clean_obf) if prec_clean_obf else 0.0
            mean_p_deo = sum(prec_clean_deo) / len(prec_clean_deo) if prec_clean_deo else 0.0

            delta_s = mean_s_deo - mean_s_obf
            delta_p = mean_p_deo - mean_p_obf
            # Recovery rate: portion of similarity recovered back towards 1.0
            recovery_rate = (delta_s / (1.0 - mean_s_obf)) if (1.0 - mean_s_obf) > 1e-6 else 0.0
            # Resilience index: how far it still is from clean (higher = more resilient)
            resilience_index = max(0.0, 1.0 - mean_s_deo)

            print(f"    --> S(Clean, Obf):   {mean_s_obf:.4f} (Prec: {mean_p_obf:.4f})")
            print(f"    --> S(Clean, Deo):   {mean_s_deo:.4f} (Prec: {mean_p_deo:.4f})")
            print(f"    --> S(Obf, Deo):     {mean_s_trans:.4f}")
            print(f"    --> Delta S:         {delta_s:+.4f} (Recovery Rate: {recovery_rate * 100:.2f}%)")
            print(f"    --> Resilience Idx:  {resilience_index:.4f} (Elapsed: {dt:.1f}s)")

            pilot_summary.append({
                'program': prog,
                'obfuscation': obf,
                'clean_size': p_clean.stat().st_size,
                'obf_size': p_obf.stat().st_size,
                'deo_size': p_deo.stat().st_size,
                'mean_score_clean_obf': round(mean_s_obf, 6),
                'mean_score_clean_deo': round(mean_s_deo, 6),
                'mean_score_obf_deo': round(mean_s_trans, 6),
                'mean_prec_clean_obf': round(mean_p_obf, 4),
                'mean_prec_clean_deo': round(mean_p_deo, 4),
                'delta_score': round(delta_s, 6),
                'delta_precision': round(delta_p, 4),
                'recovery_rate': round(recovery_rate, 4),
                'resilience_index': round(resilience_index, 4),
                'vector_clean_obf': {k: v['score'] for k, v in res_clean_obf.items()},
                'vector_clean_deo': {k: v['score'] for k, v in res_clean_deo.items()},
                'vector_obf_deo': {k: v['score'] for k, v in res_obf_deo.items()},
            })

    csv_file.close()

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(" TEST COMPLETED ")
    print("=" * 80)
    print(f"Total elapsed: {total_time:.2f}s")
    print(f"Detailed checkpoint log saved to: {log_path}")

    # Merge with existing summary JSON if present
    existing_entries = {}
    if summary_path.exists():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for item in old_data:
                    existing_entries[(item['program'], item['obfuscation'])] = item
        except Exception:
            pass
    for item in pilot_summary:
        existing_entries[(item['program'], item['obfuscation'])] = item

    final_summary = list(existing_entries.values())
    final_summary.sort(key=lambda x: (x['program'], -x['resilience_index']))

    # Write summary JSON
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)
    print(f"Summary JSON saved to:             {summary_path} ({len(final_summary)} total entries)")

    # Print summary table
    print("\n" + "=" * 105)
    print(f"{'Program':<10} | {'Obfuscation':<12} | {'S(Clean,Obf)':<13} | {'S(Clean,Deo)':<13} | {'Delta S':<10} | {'Recov %':<9} | {'Resilience':<10}")
    print("-" * 105)
    for item in final_summary:
        print(f"{item['program']:<10} | {item['obfuscation']:<12} | {item['mean_score_clean_obf']:<13.4f} | {item['mean_score_clean_deo']:<13.4f} | {item['delta_score']:<+10.4f} | {item['recovery_rate']*100:<8.2f}% | {item['resilience_index']:<10.4f}")
    print("=" * 105)

    return final_summary


def aggregate_from_log(log_path: Path, summary_path: Path):
    """Aggregates all results from a checkpoint log into a structured summary."""
    from collections import defaultdict
    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        return []

    data = defaultdict(lambda: defaultdict(dict))
    with open(log_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row.get('error'):
                continue
            p = row['program']
            o = row['obfuscation']
            pt = row['pair_type']
            cfg_key = f"{row['hash_type']}_{row['instructions_mode']}_{row['compare_mode']}"
            s = float(row['score'])
            pr = float(row.get('precision', 0.0))
            re = float(row.get('recall', 0.0))
            data[(p, o)][pt][cfg_key] = {'score': s, 'precision': pr, 'recall': re}

    summary = []
    for (p, o), pairs in data.items():
        clean_obf = pairs.get('clean_vs_obf', {})
        clean_deo = pairs.get('clean_vs_deobf', {})
        obf_deo = pairs.get('obf_vs_deobf', {})

        s_obf = [v['score'] for v in clean_obf.values()]
        s_deo = [v['score'] for v in clean_deo.values()]
        s_trans = [v['score'] for v in obf_deo.values()]
        p_obf = [v['precision'] for v in clean_obf.values()]
        p_deo = [v['precision'] for v in clean_deo.values()]

        mean_s_obf = sum(s_obf) / len(s_obf) if s_obf else 0.0
        mean_s_deo = sum(s_deo) / len(s_deo) if s_deo else 0.0
        mean_s_trans = sum(s_trans) / len(s_trans) if s_trans else 0.0
        mean_p_obf = sum(p_obf) / len(p_obf) if p_obf else 0.0
        mean_p_deo = sum(p_deo) / len(p_deo) if p_deo else 0.0

        delta_s = mean_s_deo - mean_s_obf
        delta_p = mean_p_deo - mean_p_obf
        recov = (delta_s / (1.0 - mean_s_obf)) if (1.0 - mean_s_obf) > 1e-6 else 0.0
        resil = max(0.0, 1.0 - mean_s_deo)

        summary.append({
            'program': p,
            'obfuscation': o,
            'mean_score_clean_obf': round(mean_s_obf, 6),
            'mean_score_clean_deo': round(mean_s_deo, 6),
            'mean_score_obf_deo': round(mean_s_trans, 6),
            'mean_prec_clean_obf': round(mean_p_obf, 4),
            'mean_prec_clean_deo': round(mean_p_deo, 4),
            'delta_score': round(delta_s, 6),
            'delta_precision': round(delta_p, 4),
            'recovery_rate': round(recov, 4),
            'resilience_index': round(resil, 4),
            'configs_count': len(clean_obf),
            'vector_clean_obf': {k: v['score'] for k, v in clean_obf.items()},
            'vector_clean_deo': {k: v['score'] for k, v in clean_deo.items()},
            'vector_obf_deo': {k: v['score'] for k, v in obf_deo.items()},
        })

    summary.sort(key=lambda x: (x['program'], -x['resilience_index']))

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 105)
    print(f"{'Program':<10} | {'Obfuscation':<12} | {'S(Clean,Obf)':<13} | {'S(Clean,Deo)':<13} | {'Delta S':<10} | {'Recov %':<9} | {'Resilience':<10}")
    print("-" * 105)
    for item in summary:
        print(f"{item['program']:<10} | {item['obfuscation']:<12} | {item['mean_score_clean_obf']:<13.4f} | {item['mean_score_clean_deo']:<13.4f} | {item['delta_score']:<+10.4f} | {item['recovery_rate']*100:<8.2f}% | {item['resilience_index']:<10.4f}")
    print("=" * 105)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pilot Test for Obfuscation Resilience")
    parser.add_argument('--programs', nargs='+', default=['2mm', 'atax'], help="List of programs to test")
    parser.add_argument('--obfuscations', nargs='+', default=['bcf', 'cff', 'bcf-cff'], help="List of obfuscations to test")
    parser.add_argument('--log', default='results/logs/checkpoint_deobf_test.log', help="CSV checkpoint log path")
    parser.add_argument('--summary', default='results/deobf_resilience_test_summary.json', help="Summary JSON output")
    parser.add_argument('--aggregate-only', action='store_true', help="Only aggregate existing log file into summary")
    args = parser.parse_args()

    if args.aggregate_only:
        aggregate_from_log(PROJECT_ROOT / args.log, PROJECT_ROOT / args.summary)
    else:
        run_pilot_resilience_test(
            programs=args.programs,
            obfuscations=args.obfuscations,
            output_log=args.log,
            summary_json=args.summary
        )
