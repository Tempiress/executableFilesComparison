import copy
from linkMatrix import *
import os
from similarity import similarity
from progress.bar import Bar


def main_compare8(folder1, folder2, matrix1, matrix2):
    # Создание списка файлов для каждой папки
    # P1 = os.listdir(folder1)
    # P2 = os.listdir(folder2)
    Pairs = []
    _P1_files = {file: os.path.join(folder1, file) for file in os.listdir(folder1)}
    _P2_files = {file: os.path.join(folder2, file) for file in os.listdir(folder2)}

    P1_files = {}
    for file in range(1, len(matrix1[0])):
        P1_files[matrix1[0][file]] = os.path.join(folder1, matrix1[0][file] + ".txt")

    P2_files = {}
    for file2 in range(1, len(matrix2[0])):
        P2_files[matrix2[0][file2]] = os.path.join(folder2, matrix2[0][file2] + ".txt")


    for file1 in P1_files:
        for file2 in P2_files:
            Pairs.append([file1, file2])

    ff = open('./Debug/twoFuncDebug/res.txt', 'w')
    PairWithSim = []
    bar = Bar('Processing', max=len(P1_files))
    for f, g in Pairs:
        join = f + ':' + g
        o1 = os.path.join(folder1, f + '.txt')
        o2 = os.path.join(folder2, g + '.txt')
        ssim, lndf = similarity(o1, o2)
        lf = lndf[0]
        lg = lndf[1]

        PairWithSim.append({"pair": join,
                            "sim": ssim,
                            "num_block_in_first": lf,
                            "num_block_in_second": lg
                            })

    # ff.write(str(PairWithSim))
    k = 1
    for p in PairWithSim:
        ff.write(str(k) + ". " + str(p["pair"]) + "   --->   " + str(p["sim"]) + "\n")
        k += 1


    ff.close()
    # II
    counter = 0
    p1_nodes = []
    p2_nodes = []

    # Цикл по короткому из списков функций (P1 или P2)
    min_len_p = min(len(P1_files), len(P2_files))
    index_of_short = -1
    if(min_len_p == len(P1_files)):
        arr_with_min_len_p = P1_files
        index_of_short = 0
    else:
        arr_with_min_len_p = P2_files
        index_of_short = 1


    for short_p in arr_with_min_len_p:
        max_sim = float('inf')
        max_sim_element = None
        bar.next()
        TempPairs = []
        # Цикл по всем парам с sim
        for pr in PairWithSim:
            if pr["pair"].split(":")[index_of_short] == short_p and pr["sim"] < max_sim:
                max_sim = pr["sim"]
                max_sim_element = pr
                if(pr["sim"] == 0):
                    TempPairs.append(pr)

        el = max_sim_element  # PairWithSim[1]
        p1_nodes.append({"new_label": counter,
                        "old_label": el["pair"].split(":")[0]
                        })
        p2_nodes.append({"new_label": counter,
                        "old_label": el["pair"].split(":")[1]
                        })

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

def main_compare(folder1, folder2, matrix1, matrix2):
    # Создание списка файлов для каждой папки
    P1_files = {}
    for file in range(1, len(matrix1[0])):
        P1_files[matrix1[0][file]] = os.path.join(folder1, matrix1[0][file] + ".txt")

    P2_files = {}
    for file2 in range(1, len(matrix2[0])):
        P2_files[matrix2[0][file2]] = os.path.join(folder2, matrix2[0][file2] + ".txt")

    # Генерация всех возможных пар
    Pairs = []
    for file1 in P1_files:
        for file2 in P2_files:
            Pairs.append((file1, file2))

    # Сравнение всех пар
    PairWithSim = []
    for f, g in Pairs:
        o1 = os.path.join(folder1, f + '.txt')
        o2 = os.path.join(folder2, g + '.txt')
        ssim, lndf = similarity(o1, o2)
        PairWithSim.append({
            "pair": (f, g),
            "sim": ssim,
            "num_block_in_first": lndf[0],
            "num_block_in_second": lndf[1]
        })

    ff = open('./Debug/twoFuncDebug/res.txt', 'w')
    k = 1
    for p in PairWithSim:
        ff.write(str(k) + ". " + str(p["pair"]) + "   --->   " + str(p["sim"]) + "\n")
        k += 1
    ff.close()

    # Сортировка пар по убыванию схожести
    PairWithSim.sort(key=lambda x: x["sim"], reverse=True)

    # Выбор оптимальных пар
    used_p1 = set()
    used_p2 = set()
    p1_nodes = []
    p2_nodes = []
    counter = 0

    for pair in PairWithSim:
        f, g = pair["pair"]
        if f not in used_p1 and g not in used_p2:
            p1_nodes.append({
                "new_label": counter,
                "old_label": f
            })
            p2_nodes.append({
                "new_label": counter,
                "old_label": g
            })
            used_p1.add(f)
            used_p2.add(g)
            counter += 1

    return p1_nodes, p2_nodes





# OriginalSet
# folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
# folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'

# TestSet
# folder1 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg'
# folder2 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg2'
# mc = main_compare(folder1, folder2)

# print(mc)

def hxconverter(num):
    nm = int(num[4:], 16)
    result = "cfg_" + str(nm) + ".txt"
    return result


def important_main_compare(folder1, folder2, matrix1, matrix2 ):
    print("Процесс создания словарей файлов для каждой папки")
    P1_files = {file: os.path.join(folder1, file) for file in os.listdir(folder1)}
    P2_files = {file: os.path.join(folder2, file) for file in os.listdir(folder2)}

    # P1_files = {}
    # for file in range(1, len(matrix1[0])):
     # P1_files[matrix1[0][file]] = os.path.join(folder1, matrix1[0][file] + ".txt")

    # P2_files = {}
    # for file2 in range(1, len(matrix2[0])):
     # P2_files[matrix2[0][file2]] = os.path.join(folder2, matrix2[0][file2] + ".txt")

    # Сортируем файлы по ключам
    sorted_P1_files = dict(sorted(P1_files.items(), key=lambda x: x[0]))
    sorted_P2_files = dict(sorted(P2_files.items(), key=lambda x: x[0]))

    P1_files_temp = copy.copy(P1_files)
    P2_files_temp = copy.copy(P2_files)
    print("Длина словаря P1 =>", len(P1_files))
    print("Длина словаря P2 =>", len(P2_files))

    p1_nodes = []
    p2_nodes = []
    print("Создание массивов меток....")
    bar = Bar('Processing', max=len(P1_files))
    # ff = open('result.txt', 'w')

    for file1, path1 in sorted_P1_files.items():
        max_sim = float('inf')
        max_sim_element = None

        for file2, path2 in sorted_P2_files.items():
            ssim, lndf = similarity(path1, path2)
            # print("file1 = ", file1, "file2 = ", file2, "Result = ", ssim)
            # ff.write(" file1 = " + file1 + " file2 = " + file2 + " Result = " + str(ssim) + "\n")
            if ssim < max_sim:
                max_sim = ssim
                max_sim_element = {"pair": f"{file1}:{file2}", "sim": ssim, "num_block_in_third": lndf[0], "num_block_in_second": lndf[1]}
        if max_sim_element:
            p1_nodes.append({"new_label": len(p1_nodes), "old_label": max_sim_element["pair"].split(":")[0]})
            p2_nodes.append({"new_label": len(p2_nodes), "old_label": max_sim_element["pair"].split(":")[1]})
            del P1_files_temp[max_sim_element["pair"].split(":")[0]]
            del P2_files_temp[max_sim_element["pair"].split(":")[1]]
        bar.next()
    bar.finish()
    # ff.close()

    return p1_nodes, p2_nodes





#fold1 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg'
#fold2 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg2'
#pn1, pn2 = important_main_compare(fold1, fold2, fold1, fold1)