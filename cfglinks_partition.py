import copy

import numpy as np
from progress.bar import Bar

from main_pairs_compare import main_compare
from opcodeparser import *


def count_links(path):
    """Подсчёт количества импортов """
    with open(path, 'r') as f:
        json_imports = f.read()
        data = json.loads(json_imports)
    count_imports = 0

    for item in data:
        count_imports += len(item["imports"])
        # print(item["name"])
        # print(len(item["imports"]))
    return count_imports


def pad_matrix(matrix1, matrix2):
    """Расширение меньшей матрицы до большей"""
    rows1, cols1 = matrix1.shape
    rows2, cols2 = matrix2.shape

    # Если размерности матриц уже совпадают, возвращаем их без изменений
    if rows1 == rows2 and cols1 == cols2:
        return matrix1, matrix2

    # Определяем, какая матрица больше и насколько
    max_rows = max(rows1, rows2)
    max_cols = max(cols1, cols2)

    # Создаем новые матрицы с размерами большей матрицы
    new_matrix1 = np.zeros((max_rows, max_cols), dtype='object')
    new_matrix2 = np.zeros((max_rows, max_cols), dtype='object')

    # Заполняем новые матрицы данными из исходных матриц
    new_matrix1[:rows1, :cols1] = matrix1
    new_matrix2[:rows2, :cols2] = matrix2

    return new_matrix1, new_matrix2


def hxconverter(num):
    nm = int(num[4:], 16)
    result = "cfg_" + str(nm) + ".txt"
    return result


def hxconverter2(num):
    nm = int(num[4:-4])
    nm = hex(nm)
    result = "fcn." + str(nm[2:])
    return result


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


def incidence_matr_gen(path: str):
    """Создание и заполнение матрицы инцидентности по файлам импортов"""
    with open(path, 'r') as f:
        data = json.load(f)

    names = [item["name"] for item in data]
    matr = np.zeros((len(names) + 1, len(names) + 1), dtype='object')

    matr[1:, 0] = names
    matr[0, 1:] = names

    for i, item in enumerate(data):
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
    print("Count lks in incidence matr:", count_lks)

    return matr


def links_two_program(path_cfg1, path_cfg2, label_map_path1, label_map_path2):
    matrix1 = incidence_matr_gen(label_map_path1)
    matrix2 = incidence_matr_gen(label_map_path2)
    p1_nodes, p2_nodes = main_compare(path_cfg1, path_cfg2, matrix1, matrix2)
    bar = Bar('Processing', max=len(p1_nodes))
    print("processing p1_nodes: ")

    for p1_node in p1_nodes:
        p1_node['new_label'] + 1 # Потому что матрица сдвинута
        # if hxconverter2(p1_node['old_label']) in matrix1[0]:
        if p1_node['old_label'] in matrix1[0]:
            # col_index = np.where(matrix1[0] == hxconverter2(p1_node['old_label']))[0][0]
            col_index = np.where(matrix1[0] == p1_node['old_label'])[0][0]
            if col_index != p1_node['new_label']:
                swap_columns(matrix1, col_index, p1_node['new_label'] + 1)
                swap_rows(matrix1, col_index, p1_node['new_label'] + 1)
        bar.next()
    bar.finish()


    # НАЧАЛО Отладка
    file_martix1 = open("./Debug/twoFuncDebug/fileMatrix1.txt", 'w')

    for i in range(1, len(matrix1)):
        for j in range(1, len(matrix1)):
            file_martix1.write(str(matrix1[i][j]))
        file_martix1.write('\n')


    file_martix1.close()
    # КОНЕЦ Отладка

    print("processing p2_nodes: ")
    bar2 = Bar('Processing', max=len(p2_nodes))
    for p2_node in p2_nodes:
        p2_node['new_label'] + 1 # Потому что матрица сдвинута
        # if hxconverter2(p2_node['old_label']) in matrix2[0]:
        if p2_node['old_label'] in matrix2[0]:
            # col_index = np.where(matrix2[0] == hxconverter2(p2_node['old_label']))[0][0]
            col_index = np.where(matrix2[0] == p2_node['old_label'])[0][0]
            if col_index != p2_node['new_label']:
                swap_columns(matrix2, col_index, p2_node['new_label'] + 1)
                swap_rows(matrix2, col_index, p2_node['new_label'] + 1)
        bar2.next()
    bar.finish()

    # НАЧАЛО Отладка

    file_martix2 = open("./Debug/twoFuncDebug/fileMatrix2.txt", 'w')

    for i in range(1, len(matrix2)):
        for j in range(1, len(matrix2)):
            file_martix2.write(str(matrix2[i][j]))
        file_martix2.write('\n')

    file_martix2.close()
    # КОНЕЦ Отладка

    return matrix1, matrix2

# main--------------------------------------------------

# folder1 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg'
# #folder2 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg2'
# folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
# folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'
#
# #folder2 = 'F:\\programming 2024\\Sci_Research\\C++programs\\cfgs2\\'
# #cfglinks_path =
# cfglinks_path2 = "F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker1_cfgcflinks.txt\\"
# matrix1, matrix2 = links_two_program(folder1, folder1, cfglinks_path, cfglinks_path)
# create_cfgs_from_exe("F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker1.exe", "F:\\programming 2024\\Sci_Research\\C++programs\\cfgs1\\")
# create_cfgs_from_exe("F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker_O1.exe", "F:\\programming 2024\\Sci_Research\\C++programs\\cfgs2\\")
#
# #cl = count_links("F:\\programming 2024\\Sci_Research\\cfgcflinks.txt")
# print(hemming_prog(matrix1, matrix2))



# print("Фактическое кол-во связей:", count_links("F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker1_cfgcflinks.txt\\"))
# hh = Test5()
# print(hh)










# zo = 'fcn.1400117f3'
# print(hxconverter(zo))







# def incidence_matr_gen2(path):
#     with open(path, 'r') as f:
#         text = f.read()
#         data = json.loads(text)
#
#     l = len(data)
#     matr = np.zeros([l+1, l+1], dtype='object')
#
#     for c in range(1, l+1):
#         matr[0][c] = data[c-1]["name"]
#         matr[c][0] = data[c-1]["name"]
#
#     for f in range(1, l+1):
#         for f2 in range(0, l):
#             if matr[f][0] == data[f2]["name"]:
#                 continue
#
#             p = data[f2]["name"]
#             q = data[f-1]["imports"]
#             if p in q:
#                 matr[f][f2+1] = 1
#     return matr
