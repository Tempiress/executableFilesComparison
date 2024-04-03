import copy

from linkMatrix import *
import os
from new_try import similarity
from progress.bar import Bar

def main_compare2(folder1, folder2):
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

        PairWithSim.append({"pair": join,
                            "sim": ssim,
                            "num_block_in_third": lf,
                            "num_block_in_second": lg
                            })
        #print(PairWithSim)

    # II
    counter = 0
    p1_nodes = []
    p2_nodes = []

    #Цикл по короткому из списков функций (P1 или P2)
    min_len_p = min(len(P1), len(P2))
    index_of_short = -1
    if(min_len_p == len(P1)):
        arr_with_min_len_p = P1
        index_of_short = 0
    else:
        arr_with_min_len_p = P2
        index_of_short = 1

    with open('p1_nodes.json', 'w') as f:
        for short_p in arr_with_min_len_p:
            max_sim = float('inf')
            max_sim_element = None

            #Цикл по всем парам с sim
            for pr in PairWithSim:
                if pr["pair"].split(":")[index_of_short] == short_p and pr["sim"] < max_sim:
                    max_sim = pr["sim"]
                    max_sim_element = pr


            el = max_sim_element #PairWithSim[1]
            p1_nodes.append({"new_label": counter,
                             "old_label": el["pair"].split(":")[0]
                             })
            p2_nodes.append({"new_label": counter,
                             "old_label": el["pair"].split(":")[1]
                            })

            json.dump(p1_nodes, f, indent=4)
            # for pws in PairWithSim:
            #     if(pws["pair"].split(":")[0]) == el["pair"].split(":")[0]:
            #         PairWithSim.remove(pws)
            #         # if(pws["pair"].split(":")[0] in P1):
            #         #     P1.remove(el["pair"].split(":")[0])
            #         continue
            #     if(pws["pair"].split(":")[1]) == el["pair"].split(":")[1]:
            #         PairWithSim.remove(pws)
            #         # if(pws["pair"].split(":")[1] in P2):
            #         #     P2.remove(el["pair"].split(":")[1])
            z = 0
            while z < len(PairWithSim):
                if (PairWithSim[z]["pair"].split(":")[0]) == el["pair"].split(":")[0]:
                    PairWithSim.remove(PairWithSim[z])
                    continue

                if(PairWithSim[z]["pair"].split(":")[1]) == el["pair"].split(":")[1]:
                    PairWithSim.remove(PairWithSim[z])
                    continue

                z += 1

            counter += 1
    return p1_nodes, p2_nodes
# OriginalSet
#folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
#folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'

# TestSet
#folder1 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg'
#folder2 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg2'
#mc = main_compare(folder1, folder2)

#print(mc)


def main_compare(folder1, folder2):
    # Создание словарей файлов для каждой папки
    print("Процесс создания словарей файлов для каждой папки")
    P1_files = {file: os.path.join(folder1, file) for file in os.listdir(folder1)}
    P2_files = {file: os.path.join(folder2, file) for file in os.listdir(folder2)}

    P1_files_temp = copy.copy(P1_files)
    P2_files_temp = copy.copy(P2_files)
    print("Длина словаря P1 =>", len(P1_files))
    print("Длина словаря P2 =>", len(P2_files))

    p1_nodes = []
    p2_nodes = []
    print("Создание массивов меток....")
    bar = Bar('Processing', max=len(P1_files))

    for file1, path1 in P1_files.items():
        max_sim = float('-inf')
        max_sim_element = None

        for file2, path2 in P2_files.items():
            ssim, lndf = similarity(path1, path2)

            if ssim > max_sim:
                max_sim = ssim
                max_sim_element = {"pair": f"{file1}:{file2}", "sim": ssim, "num_block_in_third": lndf[0], "num_block_in_second": lndf[1]}

        if max_sim_element:
            p1_nodes.append({"new_label": len(p1_nodes), "old_label": max_sim_element["pair"].split(":")[0]})
            p2_nodes.append({"new_label": len(p2_nodes), "old_label": max_sim_element["pair"].split(":")[1]})
            del P2_files[max_sim_element["pair"].split(":")[1]]  # Удаляем уже использованный файл из словаря
            del P1_files_temp[max_sim_element["pair"].split(":")[0]]
            del P2_files_temp[max_sim_element["pair"].split(":")[1]]
        bar.next()
    bar.finish()

    if len(P1_files_temp) != 0:
        for file, path in P1_files_temp.items():
            p1_nodes.append({"new_label": len(p1_nodes), "old_label": file})
    else:
        for file1, path in P2_files_temp.items():
            p2_nodes.append({"new_label": len(p2_nodes), "old_label": file1})

    return p1_nodes, p2_nodes

#fold1 = 'D:\\programming2024\\MyResearch\\testSets3\\cfg'
#fold2 = 'D:\\programming2024\\MyResearch\\testSets3\\cfg2'
#pn1, pn2 = main_compare(fold1, fold2)
#print('a')