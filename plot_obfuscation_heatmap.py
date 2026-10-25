"""
plot_obfuscation_heatmap.py

Построение тепловой карты сходства 63 обфускаций в пространстве R^18:
  1. Кластеризованная тепловая карта (Clustered Heatmap) — переупорядочивание
     на основе иерархической кластеризации (Ward / Average linkage) по матрице расстояний (1 - cos_sim).
     Показывает естественные блоки-кластеры похожих техник.
  2. Алфавитная тепловая карта (Alphabetical Heatmap) — для быстрого поиска конкретной пары.

Результаты сохраняются в высоком разрешении (DPI=300) в results/vectors_r18/
"""

import os
import json
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform


def load_similarity_matrix(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Файл матрицы не найден: {json_path}")

    with open(json_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    obf_names = data["obfuscations"]
    sim_dict = data["cosine_similarity_matrix"]
    n = len(obf_names)

    # Собираем симметричную матрицу сходства
    matrix = []
    for o1 in obf_names:
        row = [sim_dict[o1][o2] for o2 in obf_names]
        matrix.append(row)

    return obf_names, matrix, data.get("metric", "score")


def plot_heatmap(obf_names, matrix, output_path, title, cmap="viridis"):
    n = len(obf_names)

    fig, ax = plt.subplots(figsize=(20, 18), dpi=300)

    # Находим реальный диапазон значений (кроме диагонали 1.0) для контрастности
    off_diag = [matrix[i][j] for i in range(n) for j in range(n) if i != j]
    vmin = min(off_diag) if off_diag else 0.85
    vmax = 1.0

    im = ax.imshow(matrix, cmap=cmap, interpolation="nearest", vmin=vmin, vmax=vmax)

    # Настройка осей и подписей
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(obf_names, rotation=90, fontsize=8, ha="center")
    ax.set_yticklabels(obf_names, fontsize=8)

    # Делаем подписи читаемыми и ровными
    ax.tick_params(axis="both", which="both", length=2)

    # Цветовая шкала
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.tick_params(labelsize=11)
    cbar.set_label("Косинусное сходство векторов в $\mathbb{R}^{18}$", fontsize=13, labelpad=12)

    plt.title(title, fontsize=16, pad=18, fontweight="bold")
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[OK] Тепловая карта сохранена: {output_path}")


def plot_clustered_heatmap(obf_names, matrix, output_path, metric_name, cmap="viridis"):
    """
    Кластеризует строки и столбцы с помощью scipy hierarchical clustering,
    чтобы родственные обфускации сформировали визуальные блоки.
    """
    n = len(obf_names)

    # Матрица расстояний: d = 1 - cos_sim
    dist_matrix = [[max(0.0, 1.0 - matrix[i][j]) for j in range(n)] for i in range(n)]
    for i in range(n):
        dist_matrix[i][i] = 0.0

    # Преобразуем в компактный вектор расстояний для linkage
    condensed_dist = squareform(dist_matrix, checks=False)

    # Иерархическая кластеризация методом средней связи (average linkage)
    z = linkage(condensed_dist, method="average")
    order = leaves_list(z)

    # Переставляем строки и столбцы в соответствии с дендрограммой
    ordered_names = [obf_names[i] for i in order]
    ordered_matrix = [[matrix[i][j] for j in order] for i in order]

    title = "Кластеризованная карта сходства 63 обфускаций OLLVM в $\\mathbb{R}^{18}$ (" + metric_name.upper() + ")"
    plot_heatmap(ordered_names, ordered_matrix, output_path, title, cmap=cmap)


def main():
    parser = argparse.ArgumentParser(description="Построение тепловой карты сходства обфускаций")
    parser.add_argument(
        "--metric",
        default="score",
        choices=["score", "precision", "recall"],
        help="Метрика для визуализации"
    )
    parser.add_argument(
        "--cmap",
        default="magma",
        help="Цветовая палитра matplotlib (magma, viridis, plasma, coolwarm, RdYlBu_r)"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.resolve()
    base_dir = project_root / "results" / "vectors_r18"
    json_path = base_dir / f"obfuscation_similarity_matrices_{args.metric}.json"

    print("=" * 70)
    print("ПОСТРОЕНИЕ ТЕПЛОВЫХ КАРТ СХОДСТВА ОБФУСКАЦИЙ")
    print(f"Источник: {json_path}")
    print(f"Цветовая схема: {args.cmap}")
    print("=" * 70)

    obf_names, matrix, metric_name = load_similarity_matrix(str(json_path))

    # 1. Кластеризованная тепловая карта (основная, показывает блоки-кластеры)
    clustered_png = base_dir / f"obfuscation_heatmap_clustered_{args.metric}.png"
    plot_clustered_heatmap(obf_names, matrix, str(clustered_png), metric_name, cmap=args.cmap)

    # 2. Алфавитная тепловая карта
    alphabetical_png = base_dir / f"obfuscation_heatmap_alphabetical_{args.metric}.png"
    title_alpha = "Матрица сходства 63 обфускаций OLLVM в $\\mathbb{R}^{18}$ (" + metric_name.upper() + ")"
    plot_heatmap(obf_names, matrix, str(alphabetical_png), title_alpha, cmap=args.cmap)

    print("=" * 70)
    print("Все тепловые карты успешно созданы!")


if __name__ == "__main__":
    main()
