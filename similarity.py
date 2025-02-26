from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os


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
    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
    size_matrix = len(umatrix1)

    A = 0
    B = 0

    keys = lambda _key: [key for key, value in sim_dict.items() if value.get("block") == _key]
    m = keys(str(1))
    q = sim_dict[m[0]]
    sim = lambda i: 1 if sim_dict[keys(i)[0]]["simequal"] == 1 else (sim_dict[keys(i)[0]]["simcount"]) / 100


    for i in range(1, size_matrix0):
        for j in range(1, size_matrix0):

            A0 = (sim(str(i)) + sim(str(j)))
            A += (1 ^ (umatrix1[i][j] ^ umatrix2[i][j])) * A0

    C = (float(A) / ((size_matrix0 - 1) * (size_matrix0 - 1) * 2))
    return C, diff



    # weighted hemming prog
    # return h, diff



# print("hemming:")
# sim = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')
# print(sim)
# similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778762.txt')

# simus = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778817.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778922.txt')
# print('  simus: ', simus)
