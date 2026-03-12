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



def evaluate_matching(p1_nodes, p2_nodes):
    """
    Пусть функции p1_nodes и p2_nodes - это списки функций, которые соответствуют друг другу.
    То есть, если p1_nodes[i] соответствует p2_nodes[i]
    """

    total_matched = len(p1_nodes) # Сколько пар нашёл алгоритм
    correct = 0

    for n1,  n2 in zip(p1_nodes, p2_nodes):
        if n1['old_label'] == n2['old_label']:
            correct += 1
    
    total_p1 = len(p1_nodes)

    precision = round(correct / total_matched , 4) if total_matched else 0.0
    recall = round(correct / total_p1, 4) if total_p1 else 0.0

    return {
        "correct" : correct,
        "total_matched": total_matched,
        "precision": precision,
        "recall": recall
    }

    


def create_matrix2(data1, data2):
    """
    Генерация матрицы
    :param json_data1, json_data2:
    :return:
    """

    # data1 = orjson.loads(json_data1)
    # data2 = orjson.loads(json_data2)
    data1 = safe_load_json(data1)
    data2 = safe_load_json(data2)

    # вычисляем максимальный индекс блока (ID), который реально существует
    max_id = 0
    for d in (data1, data2):
        for block in d.values():
            max_id = max(max_id, int(block.get("NumBlock", 0)), int(block.get("NumBlockLinks", 0)),
                         int(block.get("NumBlockFail", 0)))
                         
    # Матрица всегда должна вмещать самый большой ID 
    size_matrix = max_id + 2

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
        # self.b_links = block_links(orjson.dumps(self.data).decode('utf-8'))
        self.b_links = block_links(self.data)


def fast_similarity(pref1, pref2, config):
    try:
        # Этап 1: Поиск похожих блоков (передаем словари, получаем словарь)
        sim_dict = find_similar_blocks(pref1.data, pref2.data, config=config)

        # Этап 2: Переименование блоков
        # ВАЖНО: rename_block раньше принимала sim_array (строку).
        # orjson.loads(sim_array), так как мы передаем готовый sim_dict.
        rename_op2, diff = rename_block(pref1.data, pref2.data, sim_dict)

        # Этап 3: Построение графа для переименованной функции
        b_links2 = block_links(rename_op2)

        size_matrix0 = min(len(pref1.data), len(pref2.data)) + 1
        max_size_matrix = max(len(pref1.data), len(pref2.data)) + 1

        # Этап 4: Матрицы и вычисления
        umatrix1, umatrix2 = create_matrix2(pref1.b_links, b_links2)

        # защита от ошибки: берем реальный размер, чтобы NumPy ничего не обрезал
        actual_size = min(size_matrix0, umatrix1.shape[0])


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

        m1_core = umatrix1[1:actual_size, 1:actual_size]
        m2_core = umatrix2[1:actual_size, 1:actual_size]

        xor_result = 1 ^ (m1_core ^ m2_core)
        # Вырезаем нужный кусок из sim_cache, чтобы он в точности соответствовал размеру матриц
        sim_slice = sim_cache[1:actual_size]
        sim_sum = sim_slice[:, np.newaxis] + sim_slice

        A = np.sum(xor_result * sim_sum)

        if max_size_matrix <= 1: return 0.0, diff

        C = float(A) / ((max_size_matrix - 1) * (max_size_matrix - 1) * 2)
        return C, diff

    except Exception as e:
        print(f"Error inside fast_similarity: {e}", file=sys.stderr)
        return 0.0, 0


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

    size_matrix = len(matrix1)
    if size_matrix <= 1: return 0.0

    print("Computing pairwise function similarities...")
    max_k = min(len(labels1), len(labels2), size_matrix - 1)
    sim_array = np.zeros(max_k, dtype=np.float32)

    for k in range(max_k):
        n1_k, n2_k = labels1[k], labels2[k]
        sim_val = 0.0
        if n1_k in cache1 and n2_k in cache2:
            sim_val, _ = fast_similarity(cache1[n1_k], cache2[n2_k], config=config)
        sim_array[k] = sim_val

    print("Computing final matrix distances using broadcasting...")
    try:
        if hasattr(matrix1, 'astype'):
            m1_core = matrix1[1:max_k+1, 1:max_k+1].astype(np.float32).astype(np.int8)
            m2_core = matrix2[1:max_k+1, 1:max_k+1].astype(np.float32).astype(np.int8)
        else:
            raise ValueError()
    except Exception:
        # Fallback for Python lists or uncastable objects
        m1_core = np.zeros((max_k, max_k), dtype=np.int8)
        m2_core = np.zeros((max_k, max_k), dtype=np.int8)
        for i in range(max_k):
            for j in range(max_k):
                try: m1_core[i, j] = int(matrix1[i+1][j+1])
                except: pass
                
                try: m2_core[i, j] = int(matrix2[i+1][j+1])
                except: pass

    xor_res = 1 ^ (m1_core ^ m2_core)
    sim_sum = sim_array[:, np.newaxis] + sim_array
    
    A = np.sum(xor_res * sim_sum)

    if maxlen <= 1: return 0.0

    C = float(A) / ((maxlen - 1) * (maxlen - 1) * 2)
    return C


def similarity(cfg1, cfg2, p1_funks, p2_funks, config):
    # будет медленной, так как создает PrecomputedFunc на лету
    if cfg1 not in p1_funks or cfg2 not in p2_funks: return 0.0, 0

    pref1 = PrecomputedFunc(cfg1, p1_funks[cfg1], config)
    pref2 = PrecomputedFunc(cfg2, p2_funks[cfg2], config)
    return fast_similarity(pref1, pref2, config)