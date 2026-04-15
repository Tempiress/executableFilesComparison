import argparse
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

# Добавляем путь к scripts, чтобы импортировать bin2asm
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
#sys.path.append(os.path.join(os.getcwd(), 'asm2vec'))

try:
    from scripts.bin2asm import bin2asm
except ImportError:
    try:
        import bin2asm
    except ImportError:
        print("[Error] Не найден bin2asm.py")
        sys.exit(1)

import asm2vec.utils

def cosine_similarity(v1, v2):
    return (v1 @ v2 / (v1.norm() * v2.norm())).item()


def compare_programs(bin1_path, bin2_path, model_path, epochs=10, device='auto', lr=0.02):
    """
    Сравнивает два бинарных файла целиком и возвращает оценку их схожести (0.0 - 1.0).
    """
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # -Подготовка папок-
    temp_dir = Path("temp_full_comparison")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    dir1 = temp_dir / "bin1"
    dir2 = temp_dir / "bin2"
    dir1.mkdir()
    dir2.mkdir()

    # -Дизассемблирование-
    print(f"[*] Extracting functions from {Path(bin1_path).name}...")
    count1 = bin2asm(Path(bin1_path), dir1, minlen=10)

    print(f"[*] Extracting functions from {Path(bin2_path).name}...")
    count2 = bin2asm(Path(bin2_path), dir2, minlen=10)

    if count1 == 0 or count2 == 0:
        print("[Error] No functions found in one of the binaries.")
        shutil.rmtree(temp_dir)
        return 0.0

    # -Загрузка данных и модели-
    print("[*] Vectorizing functions...")
    # Загружаем ВСЕ функции из обоих бинарников сразу
    functions, tokens_new = asm2vec.utils.load_data([dir1, dir2])

    model, tokens = asm2vec.utils.load_model(model_path, device=device)
    tokens.update(tokens_new.tokens)
    model.update(len(functions), tokens.size())
    model = model.to(device)

    # -Обучение (Fine-tuning)-
    # Мы "дообучаем" векторы для новых функций, не меняя веса самой модели
    model = asm2vec.utils.train(
        functions,
        tokens,
        model=model,
        epochs=epochs,
        device=device,
        mode='test',
        learning_rate=lr
    )

    # -Расчет метрики схожести-
    print("[*] Calculating similarity score...")

    embeddings = model.to('cpu').embeddings_f(torch.arange(len(functions)))

    # Разделяем функции по принадлежности к файлу
    # bin2asm записывает имя исходного файла в meta['file']
    bin1_name = Path(bin1_path).name
    bin2_name = Path(bin2_path).name

    funcs1_data = []  # (function_obj, embedding_vector)
    funcs2_data = []

    for i, func in enumerate(functions):
        vec = embeddings[i]
        origin = func.meta.get('file', '')
        if origin == bin1_name:
            funcs1_data.append((func, vec))
        if origin == bin2_name:
            funcs2_data.append((func, vec))



    # Определяем, кто меньше (чтобы покрытие было корректным)
    if len(funcs1_data) < len(funcs2_data):
        source_funcs = funcs1_data
        target_funcs = funcs2_data
    else:
        source_funcs = funcs2_data
        target_funcs = funcs1_data

    if not source_funcs:
        print("No valid functions to compare.")
        shutil.rmtree(temp_dir)
        return 0.0

    similarities = []

    for f_src, v_src in source_funcs:
        max_sim = -1.0
        # Ищем пару в другом бинарнике
        for f_tgt, v_tgt in target_funcs:
            sim = cosine_similarity(v_src, v_tgt)
            if sim > max_sim:
                max_sim = sim

        similarities.append(max_sim)

    # Очистка
    shutil.rmtree(temp_dir)

    # -Результат-
    # Среднее арифметическое от лучших совпадений
    total_score = np.mean(similarities) if similarities else 0.0

    return total_score


if __name__ == '__main__':
    # Входные данные
    #exe1 = r"D:\programming2025\asm2vec-pytorch-master\HW3.exe"
    #exe2 = r"D:\programming2025\asm2vec-pytorch-master\HW8.exe"  # Сравнение с самим собой
    # exe2 = r"path\to\another_program.exe"

    #model_file = r"D:\programming2025\asm2vec-pytorch-master\model.pt"

    #print(f"Comparing:\n A: {exe1}\n B: {exe2}")
    #print("-" * 30)

    #score = compare_programs(exe1, exe2, model_file, epochs=20)

    #print("-" * 30)
    #print(f"Total Similarity Score: {score:.6f}")

    parser = argparse.ArgumentParser(description="Compare two binares")
    parser.add_argument('--bin1', required=True)
    parser.add_argument('--bin2', required=True)
    parser.add_argument('--model', required=True)

    args = parser.parse_args()

    score = compare_programs(args.bin1, args.bin2, args.model, epochs=20)
    # print(score)
