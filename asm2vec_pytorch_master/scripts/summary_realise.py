import os
import shutil
import sys
from pathlib import Path

import torch

from bin2asm import cli

# Импортируем существующие модули проекта
# Предполагаем структуру:
# ./asm2vec/ (utils.py, datatype.py, model.py)
# ./scripts/ (bin2asm.py)
sys.path.append(os.path.join(os.getcwd(), 'scripts'))

root_path = Path(__file__).parent.parent.resolve()

ee = (os.path.join(str(root_path), 'asm2vec'))
if str(root_path) not in sys.path:
    sys.path.append(os.path.join(str(root_path), 'asm2vec'))

try:
    from scripts.bin2asm import bin2asm
except ImportError:
    # Если bin2asm.py лежит просто в корне или в другой папке
    try:
        import bin2asm
    except ImportError:
        print("Ошибка: Не удалось импортировать bin2asm. Убедитесь, что bin2asm.py находится в папке scripts/.")
        sys.exit(1)


import asm2vec.utils
import asm2vec.datatype


def cosine_similarity(v1, v2):
    return (v1 @ v2 / (v1.norm() * v2.norm())).item()


def compare_binaries(bin1_path, bin2_path, model_path, epochs=10, device='auto', lr=0.02, threshold=0.85):
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print("DEVICE: " + device)

    # 1. Подготовка временных директорий для ассемблерного кода
    # asm2vec работает с папками, содержащими файлы функций

    temp_dir = Path("temp_disassemble_path")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    DISASSEMBLE_PATH1 = temp_dir / "bin1"
    DISASSEMBLE_PATH2 = temp_dir / "bin2"
    DISASSEMBLE_PATH1.mkdir()
    DISASSEMBLE_PATH2.mkdir()

    #DISASSEMBLE_PATH1 = "D:\\programming2025\\asm2vec-pytorch-master\\bin1"
    #DISASSEMBLE_PATH2 = "D:\\programming2025\\asm2vec-pytorch-master\\bin2"

    print(f"[*] Дизассемблирование файла {bin1_path}...")
    # Используем функцию bin2asm из готовой реализации
    # count1 = bin2asm(Path(bin1_path), out1, minlen=10)
    count1, count_func1 = cli(bin1_path, DISASSEMBLE_PATH1, 10)
    print(f"[*] Дизассемблирование файла {bin2_path}...")
    # count2 = bin2asm(Path(bin2_path), out2, minlen=10)
    count2, count_func2 = cli(bin2_path, DISASSEMBLE_PATH2, 10)

    if count1 == 0 or count2 == 0:
        print("Ошибка: Функции не найдены")
        return

    # 2. Загрузка данных
    print("[*] Загрузка данных в asm2vec...")
    # load_data принимает список путей к папкам с asm-файлами
    functions, tokens_new = asm2vec.utils.load_data([DISASSEMBLE_PATH1, DISASSEMBLE_PATH2])

    # 3. Загрузка и обновление модели
    print(f"[*] Загрузка модели из {model_path}...")
    model, tokens = asm2vec.utils.load_model(model_path, device=device)

    # Обновляем словарь токенов новыми инструкциями
    # tokens_new - это объект Tokens, нам нужен список токенов внутри него
    tokens.update(tokens_new.tokens)
    model.update(len(functions), tokens.size())
    model = model.to(device)

    # 4. Обучение (режим 'test' обновляет только векторы функций, веса сети заморожены)
    print("[*] Генерация эмбеддингов для новых функций...")
    model = asm2vec.utils.train(
        functions,
        tokens,
        model=model,
        epochs=epochs,
        device=device,
        mode='test',
        learning_rate=lr
    )

    # 5. Сравнение векторов
    print("[*] Анализ схожести...")
    embeddings = model.to('cpu').embeddings_f(torch.arange(len(functions)))   #Было cpu

    # Разделяем функции обратно по файлам
    funcs_bin1 = []
    funcs_bin2 = []

    bin1_name = Path(bin1_path).name
    bin2_name = Path(bin2_path).name

    for i, func in enumerate(functions):
        # bin2asm сохраняет имя исходного файла в метаданные
        f_origin = func.meta.get('file', '')
        vec = embeddings[i]

        if f_origin == bin1_name:
            funcs_bin1.append((func, vec))
        if f_origin == bin2_name:
            funcs_bin2.append((func, vec))

    # --- поиск уникальных пар ---

    # Шаг 1: Создаем список всех возможных комбинаций
    # Format: (score, index_in_list1, index_in_list2)
    all_candidates = []

    print(f"[*] Сравнение {len(funcs_bin1)} функций из bin1 с {len(funcs_bin2)} функциями из bin2...")

    for i in range(len(funcs_bin1)):
        for j in range(len(funcs_bin2)):
            func1, vec1 = funcs_bin1[i]
            func2, vec2 = funcs_bin2[j]

            # Считаем похожесть
            score = cosine_similarity(vec1, vec2)

            # Добавляем в список
            all_candidates.append((score, i, j))

    # Шаг 2: Сортируем список по убыванию похожести (лучшие сверху)
    all_candidates.sort(key=lambda x: x[0], reverse=True)

    # Шаг 3: Выбираем уникальные пары
    used_indices_1 = set()
    used_indices_2 = set()
    final_matches = []

    for score, idx1, idx2 in all_candidates:
        # Если хотя бы одна функция уже занята более сильной парой - пропускаем
        if idx1 in used_indices_1 or idx2 in used_indices_2:
            continue

        # Если свободны - создаем пару
        used_indices_1.add(idx1)
        used_indices_2.add(idx2)

        func1 = funcs_bin1[idx1][0]
        func2 = funcs_bin2[idx2][0]

        # Получаем "вес" функции (количество инструкций)
        # В asm2vec функции хранят инструкции в поле .insts
        weight = len(func1.insts)

        final_matches.append({
            'f1': func1.meta['name'],
            'f2': func2.meta['name'],
            'score': score,
            'weight': weight
        })


    #Расчёт продвинутых метрик
     # 1. Сумма похожестей (Total similarity mass)
    total_sim_mass = sum(match['score'] for match in final_matches if match['score'] > 0)

    # 2. Взвешенная сумма
    weighted_sim_sum = sum(match['score'] * match['weight'] for match in final_matches)
    total_weight_bin1 = sum(len(f[0].insts) for f in funcs_bin1)
    total_weight_bin2 = sum(len(f[0].insts) for f in funcs_bin2)

    # Метрика: взвешенное сходство
    score_weighted = weighted_sim_sum / max(total_weight_bin1, total_weight_bin2) #if total_weight_bin1 > 0 else 0

    # Метрика В: Среднее только по хорошим совпадениям (моя идея)
    # Полезна для оценки: "Если функция нашлась, насколько сильно ее переписали?"
    good_matches = [m['score'] for m in final_matches if m['score'] >= threshold]
    avg_strong_match = sum(good_matches) / len(good_matches) if good_matches else 0.0

    # Метрика А: Покрытие (Coverage Score)
    # Сумма очков / количество функций в самой большой программе
    max_funcs = max(len(funcs_bin1), len(funcs_bin2))
    score_coverage = total_sim_mass / max_funcs if max_funcs > 0 else 0

    # --- ВЫВОД ---

    print("-" * 60)
    print(f"Статистика сравнения:")
    print(f"Всего функций: Bin1={len(funcs_bin1)}, Bin2={len(funcs_bin2)}")
    print(f"Найдено пар (любого качества): {len(final_matches)}")
    print("-" * 60)
    print(f"1. Global Score (Покрытие функций):   {score_coverage:.4f}")
    print(f"   (учитывает, сколько функций вообще нашлось)")
    print(f"2. Logic Score (Взвешен по коду):     {score_weighted:.4f}")
    print(f"   (большие функции влияют сильнее)")
    print(f"3. Strong Match Avg (Качество пар):   {avg_strong_match:.4f}")
    print(f"   (среднее среди тех, что похожи > {threshold})")
    print("-" * 60)

    return score_weighted

    # print(f"\n{'Функция (Файл 1)':<30} | {'Функция (Файл 2)':<30} | {'Сходство':<10}")
    # print("-" * 80)
    #
    # good_matches_count = 0
    #
    # final_matches.sort(key=lambda x: x['score'], reverse = True)
    #
    # for res in final_matches:
    #     if res['score'] >= threshold:
    #         good_matches_count += 1
    #
    #     print(f"{res['f1']:<30} | {res['f2']:<30} | {res['score']:.4f}")
    #
    # total_funcs = len(funcs_bin1)
    # if total_funcs ==0: return 0.0
    #
    # print("-" * 80)
    # print(f"Функций в файле 1: {len(funcs_bin1)}")
    # print(f"Функций в файле 1: {len(funcs_bin2)}")
    # print(f"Найдено уникальных пар (score >= {threshold}): {good_matches_count}")
    # print(f"Процент совпадения: {good_matches_count / total_funcs:.4f}")
    #
    # return good_matches_count / total_funcs

if __name__ == '__main__':

    file_a = r"D:\programming2025\asm2vec-pytorch-master\HW3.exe"

    file_b = r"D:\programming2025\asm2vec-pytorch-master\HW3.exe"
    ww = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\c10\O2\combinator"
    model_p = r"D:\programming2025\asm2vec-pytorch-master\model.pt"

    bb1 = r"D:\programming2025\asm2vecRework\MyResearch\coreutils-polybench-hashcat\c09\O0\prepare"
    bb2 = r"D:\programming2025\asm2vecRework\MyResearch\coreutils-polybench-hashcat\g10\O2\prepare"

    p2 = "./coreutils-polybench-hashcat/g10/O2/3mm"
    p2 = "./coreutils-polybench-hashcat/aoc/O2/3mm"


    cc1 = r"D:\programming2025\MyResearch\train_programs\elevator.exe"
    cc2 = r"D:\programming2025\MyResearch\train_programs\x64dbg.exe"

    pyt1= r"H:\ResearchWorkCUDA\train_programs\python-3.12.7-amd64.exe"
    pyt2 = r"H:\ResearchWorkCUDA\train_programs\python-3.14.3-amd64.exe"

    obf_p1 = r"./all_obf/3mm"
    p1 = r"./coreutils-polybench-hashcat/aoc/O0/3mm"
    p2 = r"./coreutils-polybench-hashcat/aoc/O2/3mm"

    w = compare_binaries(obf_p1, p1, model_p, epochs=20)
    print(f"{w}")


    
