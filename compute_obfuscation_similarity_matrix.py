"""
compute_obfuscation_similarity_matrix.py

Вычисление матрицы сходства и расстояний между обфускациями в пространстве R^18:
  1. Косинусное сходство (Cosine Similarity in [0, 1]):
     cos(u, v) = (u . v) / (||u|| * ||v||)
  2. Евклидово расстояние (Euclidean Distance >= 0):
     d(u, v) = ||u - v|| = sqrt(sum((u_i - v_i)^2))

На вход подаются 18-мерные векторы обфускаций V_obf (по умолчанию из obfuscation_vectors_score.json).
На выходе формируются матрицы 63 x 63 (CSV и JSON) и выявляются наиболее схожие и различные техники.
"""

import os
import csv
import json
import math
import argparse
from pathlib import Path


def dot_product(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))


def norm_l2(v):
    return math.sqrt(sum(a * a for a in v))


def cosine_similarity(v1, v2):
    n1, n2 = norm_l2(v1), norm_l2(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    val = dot_product(v1, v2) / (n1 * n2)
    # Защита от погрешностей округления с плавающей точкой
    return max(0.0, min(1.0, val))


def euclidean_distance(v1, v2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


def load_vectors(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Файл векторов не найден: {json_path}")

    with open(json_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    vectors = data.get("average_vectors_R18", {})
    metric = data.get("metric", "score")
    dim = data.get("dimension", 18)
    return vectors, metric, dim


def build_matrices(vectors):
    obf_names = sorted(vectors.keys())
    n = len(obf_names)

    cosine_matrix = [[0.0] * n for _ in range(n)]
    euclidean_matrix = [[0.0] * n for _ in range(n)]

    pairs_similarity = []

    for i in range(n):
        name_i = obf_names[i]
        vec_i = vectors[name_i]

        cosine_matrix[i][i] = 1.0
        euclidean_matrix[i][i] = 0.0

        for j in range(i + 1, n):
            name_j = obf_names[j]
            vec_j = vectors[name_j]

            cos_sim = cosine_similarity(vec_i, vec_j)
            euc_dist = euclidean_distance(vec_i, vec_j)

            cosine_matrix[i][j] = cos_sim
            cosine_matrix[j][i] = cos_sim

            euclidean_matrix[i][j] = euc_dist
            euclidean_matrix[j][i] = euc_dist

            pairs_similarity.append((cos_sim, euc_dist, name_i, name_j))

    return obf_names, cosine_matrix, euclidean_matrix, pairs_similarity


def save_matrix_to_csv(obf_names, matrix, output_csv, format_str="{:.6f}"):
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["obfuscation"] + obf_names)
        for name, row in zip(obf_names, matrix):
            writer.writerow([name] + [format_str.format(x) for x in row])


def save_json_results(obf_names, cosine_matrix, euclidean_matrix, metric, output_json):
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    payload = {
        "metric": metric,
        "obfuscations_count": len(obf_names),
        "obfuscations": obf_names,
        "cosine_similarity_matrix": {
            obf_names[i]: {obf_names[j]: round(cosine_matrix[i][j], 6) for j in range(len(obf_names))}
            for i in range(len(obf_names))
        },
        "euclidean_distance_matrix": {
            obf_names[i]: {obf_names[j]: round(euclidean_matrix[i][j], 6) for j in range(len(obf_names))}
            for i in range(len(obf_names))
        }
    }
    with open(output_json, mode="w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Расчет матрицы сходства обфускаций в R^18")
    parser.add_argument(
        "--input-dir",
        default="results/vectors_r18",
        help="Директория с векторами"
    )
    parser.add_argument(
        "--metric",
        default="score",
        choices=["score", "precision", "recall", "all"],
        help="Метрика для анализа (score, precision, recall или all)"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.resolve()
    base_dir = (project_root / args.input_dir).resolve()

    metrics = ["score", "precision", "recall"] if args.metric == "all" else [args.metric]

    for m in metrics:
        json_file = base_dir / f"obfuscation_vectors_{m}.json"
        print("=" * 75)
        print(f"РАСЧЕТ МАТРИЦЫ СХОДСТВА ОБФУСКАЦИЙ (МЕТРИКА: {m.upper()})")
        print(f"Источник данных: {json_file}")
        print("=" * 75)

        vectors, metric_name, dim = load_vectors(str(json_file))
        obf_names, cos_mat, euc_mat, pairs = build_matrices(vectors)

        csv_cos = base_dir / f"obfuscation_similarity_cosine_{m}.csv"
        csv_euc = base_dir / f"obfuscation_distance_euclidean_{m}.csv"
        out_json = base_dir / f"obfuscation_similarity_matrices_{m}.json"

        save_matrix_to_csv(obf_names, cos_mat, str(csv_cos))
        save_matrix_to_csv(obf_names, euc_mat, str(csv_euc))
        save_json_results(obf_names, cos_mat, euc_mat, m, str(out_json))

        print(f"Сохранена матрица косинусного сходства ({len(obf_names)}x{len(obf_names)}): {csv_cos}")
        print(f"Сохранена матрица евклидовых расстояний ({len(obf_names)}x{len(obf_names)}): {csv_euc}")
        print(f"Сохранены полные матрицы в JSON: {out_json}")

        # Сортируем пары по убыванию косинусного сходства
        pairs.sort(key=lambda x: x[0], reverse=True)

        print("\n--- ТОП-10 НАИБОЛЕЕ БЛИЗКИХ ПАР ОБФУСКАЦИЙ (Поведение алгоритмов почти идентично) ---")
        for rank, (cos_sim, euc_dist, o1, o2) in enumerate(pairs[:10], 1):
            print(f"  {rank:2d}. {o1:<16} <---> {o2:<16} | Cosine: {cos_sim:.5f} | Euclidean: {euc_dist:.5f}")

        print("\n--- ТОП-10 НАИБОЛЕЕ ДАЛЕКИХ ПАР ОБФУСКАЦИЙ (Принципиально разный характер влияния) ---")
        for rank, (cos_sim, euc_dist, o1, o2) in enumerate(pairs[-10:], 1):
            print(f"  {rank:2d}. {o1:<16} <---> {o2:<16} | Cosine: {cos_sim:.5f} | Euclidean: {euc_dist:.5f}")
        print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
