import os
import sys
import traceback
from multiprocessing import Value, Lock
import numpy as np
from blocklinks4 import *
from opcodeparser import *
# from renamefile import *
# import pickle
# from functools import lru_cache
import orjson  # В 2-3x быстрее стандартного json
from config import safe_load_json
import concurrent.futures
from functools import partial
from blocklinks4 import block_links
from opcodeparser import op_parser
from renamefile import rename_block


def create_matrix2(json_data1, json_data2):
    """
    Генерация матрицы
    :param json_data1, json_data2:
    :return:
    """

    # data1 = orjson.loads(json_data1)
    # data2 = orjson.loads(json_data2)
    data1 = safe_load_json(json_data1)
    data2 = safe_load_json(json_data2)
    size_matrix = max(len(data1), len(data2)) + 2

    # Создаем массивы индексов для быстрой векторизации
    indices1 = [(int(block_data["NumBlock"]), int(block_data["NumBlockLinks"])) for block_data in data1.values()]
    indices1_fail = [(int(block_data["NumBlock"]), int(block_data["NumBlockFail"])) for block_data in data1.values()]

    indices2 = [(int(block_data["NumBlock"]), int(block_data["NumBlockLinks"])) for block_data in data2.values()]
    indices2_fail = [(int(block_data["NumBlock"]), int(block_data["NumBlockFail"])) for block_data in data2.values()]

    # Создаем матрицы и заполняем их за один проход
    matrix1 = np.zeros((size_matrix, size_matrix), dtype=np.int8)
    matrix2 = np.zeros((size_matrix, size_matrix), dtype=np.int8)

    if indices1:
        rows1, cols1 = zip(*indices1)
        matrix1[rows1, cols1] = 1
        rows1_fail, cols1_fail = zip(*indices1_fail)
        matrix1[rows1_fail, cols1_fail] = 1

    if indices2:
        rows2, cols2 = zip(*indices2)
        matrix2[rows2, cols2] = 1
        rows2_fail, cols2_fail = zip(*indices2_fail)
        matrix2[rows2_fail, cols2_fail] = 1

    return matrix1, matrix2





# --- КЛАСС ДЛЯ КЭШИРОВАНИЯ ---
class PrecomputedFunc:
    """Хранит уже распаршенные данные функции, чтобы не считать их каждый раз"""

    def __init__(self, name, func_data, config):
        self.name = name

        # op_parser теперь возвращает словарь (dict)
        self.data = op_parser(func_data, config=config)

        # Строим граф связей.
        # ВАЖНО: Если функция block_links внутри делает orjson.loads(data),
        # вам нужно зайти в block_links и убрать там .loads(), чтобы она принимала dict.
        # Если вы пока не можете её изменить, можно временно обернуть так:
        # self.b_links = block_links(orjson.dumps(self.data).decode('utf-8'))
        self.b_links = block_links(self.data)


def fast_similarity(pref1, pref2, config):
    try:
        # Этап 1: Поиск похожих блоков (передаем словари, получаем словарь)
        sim_dict = find_similar_blocks(pref1.data, pref2.data, config=config)

        # Этап 2: Переименование блоков
        # ВАЖНО: rename_block раньше принимала sim_array (строку).
        # Зайдите в renamefile.py и убедитесь, что функция rename_block НЕ делает
        # orjson.loads(sim_array), так как мы передаем готовый sim_dict.
        rename_op2, diff = rename_block(pref1.data, pref2.data, sim_dict)

        # Этап 3: Построение графа для переименованной функции
        b_links2 = block_links(rename_op2)

        size_matrix0 = min(len(pref1.data), len(pref2.data)) + 1
        max_size_matrix = max(len(pref1.data), len(pref2.data)) + 1

        # Этап 4: Матрицы и вычисления
        umatrix1, umatrix2 = create_matrix2(pref1.b_links, b_links2)

        # УБРАЛИ: sim_dict = orjson.loads(sim_array)
        # (он у нас уже есть в виде словаря с Этапа 1)

        sim_cache = np.zeros(size_matrix0, dtype=np.float32)

        # Оптимизированный цикл заполнения весов
        if isinstance(sim_dict, dict):
            for key, val in sim_dict.items():
                try:
                    idx = int(val.get('block', -1))
                    if 0 < idx < size_matrix0:
                        simequal = val.get('simequal', 0)
                        sim_cache[idx] = 1.0 if simequal == 1 else val.get('simcount', 0) / 100.0
                except (ValueError, TypeError):
                    continue

        # ... (Вся матричная математика numpy остается без изменений) ...
        m1_core = umatrix1[1:size_matrix0, 1:size_matrix0]
        m2_core = umatrix2[1:size_matrix0, 1:size_matrix0]

        xor_result = 1 ^ (m1_core ^ m2_core)
        sim_sum = sim_cache[1:size_matrix0][:, np.newaxis] + sim_cache[1:size_matrix0]

        A = np.sum(xor_result * sim_sum)

        if max_size_matrix <= 1: return 0.0, diff

        C = float(A) / ((max_size_matrix - 1) * (max_size_matrix - 1) * 2)
        return C, diff

    except Exception as e:
        print(f"Error inside fast_similarity: {e}", file=sys.stderr)
        return 0.0, 0


# --- ФУНКЦИЯ ДЛЯ ПРОЦЕССОВ ---
def process_chunk_fast(chunk_indices, matrix1, matrix2, labels1, labels2, cache1, cache2, config):
    results = []
    for i, j in chunk_indices:
        try:
            if i - 1 >= len(labels1) or j - 1 >= len(labels2): continue

            name1 = labels1[i - 1]
            name2 = labels2[j - 1]

            # Получаем ребра (топология)
            try:
                edge1 = int(matrix1[i][j])
                edge2 = int(matrix2[i][j])
            except (ValueError, TypeError):
                edge1, edge2 = 0, 0

            xor_res = 1 ^ (edge1 ^ edge2)

            # Получаем имена узлов (функций) для сравнения
            n1_i, n2_i = labels1[i - 1], labels2[i - 1]
            n1_j, n2_j = labels1[j - 1], labels2[j - 1]

            # Достаем из кэша готовые объекты
            # Если функции нет в кэше, пропускаем или считаем 0
            if n1_i not in cache1 or n2_i not in cache2:
                sim_i = 0.0
            else:
                sim_i, _ = fast_similarity(cache1[n1_i], cache2[n2_i], config=config)

            if n1_j not in cache1 or n2_j not in cache2:
                sim_j = 0.0
            else:
                sim_j, _ = fast_similarity(cache1[n1_j], cache2[n2_j], config=config)

            res = xor_res * (sim_i + sim_j)
            # print(res)
            results.append(res)

        except Exception as e:
            continue
    return results


# --- Точка входа  ---
def hemming_prog(matrix1, matrix2, maxlen, p1_funks, p2_funks, config):
    # Извлекаем метки
    def get_headers(mat):
        if hasattr(mat, 'shape'):
            if mat.shape[0] > 0 and mat.shape[1] > 1: return mat[0, 1:]
        elif len(mat) > 0 and len(mat[0]) > 1:
            return mat[0][1:]
        return []

    labels1 = get_headers(matrix1)
    labels2 = get_headers(matrix2)

    if len(labels1) == 0 or len(labels2) == 0: return 0.0

    print("Pre-computing function data...")
    # Парсим всё 1 раз
    cache1 = {}
    cache2 = {}

    # Чтобы не парсить лишнее, берем только те функции, что есть в матрице
    for name in set(labels1):
        if name in p1_funks:
            cache1[name] = PrecomputedFunc(name, p1_funks[name], config)

    for name in set(labels2):
        if name in p2_funks:
            cache2[name] = PrecomputedFunc(name, p2_funks[name], config)

    # Параллельная обработка
    size_matrix = len(matrix1)
    indices = [(i, j) for i in range(1, size_matrix) for j in range(1, size_matrix)]

    # Увеличиваем размер чанка, чтобы меньше вызывать процессы
    chunk_size = 2000
    chunks = [indices[i:i + chunk_size] for i in range(0, len(indices), chunk_size)]

    results = []

    # cpu_count для выбора числа процессов
    max_workers = os.cpu_count() or 4

    print(f"Starting parallel comparison on {max_workers} workers...")

    try:
        for chunk in chunks:
            res = process_chunk_fast(
                             chunk_indices=chunk,
                             matrix1=matrix1,
                             matrix2=matrix2,
                             labels1=labels1,
                             labels2=labels2,
                             cache1=cache1,  # Передаем кэш
                             cache2=cache2,
                             config=config)
            if res: results.extend(res)



    except Exception as e:
        print(f"Global error: {e}", file=sys.stderr)
        return 0.0

    if not results: return 0.0

    A = sum(results)
    if maxlen <= 1: return 0.0

    C = float(A) / ((maxlen - 1) * (maxlen - 1) * 2)
    return C


def similarity(cfg1, cfg2, p1_funks, p2_funks, config):
    # будет медленной, так как создает PrecomputedFunc на лету
    if cfg1 not in p1_funks or cfg2 not in p2_funks: return 0.0, 0

    pref1 = PrecomputedFunc(cfg1, p1_funks[cfg1], config)
    pref2 = PrecomputedFunc(cfg2, p2_funks[cfg2], config)
    return fast_similarity(pref1, pref2, config)