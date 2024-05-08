from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os


def similarity(cfg1, cfg2):
    """
     Число Хемминга (0-идентич., 1- не иднетич.)
    :param: cfg1 cfg2
    :return: double
    """
    # print("1.op_parser")
    op1 = op_parser(cfg1)
    op2 = op_parser(cfg2)

    rename_op2 = rename_block(op1, op2)
    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
    h = hemming(umatrix1, umatrix2)
    return h

#print("hemming:")
#sim = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')
#print(sim)
# similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778762.txt')

#simus = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778817.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778922.txt')
#print('  simus: ', simus)