import os
from multiprocessing import Value, Lock
import numpy as np
from blocklinks4 import *
from opcodeparser import *
from renamefile import *
import pickle
from functools import lru_cache
import orjson # В 2-3x быстрее стандартного json

def create_matrix2(json_data1, json_data2):
    """
    Генерация матрицы
    :param json_data1, json_data2:
    :return:
    """

    data1 = orjson.loads(json_data1)
    data2 = orjson.loads(json_data2)
    size_matrix = max(len(data1), len(data2)) + 2

    matrix1 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data1.items():
        matrix1[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1
        matrix1[int(block_data["NumBlock"])][int(block_data["NumBlockFail"])] = 1

    matrix2 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data2.items():
        matrix2[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1
        matrix2[int(block_data["NumBlock"])][int(block_data["NumBlockFail"])] = 1

    return matrix1, matrix2


@lru_cache(maxsize=1000)
def cached_op_parser(func_dict_tuple, cfg):
    # Преобразуем кортеж обратно в dict
    func_dict = dict(func_dict_tuple)
    return op_parser(func_dict[cfg])

def similarity(cfg1, cfg2, p1_funks, p2_funks):
    """
     Число Хемминга (0-идентич., 1- не иднетич.)
    :param: cfg1 cfg2
    :return: double, difference
    """
    op1 = op_parser(p1_funks[cfg1])
    op2 = op_parser(p2_funks[cfg2])

    #p1_tuple = tuple(sorted(p1_funks.items()))
    #p2_tuple = tuple(sorted(p2_funks.items()))

    #print(op1.__class__)
    #op11 = cached_op_parser(p1_tuple, cfg1)
    #op22 = cached_op_parser(p2_tuple, cfg2)
    # print(op11.__class__)

    data1 = orjson.loads(op1)
    data2 = orjson.loads(op2)
    sim_array = find_similar_blocks(op1, op2)
    rename_op2, diff = rename_block(data1, data2, sim_array)

    sim_dict = orjson.loads(sim_array)
    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    size_matrix0 = min(len(data1), len(data2)) + 1
    max_size_matrix = max(len(data1), len(data2)) + 1
    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)

    # Оптимизация 1: Предварительно вычисляем keys для всех блоков
    keys_cache = {}
    for key, value in sim_dict.items():
        block = value.get("block")
        if block not in keys_cache:
            keys_cache[block] = []
        keys_cache[block].append(key)

    # Оптимизация 2: Предварительно вычисляем sim значения
    sim_cache = {}
    for i in range(1, size_matrix0):
        block = str(i)
        if block in keys_cache and keys_cache[block]:
            first_key = keys_cache[block][0]
            sim_value = 1 if sim_dict[first_key]["simequal"] == 1 else sim_dict[first_key]["simcount"] / 100
            sim_cache[block] = sim_value
        else:
            sim_cache[block] = 0

    A = 0
    for i in range(1, size_matrix0):
        for j in range(1, size_matrix0):
            A0 = sim_cache[str(i)] + sim_cache[str(j)]
            A += (1 ^ (umatrix1[i][j] ^ umatrix2[i][j])) * A0


    C = float(A) / ((max_size_matrix - 1) * (max_size_matrix - 1) * 2)
    # print("end similarity.")
    return C, diff

#
# def create_matrix(json_data1):
#     """
#     Генерация матрицы
#     :param json_data1:
#     :return:
#     """
#     # dt = block_links(json_data1)
#     data = orjson.loads(json_data1)
#     size_matrix = len(data) + 2
#
#     matrix = np.zeros((size_matrix, size_matrix), dtype=int)
#
#     for block_id, block_data in data.items():
#         matrix[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1
#
#     return matrix


# Выносим функцию в глобальную область
def compute_element(i, j, mat1, mat2, funk1, funk2):
    sim_i = similarity(mat1[0][i], mat2[0][i], funk1, funk2)[0]
    sim_j = similarity(mat1[0][j], mat2[0][j], funk1, funk2)[0]
    return (1 ^ (mat1[i][j] ^ mat2[i][j])) * (sim_i + sim_j)

def hemming_prog(matrix1, matrix2, maxlen, p1_funk, p2_funk):
    import concurrent.futures
    import sys
    from functools import partial

    size_matrix = len(matrix1)
    indices = [(i, j) for i in range(1, size_matrix)
               for j in range(1, size_matrix)]


    print(f"Count of indexes in hemming prog: {len(indices)}")
    # Создаем partial функцию с передачей данных
    worker = partial(compute_element,
                     mat1=matrix1,
                     mat2=matrix2,
                     funk1=p1_funk,
                     funk2=p2_funk)

    try:

        with concurrent.futures.ProcessPoolExecutor(max_workers=33) as executor:
            futures = [executor.submit(worker, i, j) for i, j in indices]

            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"Ошибка в процессе: {e}", file=sys.stderr)
                    raise

    except Exception as e:
        print(f"Глобальная ошибка: {e}", file=sys.stderr)
        raise

    A = sum(results)
    C = float(A) / ((maxlen - 1) * (maxlen - 1) * 2)
    return C
