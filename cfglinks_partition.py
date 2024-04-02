import copy
import json
import os
from opcodeparser import *
import numpy as np
from main_pairs_compare import main_compare
from progress.bar import Bar
from cfg_from_exe_generator import call_func_graph


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

def swap_rows(matrix, row1, row2):
    m1 = matrix[row2]
    c = copy.copy(matrix[row1])
    matrix[row1] = m1
    matrix[row2] = c




def cfglinks_partition(path):
    with open(path, 'r') as f:
        text = f.read()
        data = json.loads(text)

    l = len(data)
    matr = np.zeros([l+1, l+1], dtype='object')

    for c in range(1, l+1):
        matr[0][c] = data[c-1]["name"]
        matr[c][0] = data[c-1]["name"]


    for f in range(1, l+1):
        for f2 in range(0, l):
            if matr[f][0] == data[f2]["name"]:
                continue

            p = data[f2]["name"]
            q = data[f-1]["imports"]
            if p in q:
                matr[f][f2+1] = 1
    return matr


def links_two_program(path_cfg1, path_cfg2, label_map_path1, label_map_path2):
    matrix1 = cfglinks_partition(label_map_path1)
    matrix2 = cfglinks_partition(label_map_path2)
    p1_nodes, p2_nodes = main_compare(path_cfg1, path_cfg2)

    for p1_node in p1_nodes:
        p1_node['new_label'] + 1 # Потому что матрица сдвинута
        if hxconverter2(p1_node['old_label']) in matrix1[0]:
            col_index = np.where(matrix1[0] == hxconverter2(p1_node['old_label']))[0][0]
            if col_index != p1_node['new_label']:
                swap_columns(matrix1, col_index, p1_node['new_label'] + 1)
                swap_rows(matrix1, col_index, p1_node['new_label'] + 1)

    for p2_node in p2_nodes:
        p2_node['new_label'] + 1 # Потому что матрица сдвинута
        if hxconverter2(p2_node['old_label']) in matrix2[0]:
            col_index = np.where(matrix2[0] == hxconverter2(p2_node['old_label']))[0][0]
            if col_index != p2_node['new_label']:
                swap_columns(matrix2, col_index, p2_node['new_label'] + 1)
                swap_rows(matrix2, col_index, p2_node['new_label'] + 1)


    #bar.finish()
    return matrix1, matrix2

# main--------------------------------------------------

#folder1 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg'
#folder2 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg2'
#folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
#folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'

folder1 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg'
folder2 = 'F:\\programming 2024\\Sci_Research\\TestSets2\\cfg'


call_func_graph("F:\\programming 2024\\Sci_Research\\HW8.exe", "F:\\programming 2024\\Sci_Research\\HW8_cfgcflinks.txt")

cfglinks_path = "cfgcflinks.txt"
cfglinks_path2 = "HW8_cfgcflinks.txt"

#matrix1, matrix2 = links_two_program(folder1, folder2, cfglinks_path, cfglinks_path2)
matrix1, matrix2 = links_two_program(folder1, folder1, cfglinks_path, cfglinks_path)

print("Done!")



#zo = 'fcn.1400117f3'
#print(hxconverter(zo))