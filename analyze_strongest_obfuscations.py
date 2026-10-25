"""
analyze_strongest_obfuscations.py

1. Для каждой из 63 обфускаций вычисляет среднее по всем 18 компонентам вектора:
   mean_18 = (1 / 18) * sum(s_1 ... s_18)
2. Добавляет столбец 'mean_18' в таблицу.
3. Добавляет итоговую строку 'TOTAL_AVERAGE' (усреднение столбца mean_18 и всех s_1..s_18).
4. Определяет самую сильную обфускацию (минимальное сходство, код скрыт сильнее всего)
   и выводит рейтинг стойкости.
"""

import os
import csv
import json
from pathlib import Path


def process_vectors(input_csv, output_csv, output_json):
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Файл не найден: {input_csv}")

    rows = []
    with open(input_csv, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        for r in reader:
            if r:
                rows.append(r)

    # Заголовок: добавляем новый столбец mean_18
    new_header = header + ["mean_18 (overall_resilience)"]

    processed_data = []
    col_sums = [0.0] * 18
    total_mean_sum = 0.0

    for r in rows:
        obf = r[0]
        prog_cnt = int(r[1])
        vals = [float(x) for x in r[2:20]]

        mean_18 = sum(vals) / len(vals)
        total_mean_sum += mean_18

        for idx, v in enumerate(vals):
            col_sums[idx] += v

        processed_data.append({
            "obfuscation": obf,
            "programs_count": prog_cnt,
            "vector": vals,
            "mean_18": mean_18,
            "row_raw": r + [f"{mean_18:.6f}"]
        })

    num_obf = len(processed_data)
    avg_col_vals = [s / num_obf for s in col_sums]
    total_overall_mean = total_mean_sum / num_obf

    # Итоговая строка усреднения по всем 63 обфускациям
    total_row = ["TOTAL_AVERAGE", num_obf] + [f"{x:.6f}" for x in avg_col_vals] + [f"{total_overall_mean:.6f}"]

    # Сохраняем обновленный CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(new_header)
        for item in processed_data:
            writer.writerow(item["row_raw"])
        writer.writerow(total_row)

    print(f"Обновленный CSV сохранен в: {output_csv}")

    # Сортировка по возрастанию сходства:
    # Меньше сходство (score) -> сильнее обфускация!
    ranked_strongest = sorted(processed_data, key=lambda x: x["mean_18"])

    # Сохраняем метаданные в JSON
    json_data = {
        "metric": "score",
        "obfuscations_count": num_obf,
        "total_overall_mean": round(total_overall_mean, 6),
        "column_averages": {
            header[i + 2]: round(avg_col_vals[i], 6) for i in range(18)
        },
        "strongest_obfuscation": {
            "name": ranked_strongest[0]["obfuscation"],
            "mean_score": round(ranked_strongest[0]["mean_18"], 6),
            "programs_count": ranked_strongest[0]["programs_count"]
        },
        "rankings_ascending_similarity": [
            {
                "rank": idx + 1,
                "obfuscation": item["obfuscation"],
                "mean_score": round(item["mean_18"], 6),
                "programs_count": item["programs_count"]
            }
            for idx, item in enumerate(ranked_strongest)
        ]
    }

    with open(output_json, mode="w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"JSON с рейтингом сохранен в: {output_json}")

    return ranked_strongest, total_overall_mean, avg_col_vals, num_obf


def main():
    root = Path(__file__).parent.resolve()
    in_csv = root / "results" / "vectors_r18" / "obfuscation_vectors_score.csv"
    out_csv = root / "results" / "vectors_r18" / "obfuscation_vectors_with_mean.csv"
    out_json = root / "results" / "vectors_r18" / "obfuscation_strength_ranking.json"

    ranked, overall_mean, col_avgs, n = process_vectors(in_csv, out_csv, out_json)

    print("\n" + "=" * 70)
    print("РЕЙТИНГ СТОЙКОСТИ ОБФУСКАЦИЙ (ПО МЕТРИКЕ СХОДСТВА):")
    print(f"Всего исследовано обфускаций: {n}")
    print(f"Общее среднее по всей матрице (TOTAL_AVERAGE): {overall_mean:.6f}")
    print("=" * 70)

    print("\n--- ТОП-10 САМЫХ СИЛЬНЫХ ОБФУСКАЦИЙ (Минимальное сходство, код скрыт лучше всего) ---")
    for idx, item in enumerate(ranked[:10], 1):
        print(f"  {idx:2d}. {item['obfuscation']:<18} | Среднее сходство (mean_18): {item['mean_18']:.6f}")

    print("\n--- ТОП-10 НАИМЕНЕЕ ЭФФЕКТИВНЫХ ОБФУСКАЦИЙ (Максимальное сходство, код легко узнаваем) ---")
    for idx, item in enumerate(reversed(ranked[-10:]), 1):
        print(f"  {idx:2d}. {item['obfuscation']:<18} | Среднее сходство (mean_18): {item['mean_18']:.6f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
