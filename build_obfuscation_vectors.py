"""
build_obfuscation_vectors.py

Построение 18-мерных векторов для каждой обфускации:
  1. Для каждой пары (program, obfuscation) собирается вектор V_i in R^18,
     где компоненты s_1 ... s_18 соответствуют уникальным конфигурациям:
     (hash_type, instructions_mode, compare_mode).
  2. Для каждой обфускации вычисляется усредненный вектор:
     V_obf = (1 / N) * sum(V_i) in R^18 по всем программам.

Конфигураций ровно 18:
  - ssdeep (5 режимов x 2 режима сравнения) = 10
  - nilsimsa (4 режима x 2 режима сравнения, без group_only) = 8
  Итого: 10 + 8 = 18 уникальных параметров.
"""

import os
import csv
import json
import argparse
from pathlib import Path
from collections import defaultdict


# Фиксированный порядок 18 уникальных конфигураций (s_1 ... s_18)
CONFIGS_18 = [
    # ---- ssdeep (10 конфигураций) ----
    ("ssdeep", "none", "custom"),         # s_1
    ("ssdeep", "none", "GPU"),            # s_2
    ("ssdeep", "generalize", "custom"),   # s_3
    ("ssdeep", "generalize", "GPU"),      # s_4
    ("ssdeep", "group", "custom"),        # s_5
    ("ssdeep", "group", "GPU"),           # s_6
    ("ssdeep", "both", "custom"),         # s_7
    ("ssdeep", "both", "GPU"),            # s_8
    ("ssdeep", "group_only", "custom"),   # s_9
    ("ssdeep", "group_only", "GPU"),      # s_10

    # ---- nilsimsa (8 конфигураций, без дублирующего group_only) ----
    ("nilsimsa", "none", "custom"),       # s_11
    ("nilsimsa", "none", "GPU"),          # s_12
    ("nilsimsa", "generalize", "custom"), # s_13
    ("nilsimsa", "generalize", "GPU"),    # s_14
    ("nilsimsa", "group", "custom"),      # s_15
    ("nilsimsa", "group", "GPU"),         # s_16
    ("nilsimsa", "both", "custom"),       # s_17
    ("nilsimsa", "both", "GPU"),          # s_18
]

# Читабельные имена параметров для колонок
CONFIG_NAMES = [f"{h}__{m}__{c}" for (h, m, c) in CONFIGS_18]


def load_log_data(log_path):
    """
    Загружает лог-файл (CSV с разделителем ';').
    Возвращает структуру:
      raw_data[obfuscation][program][config] = {'score': float, 'precision': float, 'recall': float}
    """
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Файл логов не найден: {log_path}")

    raw_data = defaultdict(lambda: defaultdict(dict))
    valid_configs = set(CONFIGS_18)
    total_rows = 0
    skipped_rows = 0

    with open(log_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            total_rows += 1
            if row.get("error"):
                skipped_rows += 1
                continue

            prog = row.get("program", "").strip()
            obf = row.get("obfuscation", "").strip()
            h_type = row.get("hash_type", "").strip()
            i_mode = row.get("instructions_mode", "").strip()
            c_mode = row.get("compare_mode", "").strip()

            cfg = (h_type, i_mode, c_mode)
            if cfg not in valid_configs:
                continue

            try:
                score = float(row.get("score", 0.0))
                precision = float(row.get("precision", 0.0))
                recall = float(row.get("recall", 0.0))
            except (ValueError, TypeError):
                skipped_rows += 1
                continue

            raw_data[obf][prog][cfg] = {
                "score": score,
                "precision": precision,
                "recall": recall
            }

    print(f"Загружено строк: {total_rows}, пропущено с ошибками: {skipped_rows}")
    print(f"Найдено уникальных обфускаций: {len(raw_data)}")
    return raw_data


def compute_vectors(raw_data, metric="score"):
    """
    Вычисляет:
      1. prog_vectors[obf][prog] -> list[float] размерности 18 (V_i in R^18)
      2. avg_vectors[obf] -> list[float] размерности 18 (V_obf in R^18)
      3. counts[obf] -> число программ, вошедших в усреднение
    """
    prog_vectors = defaultdict(dict)
    avg_vectors = {}
    counts = {}

    for obf, progs in sorted(raw_data.items()):
        obf_vectors = []
        for prog, cfgs in sorted(progs.items()):
            vec = []
            for cfg in CONFIGS_18:
                if cfg in cfgs:
                    vec.append(cfgs[cfg][metric])
                else:
                    vec.append(None)

            prog_vectors[obf][prog] = vec
            # Учитываем вектор, если в нем есть данные
            if any(val is not None for val in vec):
                obf_vectors.append(vec)

        counts[obf] = len(obf_vectors)

        # Покомпонентное усреднение по всем программам для данной обфускации
        avg_vec = []
        for dim_idx in range(len(CONFIGS_18)):
            vals = [v[dim_idx] for v in obf_vectors if v[dim_idx] is not None]
            if vals:
                avg_vec.append(round(sum(vals) / len(vals), 6))
            else:
                avg_vec.append(0.0)

        avg_vectors[obf] = avg_vec

    return avg_vectors, prog_vectors, counts


def save_vectors_to_csv(avg_vectors, counts, output_csv, metric="score"):
    """Сохраняет итоговую матрицу (N_obf x 18) в CSV."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        header = ["obfuscation", "programs_count"] + [f"s_{i+1} ({CONFIG_NAMES[i]})" for i in range(len(CONFIGS_18))]
        writer.writerow(header)

        for obf, vec in sorted(avg_vectors.items()):
            row = [obf, counts[obf]] + [f"{x:.6f}" for x in vec]
            writer.writerow(row)

    print(f"[{metric.upper()}] Векторы усредненных обфускаций сохранены в: {output_csv}")


def save_metadata_json(avg_vectors, prog_vectors, counts, output_json, metric="score"):
    """Сохраняет структуру в JSON с описанием базиса s_1 ... s_18."""
    os.makedirs(os.path.dirname(output_json), exist_ok=True)

    metadata = {
        "metric": metric,
        "dimension": len(CONFIGS_18),
        "basis_coordinates": {
            f"s_{i+1}": {
                "hash_type": cfg[0],
                "instructions_mode": cfg[1],
                "compare_mode": cfg[2],
                "name": CONFIG_NAMES[i]
            }
            for i, cfg in enumerate(CONFIGS_18)
        },
        "obfuscations_count": len(avg_vectors),
        "average_vectors_R18": avg_vectors,
        "programs_count_per_obfuscation": counts
    }

    with open(output_json, mode="w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[{metric.upper()}] Метаданные и векторы сохранены в: {output_json}")


def main():
    parser = argparse.ArgumentParser(description="Построение 18-мерных векторов обфускаций")
    parser.add_argument(
        "--log",
        default="results/logs/checkpoint_os.log",
        help="Путь к исходному checkpoint_os.log"
    )
    parser.add_argument(
        "--output-dir",
        default="results/vectors_r18",
        help="Папка для сохранения результирующих файлов"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.resolve()
    log_path = (project_root / args.log).resolve()
    out_dir = (project_root / args.output_dir).resolve()

    print("=" * 70)
    print("ПОСТРОЕНИЕ 18-МЕРНЫХ ВЕКТОРОВ ОБФУСКАЦИЙ V_obf in R^18")
    print(f"Лог-файл: {log_path}")
    print(f"Выходная папка: {out_dir}")
    print("=" * 70)

    raw_data = load_log_data(str(log_path))

    # Считаем для всех трех ключевых метрик: score (сходство), precision, recall
    for metric in ["score", "precision", "recall"]:
        avg_vectors, prog_vectors, counts = compute_vectors(raw_data, metric=metric)
        csv_path = out_dir / f"obfuscation_vectors_{metric}.csv"
        json_path = out_dir / f"obfuscation_vectors_{metric}.json"

        save_vectors_to_csv(avg_vectors, counts, str(csv_path), metric=metric)
        save_metadata_json(avg_vectors, prog_vectors, counts, str(json_path), metric=metric)

    # Выведем на экран пример для демонстрации
    sample_obf = "bcf" if "bcf" in avg_vectors else next(iter(avg_vectors))
    print("\n" + "=" * 70)
    print(f"ПРИМЕР ВЕКТОРА V_obf ДЛЯ '{sample_obf}' (score):")
    sample_vec = avg_vectors[sample_obf]
    for i, (val, name) in enumerate(zip(sample_vec, CONFIG_NAMES)):
        print(f"  s_{i+1:02d} ({name:<30}) = {val:.4f}")
    print(f"\nВсего обфускаций обработано: {len(avg_vectors)}")
    print(f"Размерность каждого вектора: {len(sample_vec)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
