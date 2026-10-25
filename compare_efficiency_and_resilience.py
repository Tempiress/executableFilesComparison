"""
Compare Obfuscation Potency (Efficiency) vs Obfuscation Resilience.

Loads:
  - Obfuscation vectors (P_orig <-> P_obf) from results/vectors_r18/
  - Deobfuscation vectors (P_orig <-> P_deobf) from results/vectors_deo_r18/
(or directly from checkpoints: checkpoint_os.log and checkpoint_deo.log).

Calculates side-by-side metrics:
  - Potency similarity:   S_obf (lower = more potent)
  - Deobf similarity:     S_deo (lower = more resilient against deobfuscator)
  - Delta:                Delta S = S_deo - S_obf
  - Recovery Rate:        (S_deo - S_obf) / (1.0 - S_obf)
  - Resilience Index:     1.0 - S_deo

Outputs:
  - results/comparison_efficiency_vs_resilience.csv
  - results/comparison_efficiency_vs_resilience.json
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)


def load_vectors_csv(csv_path: Path):
    """Loads obfuscation vectors CSV and returns dict: {obf: {config_col: float_val}} and mean_18."""
    if not csv_path.exists():
        return {}
    data = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = ';' if ';' in first_line else ','
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            obf = row.get('obfuscation')
            if not obf:
                continue
            vals = {}
            for col, val in row.items():
                if col in ('obfuscation', 'programs_count', 'mean_18'):
                    continue
                try:
                    vals[col] = float(val)
                except (ValueError, TypeError):
                    pass
            mean_val = float(row['mean_18']) if 'mean_18' in row else (sum(vals.values()) / len(vals) if vals else 0.0)
            data[obf] = {
                'vector': vals,
                'mean_18': mean_val,
                'programs_count': int(row.get('programs_count', 0))
            }
    return data


def compare_studies(
    obf_csv: Path,
    deo_csv: Path,
    out_csv: Path,
    out_json: Path,
    metric_name: str = 'score'
):
    data_obf = load_vectors_csv(obf_csv)
    data_deo = load_vectors_csv(deo_csv)

    if not data_obf:
        print(f"[WARN] Obfuscation vector file not found: {obf_csv}")
    if not data_deo:
        print(f"[WARN] Deobfuscation vector file not found: {deo_csv}")

    common_obfs = sorted(set(data_obf.keys()) & set(data_deo.keys()))
    if not common_obfs:
        # Fallback to any available in deo
        common_obfs = sorted(data_deo.keys())

    comparisons = []
    for obf in common_obfs:
        s_obf = data_obf.get(obf, {}).get('mean_18', 0.0)
        s_deo = data_deo.get(obf, {}).get('mean_18', 0.0)
        cnt_obf = data_obf.get(obf, {}).get('programs_count', 0)
        cnt_deo = data_deo.get(obf, {}).get('programs_count', 0)

        delta_s = s_deo - s_obf
        denom = (1.0 - s_obf)
        recovery_rate = (delta_s / denom) if abs(denom) > 1e-6 else 0.0
        resilience = max(0.0, 1.0 - s_deo)

        comparisons.append({
            'obfuscation': obf,
            'mean_potency_score': round(s_obf, 6),
            'mean_deobf_score': round(s_deo, 6),
            'delta_score': round(delta_s, 6),
            'recovery_rate': round(recovery_rate, 4),
            'resilience_index': round(resilience, 4),
            'obf_programs_count': cnt_obf,
            'deo_programs_count': cnt_deo,
        })

    # Sort by resilience (highest first)
    comparisons.sort(key=lambda x: x['resilience_index'], reverse=True)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        fields = [
            'obfuscation',
            'mean_potency_score',
            'mean_deobf_score',
            'delta_score',
            'recovery_rate',
            'resilience_index',
            'obf_programs_count',
            'deo_programs_count'
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(comparisons)

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(comparisons, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 110)
    print(f" COMPARATIVE ANALYSIS: POTENCY vs RESILIENCE ({metric_name.upper()}) ")
    print("=" * 110)
    print(f"{'Obfuscation':<16} | {'S_obf (Potency)':<15} | {'S_deo (Deobf)':<15} | {'Delta S':<10} | {'Recov %':<10} | {'Resilience':<12}")
    print("-" * 110)
    for row in comparisons:
        print(f"{row['obfuscation']:<16} | {row['mean_potency_score']:<15.4f} | {row['mean_deobf_score']:<15.4f} | {row['delta_score']:<+10.4f} | {row['recovery_rate']*100:<9.2f}% | {row['resilience_index']:<12.4f}")
    print("=" * 110)
    print(f"Saved CSV:  {out_csv}")
    print(f"Saved JSON: {out_json}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Compare Obfuscation Potency and Resilience")
    parser.add_argument('--obf-csv', default='results/vectors_r18/obfuscation_vectors_score.csv', help='Obfuscation vectors CSV')
    parser.add_argument('--deo-csv', default='results/vectors_deo_r18/obfuscation_vectors_score.csv', help='Deobfuscation vectors CSV')
    parser.add_argument('--out-csv', default='results/comparison_potency_vs_resilience.csv', help='Output comparative CSV')
    parser.add_argument('--out-json', default='results/comparison_potency_vs_resilience.json', help='Output comparative JSON')
    parser.add_argument('--metric', default='score', choices=['score', 'precision', 'recall'])
    args = parser.parse_args()

    compare_studies(
        obf_csv=PROJECT_ROOT / args.obf_csv,
        deo_csv=PROJECT_ROOT / args.deo_csv,
        out_csv=PROJECT_ROOT / args.out_csv,
        out_json=PROJECT_ROOT / args.out_json,
        metric_name=args.metric
    )
