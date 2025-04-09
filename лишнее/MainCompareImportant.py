import os
from similarity import similarity
from progress.bar import Bar


def important_main_compare(folder1, folder2):
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

    # P1_files_temp = copy.copy(P1_files)
    # P2_files_temp = copy.copy(P2_files)
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
        bar.next()
    bar.finish()
    # ff.close()

    return p1_nodes, p2_nodes

# folder1 = 'D:\\programming2024\\MyResearch\\TestSets\\cfg'
# folder2 = 'D:\\programming2024\\MyResearch\\TestSets\cfg2'
# important_main_compare(folder1, folder2)
