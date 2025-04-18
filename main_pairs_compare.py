import concurrent.futures
import os
from functools import partial
from progress.bar import Bar
from similarity import similarity


def main_compare_assist(args, p1_funks, p2_funks):
    f, g = args
    # Сравнение функции
    ssim, lndf = similarity(f, g, p1_funks, p2_funks)
    return {
        "pair": (f, g),
        "sim": ssim,
        "num_block_in_first": lndf[0],
        "num_block_in_second": lndf[1]}


def main_compare(matrix1, matrix2, p1_funks, p2_funks):
    print("Start main_compare \n")
    # Генерация всех возможных пар
    Pairs = []
    for file1 in range(1, len(matrix1)):
        for file2 in range(1, len(matrix2)):
            Pairs.append((matrix1[0][file1], matrix2[0][file2]))

    # Сравнение всех пар
    print(f"count numbers of comparisons: {len(Pairs)}")

    worker = partial(main_compare_assist, p1_funks = p1_funks, p2_funks = p2_funks)

    with concurrent.futures.ProcessPoolExecutor(max_workers=min(50, os.cpu_count() * 2 + 2)) as executor:
        # Отправляем задачи более мелкими порциями
        future_to_pair = {
            executor.submit(worker, pair): pair
            for pair in Pairs
        }
        PairWithSim = []
        for future in concurrent.futures.as_completed(future_to_pair):
            try:
                PairWithSim.append(future.result())
            except Exception as e:
                print(f"Error processing pair: {e}")

    # Сортировка пар по убыванию схожести
    PairWithSim.sort(key=lambda x: x["sim"], reverse=True)

    print("find optimal pairs...")
    # Выбор оптимальных пар
    used_p1 = set()
    used_p2 = set()
    p1_nodes = []
    p2_nodes = []
    counter = 0

    for pair in PairWithSim:
        f, g = pair["pair"]

        if f not in used_p1 and g not in used_p2:
            p1_nodes.append({
                "new_label": counter,
                "old_label": f
            })
            p2_nodes.append({
                "new_label": counter,
                "old_label": g
            })
            used_p1.add(f)
            used_p2.add(g)
            counter += 1

    print("End of main_compare \n")
    return p1_nodes, p2_nodes
