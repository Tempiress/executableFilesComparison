import json
import os

import numpy as np

from blocklinks4 import *
from opcodeparser import *
from renamefile import *


def create_matrix2(json_data1, json_data2):
    """
    Генерация матрицы
    :param json_data1, json_data2:
    :return:
    """

    data1 = json.loads(json_data1)
    data2 = json.loads(json_data2)
    size_matrix = max(len(data1), len(data2)) + 2

    matrix1 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data1.items():
        matrix1[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1

    matrix2 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data2.items():
        matrix2[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1

    return matrix1, matrix2


def similarity(cfg1, cfg2):
    """
     Число Хемминга (0-идентич., 1- не иднетич.)
    :param: cfg1 cfg2
    :return: double, difference
    """
    op1 = op_parser(cfg1)
    op2 = op_parser(cfg2)

    data1 = json.loads(op1)
    data2 = json.loads(op2)
    sim_array = find_similar_blocks(op1, op2)
    rename_op2, diff = rename_block(data1, data2, sim_array)

    sim_dict = json.loads(sim_array)
    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    size_matrix0 = min(len(data1), len(data2)) + 1
    max_size_matrix = max(len(data1), len(data2)) + 1
    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
    size_matrix = len(umatrix1)

    A = 0
    B = 0

    try:
        keys = lambda _key: [key for key, value in sim_dict.items() if value.get("block") == _key]
    except Exception as ex:
        print("Error in keys:", ex)
    m = keys(str(1))
    # q = sim_dict[m[0]]
    try:
        sim = lambda i: 1 if len(keys(i)) > 0 and sim_dict[keys(i)[0]]["simequal"] == 1 else (sim_dict[keys(i)[0]]["simcount"]) / 100 if len(keys(i)) > 0 else 0
    except IndexError as ex:
        print(" Список keys(i) пуст. Проверьте данные в sim_dict.", ex)

    for i in range(1, size_matrix0):
        for j in range(1, size_matrix0):

            A0 = (sim(str(i)) + sim(str(j)))
            A += (1 ^ (umatrix1[i][j] ^ umatrix2[i][j])) * A0

    C = (float(A) / ((max_size_matrix - 1) * (max_size_matrix - 1) * 2))
    return C, diff


    # weighted hemming prog
    # return h, diff

# print("hemming:")
# sim = similarity('..\\cfg\\cfg_5368778762.txt', '..\\cfg\\cfg_5368778977.txt')
# print(sim)
# similarity('..\\cfg\\cfg_5368778762.txt', '..\\cfg\\cfg_5368778762.txt')

# simus = similarity('..\\cfg\\cfg_5368778817.txt', '..\\cfg\\cfg_5368778922.txt')


def create_matrix(json_data1):
    """
    Генерация матрицы
    :param json_data1:
    :return:
    """
    # dt = block_links(json_data1)
    data = json.loads(json_data1)
    size_matrix = len(data) + 2

    matrix = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data.items():
        matrix[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1

    return matrix



# def hemming(matrix1, matrix2):
#     size_matrix = len(matrix1)
#
#     difference_count = 0
#     for i in range(size_matrix):
#         for j in range(size_matrix):
#             if matrix1[i][j] != matrix2[i][j]:
#                 difference_count += 1
#
#     #return difference_count / (size_matrix * size_matrix)
#     return difference_count

def hemming_prog(matrix1, matrix2, maxlen, folder1, folder2):
    size_matrix = len(matrix1)
    # folder1 = ".\\cfg1\\"
    # folder2 = ".\\cfg2\\"
    difference_count = 0
    A = 0
    B = 0
    q = []
    for i in range(1, size_matrix):
        for j in range(1, size_matrix):
            # A0 = (similarity(matrix1[0][i], matrix2[0][j]) + similarity(matrix1[0][j], matrix2[0][i]))


            A0 = (similarity(os.path.join(folder1, matrix1[0][i] + ".txt"),
                             os.path.join(folder2, matrix2[0][i] + ".txt"))[0] + similarity(
                os.path.join(folder1, matrix1[0][j] + ".txt"), os.path.join(folder2, matrix2[0][j] + ".txt"))[0])

            A += (1 ^ (matrix1[i][j] ^ matrix2[i][j])) * A0

    # A0 = (similarity(os.path.join(folder1, matrix1[0][i] + ".txt"),os.path.join(folder1, matrix2[0][j] + ".txt")) + similarity(os.path.join(folder1, matrix1[0][j] + ".txt"),os.path.join(folder1, matrix2[0][i] + ".txt")))
    # os.path.join(folder1, matrix1[0][i] + ".txt")

    C = (float(A) / ((maxlen - 1) * (maxlen - 1) * 2))  #

    return C


# def hemming_prog(matrix1, matrix2):
#     size_matrix = len(matrix1)
#
#     difference_count = 0
#
#     for i in range(1, size_matrix):
#         for j in range(1, size_matrix):
#             if matrix1[i][j] == matrix2[i][j]:
#                 difference_count +=1
#
# return difference_count / ((size_matrix - 1) * (size_matrix - 1))


# print(create_matrix('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt'))
