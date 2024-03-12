import json
from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os
from progress.bar import Bar


def similarity(cfg1, cfg2):
    # print("1.op_parser")
    op1 = op_parser(cfg1)
    op2 = op_parser(cfg2)
    # print(op1, "\n")

    # print("2.rename_block")
    rename_op2 = rename_block(op1, op2)
    # print(rename_op2)
    # print("3.block_links: ")
    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    # print(b_links2)

    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
    # print("_______________union_matrix______________")
    # print(umatrix1)
    # print("\n")
    # print(umatrix2)

    # print("hemming:")
    h = hemming(umatrix1, umatrix2)
    #print(h)
    return h


def compare_files(folder1, folder2):
    files1 = os.listdir(folder1)
    files2 = os.listdir(folder2)

    max_similarity = 0
    most_similar_pair = {}

    bar = Bar('Processing', max=len(files1))
    f = open('most_similar_pair.json', 'w')

    for file1 in files1:
        bar.next()
        path1 = os.path.join(folder1, file1)
        if os.path.isfile(path1):
            for file2 in files2:
                path2 = os.path.join(folder2, file2)
                if os.path.isfile(path2):
                    sim = similarity(path1, path2)
                    if sim > max_similarity:
                        max_similarity = sim
                        most_similar_pair = {"file1": {"name": file1, "path": path1, "similarity": round(max_similarity, 3)}, "file2": {"name": file2, "path": path2}}


        json.dump(most_similar_pair, f, indent=4)
    f.close()
    bar.finish()


# Пример использования функции
folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'

#compare_files(folder1, folder2)


with open("tempfile.json", "r") as fi:
    q = json.load(fi)
    print(q)
    #print(q["file1"])


