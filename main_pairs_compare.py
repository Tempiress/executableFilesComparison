import json
from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os
from main_comparator import similarity
from progress.bar import Bar


def main_compare(folder1, folder2):
    # Создание списка файлов для каждой папки
    P1 = os.listdir(folder1)
    P2 = os.listdir(folder2)

    Pairs = []

    for file1 in P1:
        for file2 in P2:
            Pairs.append([file1, file2])

    PairWithSim = []
    for f, g in Pairs:
        join = f + '_' + g
        PairWithSim.append({"pair:": join,
                            "sim": similarity(f, g),
                            "num_block_in_fird": n1,
                            "num_block_in_second":
                            })
    # for file1 in P1:
    #     max_similarity = 0
    #     most_similar_file2 = ''
    #     path1 = os.path.join(folder1, file1)
    #     for file2 in P2:
    #         path2 = os.path.join(folder2, file2)
    #         sim, diff = max_similarity(path1, path2)
    #         if sim > max_similarity:
    #             max_similarity = sim
    #             most_similar_file2 = file2
    #     if most_similar_file2:
    #         Pairs.append()

folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'
mc = main_compare(folder1, folder2)