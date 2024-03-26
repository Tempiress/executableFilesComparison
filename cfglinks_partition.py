import json
import os
from opcodeparser import *
import numpy as np
from main_pairs_compare import main_compare
from progress.bar import Bar


def hxconverter(num):
    nm = int(num[4:], 16)
    result = "cfg_" + str(nm) + ".txt"
    return result

def hxconverter2(num):
    nm = int(num[4:-4])
    nm = hex(nm)
    result = "fcn." + str(nm[2:])
    return result


#Поменять местами два столбца
def swap_columns(matrix, col1, col2):
    for row in matrix:
        row[col1], row[col2] = row[col2], row[col1]


def cfglinks_partition(path):
    with open(path, 'r') as f:
        text = f.read()
        data = json.loads(text)

    l = len(data)
    matr = np.zeros([l+1, l+1], dtype='object')

    for c in range(1, l+1):
        matr[0][c] = data[c-1]["name"]
        matr[c][0] = data[c-1]["name"]
    print(matr)

    for f in range(1, l+1):
        for f2 in range(0, l):
            if matr[f][0] == data[f2]["name"]:
                continue

            p = data[f2]["name"]
            q = data[f-1]["imports"]
            if p in q:
                matr[f][f2+1] = 1
    return matr


def links_two_program(path_cfg1, path_cfg2, label_map_path):
    matrix1 = cfglinks_partition(label_map_path)
    p1_nodes, p2_nodes = main_compare(path_cfg1, path_cfg2)

    #q = np.where(matrix1[0] == 'fcn.1400114ce')[0][0]

    bar = Bar('Processing', max=len(p1_nodes))
    for p1_node in p1_nodes:
        p1_node['new_label'] + 1 # Потому что матрица сдвинута
        if hxconverter2(p1_node['old_label']) in matrix1[0]:
            col_index = np.where(matrix1[0] == hxconverter2(p1_node['old_label']))[0][0]
            if col_index != p1_node['new_label']:
                swap_columns(matrix1, col_index, p1_node['new_label'] + 1)
        bar.next()
    bar.finish()
    return matrix1

# main--------------------------------------------------

folder1 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg'
folder2 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg2'
cfglinks_path = "cfgcflinks.txt"
matrix1 = cfglinks_partition(cfglinks_path)
matrix11 = links_two_program(folder1, folder2, cfglinks_path)

print("Done!")



#zo = 'fcn.1400117f3'
#print(hxconverter(zo))