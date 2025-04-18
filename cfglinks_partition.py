import copy
import asyncio
import numpy as np
from line_profiler import profile
from progress.bar import Bar

from main_pairs_compare import main_compare
from opcodeparser import *


# def count_links(path):
#     """Подсчёт количества импортов """
#     with open(path, 'r') as f:
#         json_imports = f.read()
#         data = json.loads(json_imports)
#     count_imports = 0
#
#     for item in data:
#         count_imports += len(item["imports"])
#     return count_imports


def swap_columns(matrix, col1, col2):
    """Поменять местами два столбца"""
    for row in matrix:
        row[col1], row[col2] = row[col2], row[col1]


def swap_rows(matrix, row1, row2):
    """Поменять местами две строчки"""
    m1 = matrix[row2]
    c = copy.copy(matrix[row1])
    matrix[row1] = m1
    matrix[row2] = c


def incidence_matr_gen(lks):
    """Создание и заполнение матрицы инцидентности по файлам импортов"""
    names = [item["name"] for item in lks]
    matr = np.zeros((len(names) + 1, len(names) + 1), dtype='object')

    matr[1:, 0] = names
    matr[0, 1:] = names

    for i, item in enumerate(lks):
        imports = set(item["imports"])
        for j, name in enumerate(names):
            if name != item["name"] and name in imports:
                matr[i + 1, j + 1] = 1

    # Подсчёт количества связей в матрице инцидентности (для отладки)
    count_lks = 0
    for i in range(1, len(matr)):
        for j in range(1, len(matr)):
            if matr[i][j] == 1:
                count_lks += 1
    print("Lks in incidence matr:", count_lks)

    return matr


def links_two_program(p1_funcs, p2_funcs, lks1, lks2):
    print("Generate matrices...")
    matrix1 = incidence_matr_gen(lks1)
    matrix2 = incidence_matr_gen(lks2)
    p1_nodes, p2_nodes = main_compare(matrix1, matrix2, p1_funcs, p2_funcs)
    print("processing p1_nodes...")

    for p1_node in p1_nodes:
        p1_node['new_label'] + 1 # Потому что матрица сдвинута
        if p1_node['old_label'] in matrix1[0]:
            col_index = np.where(matrix1[0] == p1_node['old_label'])[0][0]
            if col_index != p1_node['new_label']:
                swap_columns(matrix1, col_index, p1_node['new_label'] + 1)
                swap_rows(matrix1, col_index, p1_node['new_label'] + 1)


    # НАЧАЛО Отладка
    # file_martix1 = open("./Debug/twoFuncDebug/fileMatrix1.txt", 'w')
    # file_martix1.write(f"{path_cfg1}  {label_map_path1} \n")
    # for i in range(1, len(matrix1)):
    #     for j in range(1, len(matrix1)):
    #         file_martix1.write(str(matrix1[i][j]))
    #     file_martix1.write('\n')
    #
    #
    # file_martix1.close()
    # КОНЕЦ Отладка

    print("processing p2_nodes... ")
    # bar2 = Bar('Processing', max=len(p2_nodes))
    for p2_node in p2_nodes:
        p2_node['new_label'] + 1 # Потому что матрица сдвинута
        # if hxconverter2(p2_node['old_label']) in matrix2[0]:
        if p2_node['old_label'] in matrix2[0]:
            # col_index = np.where(matrix2[0] == hxconverter2(p2_node['old_label']))[0][0]
            col_index = np.where(matrix2[0] == p2_node['old_label'])[0][0]
            if col_index != p2_node['new_label']:
                swap_columns(matrix2, col_index, p2_node['new_label'] + 1)
                swap_rows(matrix2, col_index, p2_node['new_label'] + 1)
        # bar2.next()
    # bar.finish()

    # НАЧАЛО Отладка

    # file_martix2 = open("./Debug/twoFuncDebug/fileMatrix2.txt", 'w')
    # file_martix2.write(f"{path_cfg2}  {label_map_path2} \n")
    # for i in range(1, len(matrix2)):
    #     for j in range(1, len(matrix2)):
    #         file_martix2.write(str(matrix2[i][j]))
    #     file_martix2.write('\n')
    #
    # file_martix2.close()
    # КОНЕЦ Отладка

    return matrix1, matrix2
