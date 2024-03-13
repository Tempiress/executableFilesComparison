import json
from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os
from new_try import similarity
from progress.bar import Bar
from progress.spinner import Spinner


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
        join = f + ':' + g
        ssim, lndf = similarity(os.path.join(folder1, f), os.path.join(folder2, g))
        lf = lndf[0]
        lg = lndf[1]

        PairWithSim.append({"pair:": join,
                            "sim": ssim,
                            "num_block_in_fird": lf,
                            "num_block_in_second": lg
                            })
        print(PairWithSim)


    # II

    counter = 0
    p1_nodes = []
    p2_nodes = []

    #Цикл по короткому из списков функций (P1 или P2)
    min_len_p = min(len(P1), len(P2))
    if(min_len_p == len(P1)):
        arr_wit_min_len_p = P1
    for short_p in range(min_len_p):
        max_sim = float('-inf')
        max_sim_element = None

        #Цикл по всем парам с sim
        for pr in PairWithSim:
            if pr["pair"] ==  and pr["sim"]> max_sim:
                max_sim = pr["sim"]
                max_sim_element = pr


        el = PairWithSim[1]
        p1_nodes.append({"new_label": counter,
                         "old_label": str.split(":", el["pair"].split(":")[0])
                         })
        p2_nodes.append({"new_label": counter,
                         "old_label": el["pair"].split(":")[1]
                        })


        for pws in PairWithSim:
            if(pws["pair"].split(":")[0]) == el["pair"].split(":")[0]:
                PairWithSim.remove(pws)
                P1.remove(el["pair"].split(":")[0])
                continue

            if(pws["pair"].split(":")[1]) == el["pair"].split(":")[1]:
                PairWithSim.remove(pws)
                P2.remove(el["Pair"].split(":")[1])

        counter += 1


folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'
mc = main_compare(folder1, folder2)










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