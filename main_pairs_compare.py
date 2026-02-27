import concurrent.futures
import os
from functools import partial
from progress.bar import Bar
from similarity import similarity
import torch
from pathlib import Path
import shutil
import sys
import random
import numpy as np

sys.path.append(os.path.join(os.getcwd(), 'scripts'))

root_path = Path(__file__).parent.resolve()

try:
    from asm2vec_pytorch_master.scripts import bin2asm
except ImportError:
    print("Ошибка: Не удалось импортировать bin2asm. Убедитесь, что bin2asm.py находится в папке scripts/.")
    sys.exit(1)


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


set_seed(42)

import asm2vec.utils
import asm2vec.datatype

def main_compare_assist(args, p1_funks, p2_funks, config):
    f, g = args
    # Сравнение функции
    ssim, lndf = similarity(f, g, p1_funks, p2_funks, config=config)
    return {
        "pair": (f, g),
        "sim": ssim}
        # "num_block_in_first": lndf[0],
        # "num_block_in_second": lndf[1]}


def main_compare(matrix1, matrix2, p1_funks, p2_funks, config):
    print("Start main_compare \n")
    # Генерация всех возможных пар
    Pairs = []
    for file1 in range(1, len(matrix1)):
        for file2 in range(1, len(matrix2)):
            Pairs.append((matrix1[0][file1], matrix2[0][file2]))

    # Сравнение всех пар
    print(f"count numbers of comparisons: {len(Pairs)}")

    worker = partial(main_compare_assist, p1_funks = p1_funks, p2_funks = p2_funks, config=config)

    with concurrent.futures.ProcessPoolExecutor(1) as executor:#max_workers=min(50, os.cpu_count() * 2 + 2)) as executor:
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


def main_compareGPU(matrix1, matrix2, p1_funks, p2_funks, config):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"DEVICE: {device}")

    # Подготовка папок
    temp_dir = Path("temp_disassemble_path_maincompare")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    DISASSEMBLE_PATH1 = temp_dir / "bin1"
    DISASSEMBLE_PATH2 = temp_dir / "bin2"
    DISASSEMBLE_PATH1.mkdir()
    DISASSEMBLE_PATH2.mkdir()

    # Дизассемблирование (извлекаем все функции сразу)
    print(f"[*] Дизассемблирование файла {config.bin1_path}...")
    count1, _ = bin2asm.cli(config.bin1_path, DISASSEMBLE_PATH1, 6)
    print(f"[*] Дизассемблирование файла {config.bin2_path}...")
    count2, _ = bin2asm.cli(config.bin2_path, DISASSEMBLE_PATH2, 6)

    if count1 == 0 or count2 == 0:
        print("Ошибка: Функции не найдены")
        return [], []



    files1_paths = []
    files1_indices = []
    for i in range(1, len(matrix1)):
        fname = matrix1[0][i]
        fpath = DISASSEMBLE_PATH1 / fname
        if fpath.exists():
            files1_paths.append(fpath)
            files1_indices.append(fname)  # Сохраняем имя для идентификации

    files2_paths = []
    files2_indices = []
    for i in range(1, len(matrix2)):
        fname = matrix2[0][i]
        fpath = DISASSEMBLE_PATH2 / fname
        if fpath.exists():
            files2_paths.append(fpath)
            files2_indices.append(fname)

    # Загрузка данных и модели
    print("[*] Загрузка и обучение модели asm2vec...")
    model_path = "H:\\programming2026\\ResearchWorkCUDA\\asm2vec_pytorch_master\\model_optim.pt"

    # Загружаем все файлы скопом
    all_files = files1_paths + files2_paths

    # Загружаем базовую модель
    model, tokens = asm2vec.utils.load_model(model_path, device=device)

    # Парсим функции
    functions, tokens_new = asm2vec.utils.load_data(all_files)

    if not functions:
        print("[Error] Функции не загрузились.")
        return [], []

    # Обновляем словарь и модель
    tokens.update(tokens_new)
    model.update(len(functions), tokens.size())
    model = model.to(device)

    # Обучение (Fine-tuning) один раз для всех векторов
    model = asm2vec.utils.train(
        functions,
        tokens,
        model=model,
        epochs=50,  # Увеличил с 20 до 50 для точности
        device=device,
        mode='test',
        learning_rate=0.02
    )

    # 6. Получение векторов и матричное сравнение
    print("[*] Вычисление матрицы схожести...")

    # Извлекаем векторы (они уже на GPU или переносим)
    # embeddings_f возвращает тензор (N, embedding_dim)
    all_embeddings = model.embeddings_f(torch.arange(len(functions)).to(device))

    # Разделяем обратно на группу 1 и группу 2
    n1 = len(files1_paths)
    embeddings1 = all_embeddings[:n1]  # Векторы первого бинарника
    embeddings2 = all_embeddings[n1:]  # Векторы второго бинарника

    # Нормализация векторов (для Cosine Similarity: A . B / (|A|*|B|))
    # Нормируем векторы сразу, чтобы потом просто перемножать
    embeddings1 = embeddings1 / embeddings1.norm(dim=1, keepdim=True)
    embeddings2 = embeddings2 / embeddings2.norm(dim=1, keepdim=True)

    # Матричное умножение: (N1, Dim) x (Dim, N2) -> (N1, N2)
    # В ячейке [i][j] будет cosine similarity между i-й функцией bin1 и j-й функцией bin2
    similarity_matrix = torch.mm(embeddings1, embeddings2.t())

    # Переносим на CPU для обработки списков
    sim_matrix_cpu = similarity_matrix.detach().cpu().numpy()

    # 7. Формирование списка пар для жадного алгоритма
    print("[*] Поиск уникальных пар...")
    Pairs = []

    # Проходим по матрице и собираем все связи
    rows, cols = sim_matrix_cpu.shape
    for r in range(rows):
        for c in range(cols):
            score = float(sim_matrix_cpu[r, c])
            # Сохраняем (score, имя_функции_1, имя_функции_2)
            Pairs.append((score, files1_indices[r], files2_indices[c]))

    # Сортируем по убыванию
    Pairs.sort(key=lambda x: x[0], reverse=True)

    # 8. Жадный выбор лучших пар
    used_p1 = set()
    used_p2 = set()
    p1_nodes = []
    p2_nodes = []
    counter = 0

    for score, fn1, fn2 in Pairs:
        if fn1 in used_p1 or fn2 in used_p2:
            continue

        # Можно добавить порог отсечения, например if score < 0.5: break

        p1_nodes.append({
            "new_label": counter,
            "old_label": fn1
        })
        p2_nodes.append({
            "new_label": counter,
            "old_label": fn2
        })
        used_p1.add(fn1)
        used_p2.add(fn2)
        counter += 1

    print("End of main_compare \n")
    return p1_nodes, p2_nodes



