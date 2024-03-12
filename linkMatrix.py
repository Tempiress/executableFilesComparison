from blocklinks4 import *
from renamefile import *
import json


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


def create_matrix2(json_data1, json_data2):
    """
    Генерация матрицы
    :param json_data1, json_data2:
    :return:
    """

    data1 = json.loads(json_data1)
    data2 = json.loads(json_data2)
    size_matrix = max(len(data1), len(data2))+2

    matrix1 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data1.items():
        matrix1[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1

    matrix2 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data2.items():
        matrix2[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1

    return matrix1, matrix2


def hemming(matrix1, matrix2):
    size_matrix = len(matrix1)

    difference_count = 0
    for i in range(size_matrix):
        for j in range(size_matrix):
            if matrix1[i][j] != matrix2[i][j]:
                difference_count += 1

    return difference_count / (size_matrix * size_matrix)


# print(create_matrix('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt'))