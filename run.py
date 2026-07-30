"""
ResearchWorkCUDA — Binary Comparison Runner.

Entry point for single-pair and batch comparisons.
Usage:
    python run.py             # single pair (edit paths inside)
    python run_batch_final.py # batch with multiprocessing
"""

import datetime
import glob
import os
from pathlib import Path

import numpy as np
import torch

from src.batch import run, run_comparison, extract_features
from src.cfg import CfgAnalyzer
from src.core import AnalysisConfig, evaluate_matching
from src.core.similarity_engine import compute_program_similarity
from src.cfg import link_two_programs
from src.comparison.lancedb_cache import create_lancedb

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def set_seed(seed: int = 42):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


set_seed(42)


def clean_directory(dir_path: str):
    """Delete all files in *dir_path* (skips subdirectories)."""
    for file_path in glob.glob(os.path.join(dir_path, '*')):
        if os.path.isfile(file_path):
            os.remove(file_path)


# ---------------------------------------------------------------------------
# Main block
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    #create_lancedb()
    start_time = datetime.datetime.now()

    # ---- Quick single-pair comparison ----

    # config = AnalysisConfig(
    #     hash_type='ssdeep',
    #     instructions_mode='group_only',
    #     bin1_path=bin_a,
    #     bin2_path=bin_b,
    #     compare_mode='GPU',
    # )
    #
    # funcs_a, funcs_b, cg_a, cg_b = extract_features(Path(bin_a), Path(bin_b))
    # score, matched_a, matched_b = run_comparison(funcs_a, funcs_b, cg_a, cg_b, config)
    # eval_result = evaluate_matching(matched_a, matched_b, total_p1=len(funcs_a))

    # print(
    #     f"Custom: correct: {eval_result['correct']} "
    #     f"total_matched: {eval_result['total_matched']} "
    #     f"precision: {eval_result['precision']} "
    #     f"recall: {eval_result['recall']}"
    # )
    # print("Results:", round(score, 4))
    #
    # finish = datetime.datetime.now()
    # print(f'Elapsed: {finish - start_time}')

    # ---- Batch clear-vs-obfuscated sweep ----
    work_dir = Path(__file__).parent
    Files = [Path(work_dir, "coreutils-polybench-hashcat/aoc/Os/3mm"), Path(work_dir, "coreutils-polybench-hashcat/aoc/Os/combinatorX")]
    Files2 = ["basename"]
    clear_dir_path = work_dir / "coreutils-polybench-hashcat/aoc/Os/"
    obf_dir_path = work_dir / "OBF/coreutils-polybench-hashcat-obf/"

    results_path = work_dir / "Debug/results_generalize.txt"
    errors_path = work_dir / "Debug/error_generalize.txt"

    clear_files = os.listdir(clear_dir_path)
    obf_dirs = os.listdir(obf_dir_path)[:2]

    # Resume checkpoint: skip already-processed files
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            results_content = f.read()
        clear_files = list(filter(
            lambda x: f"filename: {x}" not in results_content, clear_files
        ))

    if len(clear_files) == 1:
        print("Нет файлов для сравнения")


    hash_types = ['ssdeep', 'nilsimsa']
    instructions_modes = ['none', 'generalize', 'group', 'group_only', 'both']
    compare_modes = ['GPU', 'custom']

    total_comparisons = len(hash_types) * len(instructions_modes) * len(compare_modes) * len(obf_dirs)
    print(f"total_comparisons: {total_comparisons}")
    k = 0
    with open(results_path, "a", encoding="utf-8") as out_f, \
         open(errors_path, "a", encoding="utf-8") as err_f:

        for filename in Files2:
            for obf_dir in obf_dirs:
                obf_bin_path = obf_dir_path / obf_dir

                if filename not in os.listdir(obf_bin_path):
                    print(f"файл {filename} не найден. Пропуск.")
                    continue

                clear_bin_path = clear_dir_path / filename
                obf_bin_path = obf_bin_path / filename

                try:
                    print(f"Extracting features for {filename}...")
                    funcs_a, funcs_b, cg_a, cg_b = extract_features(clear_bin_path, obf_bin_path)
                except Exception as exc:
                    print(f"Failed: {exc}")
                    err_f.write(f"Feature extraction error: {filename}: {exc}\n")
                    err_f.flush()
                    continue

                for hash_type in hash_types:
                    for instr_mode in instructions_modes:
                        for cmp_mode in compare_modes:
                            try:
                                cfg = AnalysisConfig(
                                    hash_type=hash_type,
                                    instructions_mode=instr_mode,
                                    compare_mode=cmp_mode,
                                    bin1_path=str(clear_bin_path),
                                    bin2_path=str(obf_bin_path),
                                )
                                print(f"[{k}/ {total_comparisons}] file:{filename}, obf:{obf_dir}, hash_type: {hash_type},  instr_mode:{instr_mode} cmp_mode: {cmp_mode}")

                                res, matched_a, matched_b = run_comparison(
                                    funcs_a, funcs_b, cg_a, cg_b, cfg,
                                )
                                eval_res = evaluate_matching(matched_a, matched_b, total_p1=len(funcs_a))
                                # print(
                                #     f"correct: {eval_res['correct']} "
                                #     f"total_matched: {eval_res['total_matched']} "
                                #     f"precision: {eval_res['precision']} "
                                #     f"recall: {eval_res['recall']}"
                                # )
                                # print(
                                #     f"=========> result: {res} h_type: {hash_type} "
                                #     f"// i_mode: {instr_mode} // c_mode: {cmp_mode} "
                                #     f"// filename: {filename}: {round(res, 4)} <========="
                                # )
                                k += 1
                                out_f.write(
                                    f"filename: {filename};result: {round(res, 4)};"
                                    f"obf_type: {obf_dir}"
                                    f"h_type: {hash_type};i_mode: {instr_mode};"
                                    f"c_mode: {cmp_mode};"
                                    f"correct:{eval_res['correct']};"
                                    f"total_matched: {eval_res['total_matched']};"
                                    f"precision: {eval_res['precision']};"
                                    f"recall: {eval_res['recall']}\n"
                                )
                                out_f.flush()
                            except Exception as exc:
                                print(
                                    f"=========> error: h_type: {hash_type} "
                                    f"// i_mode: {instr_mode} // c_mode: {cmp_mode} "
                                    f"// filename: {filename}: {exc} <========="
                                )
                                err_f.write(
                                    f"error: filename {filename};obf_type {obf_dir};" 
                                    f"h_type: {hash_type};i_mode: {instr_mode};"
                                    f"c_mode: {cmp_mode};filename: {filename}: {exc}\n"
                                )
                                err_f.flush()
    finish = datetime.datetime.now()
    print(f'Elapsed: {finish - start_time}')