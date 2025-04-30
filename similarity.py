import os
import sys
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


@lru_cache(maxsize=1000)
def cached_op_parser(func_dict_tuple, cfg):
    # Преобразуем кортеж обратно в dict
    func_dict = dict(func_dict_tuple)
    return op_parser(func_dict[cfg])

@lru_cache(maxsize=1000)
def cached_similarity(cfg1, cfg2, p1_funks_tuple, p2_funks_tuple):
    p1_funks = dict(p1_funks_tuple)
    p2_funks = dict(p2_funks_tuple)
    return similarity(cfg1, cfg2, p1_funks, p2_funks)

def similarity(cfg1, cfg2, p1_funks, p2_funks):
    try:
        # Проверяем типы входных данных
        if not isinstance(cfg1, str) or not isinstance(cfg2, str):
            print(f"Некорректные типы входных данных: cfg1={type(cfg1)}, cfg2={type(cfg2)}", file=sys.stderr)
            return 0.0, 0

        # Проверяем наличие ключей в словарях
        if cfg1 not in p1_funks or cfg2 not in p2_funks:
            print(f"Ключи не найдены: cfg1={cfg1}, cfg2={cfg2}", file=sys.stderr)
            return 0.0, 0

        try:
            op1 = op_parser(p1_funks[cfg1])
            op2 = op_parser(p2_funks[cfg2])
        except Exception as e:
            print(f"Ошибка в op_parser: {e}", file=sys.stderr)
            return 0.0, 0

        try:
            data1 = orjson.loads(op1)
            data2 = orjson.loads(op2)
        except Exception as e:
            print(f"Ошибка в orjson.loads: {e}", file=sys.stderr)
            return 0.0, 0

        try:
            sim_array = find_similar_blocks(op1, op2)
            rename_op2, diff = rename_block(data1, data2, sim_array)
        except Exception as e:
            print(f"Ошибка в find_similar_blocks/rename_block: {e}", file=sys.stderr)
            return 0.0, 0

        try:
            sim_dict = orjson.loads(sim_array)
            #print(f"Структура sim_dict: {sim_dict}", file=sys.stderr)
            b_links1 = block_links(op1)
            b_links2 = block_links(rename_op2)
        except Exception as e:
            print(f"Ошибка в block_links: {e}", file=sys.stderr)
            return 0.0, 0

        size_matrix0 = min(len(data1), len(data2)) + 1
        max_size_matrix = max(len(data1), len(data2)) + 1

        try:
            umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
        except Exception as e:
            print(f"Ошибка в create_matrix2: {e}", file=sys.stderr)
            return 0.0, 0

        # Векторизованное вычисление sim_cache
        sim_cache = np.zeros(size_matrix0, dtype=np.float32)
        for i in range(1, size_matrix0):
            block = str(i)
            # Ищем блок в sim_dict
            for key, value in sim_dict.items():
                if value.get('block') == block:
                    try:
                        simcount = value.get('simcount', 0)
                        simequal = value.get('simequal', 0)
                        #print(f"Обработка блока {block}: simcount={simcount}, simequal={simequal}", file=sys.stderr)
                        sim_value = 1 if simequal == 1 else simcount / 100
                        sim_cache[i] = sim_value
                        #print(f"Результат для блока {block}: sim_value={sim_value}", file=sys.stderr)
                        break
                    except Exception as e:
                        print(f"Ошибка при обработке блока {block}: {e}", file=sys.stderr)
                        continue

        # Векторизованное вычисление A
        try:
            i_indices, j_indices = np.meshgrid(np.arange(1, size_matrix0), np.arange(1, size_matrix0))
            xor_result = 1 ^ (umatrix1[1:size_matrix0, 1:size_matrix0] ^ umatrix2[1:size_matrix0, 1:size_matrix0])
            sim_sum = sim_cache[1:size_matrix0][:, np.newaxis] + sim_cache[1:size_matrix0]
            A = np.sum(xor_result * sim_sum)
        except Exception as e:
            print(f"Ошибка при вычислении A: {e}", file=sys.stderr)
            return 0.0, 0

        C = float(A) / ((max_size_matrix - 1) * (max_size_matrix - 1) * 2)
        return C, diff
    except Exception as e:
        print(f"Общая ошибка в similarity: {e}", file=sys.stderr)
        return 0.0, 0

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

def process_chunk(chunk_indices, matrix1, matrix2, p1_funk, p2_funk):
    results = []
    # print(f"Размеры матриц: matrix1={len(matrix1)}x{len(matrix1[0])}, matrix2={len(matrix2)}x{len(matrix2[0])}", file=sys.stderr)
    
    for i, j in chunk_indices:
        try:
            # Проверяем размеры матриц
            if i >= len(matrix1) or j >= len(matrix1[0]) or i >= len(matrix2) or j >= len(matrix2[0]):
                print(f"Индекс вне границ: i={i}, j={j}", file=sys.stderr)
                continue
                
            # Проверяем типы индексов
            if not isinstance(i, int) or not isinstance(j, int):
                print(f"Некорректные типы индексов: i={type(i)}, j={type(j)}", file=sys.stderr)
                continue
                
            # Получаем значения из матрицы
            try:
                # Проверяем, что matrix1[i] и matrix2[i] являются списками/массивами
                if not isinstance(matrix1[i], (list, np.ndarray)) or not isinstance(matrix2[i], (list, np.ndarray)):
                    print(f"Некорректный тип строки матрицы: matrix1[{i}]={type(matrix1[i])}, matrix2[{i}]={type(matrix2[i])}", file=sys.stderr)
                    continue
                    
                val1_i = matrix1[i][0]
                val2_i = matrix2[i][0]
                val1_j = matrix1[j][0]
                val2_j = matrix2[j][0]
            except (IndexError, TypeError) as e:
                print(f"Ошибка доступа к матрице: {e}", file=sys.stderr)
                continue
                
            # Преобразуем значения в строки
            val1_i = str(val1_i) if not isinstance(val1_i, str) else val1_i
            val2_i = str(val2_i) if not isinstance(val2_i, str) else val2_i
            val1_j = str(val1_j) if not isinstance(val1_j, str) else val1_j
            val2_j = str(val2_j) if not isinstance(val2_j, str) else val2_j
            
            # Вычисляем similarity
            try:
                sim_i, _ = similarity(val1_i, val2_i, p1_funk, p2_funk)
                sim_j, _ = similarity(val1_j, val2_j, p1_funk, p2_funk)
            except Exception as e:
                print(f"Ошибка в similarity: {e}", file=sys.stderr)
                continue
                
            # Проверяем значения перед вычислением
            try:
                # Проверяем, что значения являются числами
                if not isinstance(matrix1[i][j], (int, float)) or not isinstance(matrix2[i][j], (int, float)):
                    print(f"Некорректные значения в матрице: matrix1[{i}][{j}]={matrix1[i][j]}, matrix2[{i}][{j}]={matrix2[i][j]}", file=sys.stderr)
                    continue
                    
                # Вычисляем результат
                xor_result = 1 ^ (matrix1[i][j] ^ matrix2[i][j])
                sim_sum = sim_i + sim_j
                result = xor_result * sim_sum
                results.append(result)
            except Exception as e:
                print(f"Ошибка при вычислении результата: {e}", file=sys.stderr)
                continue
                
        except Exception as e:
            print(f"Общая ошибка в процессе: {e}", file=sys.stderr)
            continue
            
    return results

def hemming_prog(matrix1, matrix2, maxlen, p1_funk, p2_funk):
    import concurrent.futures
    from functools import partial
    import numpy as np

    size_matrix = len(matrix1)
    
    # Разбиваем индексы на чанки для лучшей параллелизации
    chunk_size = 1000
    indices = [(i, j) for i in range(1, size_matrix) for j in range(1, size_matrix)]
    chunks = [indices[i:i + chunk_size] for i in range(0, len(indices), chunk_size)]
    print(len(chunks))
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=min(33, len(chunks))) as executor:
            # Создаем partial функцию с фиксированными аргументами
            worker = partial(process_chunk, 
                          matrix1=matrix1,
                          matrix2=matrix2,
                          p1_funk=p1_funk,
                          p2_funk=p2_funk)
            
            futures = [executor.submit(worker, chunk) for chunk in chunks]
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    chunk_results = future.result()
                    if chunk_results:  # Добавляем только непустые результаты
                        results.extend(chunk_results)
                except Exception as e:
                    print(f"Ошибка в процессе: {e}", file=sys.stderr)
                    continue

    except Exception as e:
        print(f"Глобальная ошибка: {e}", file=sys.stderr)
        raise

    if not results:  # Если все результаты пустые
        return 0.0

    A = sum(results)
    C = float(A) / ((maxlen - 1) * (maxlen - 1) * 2)
    return C
