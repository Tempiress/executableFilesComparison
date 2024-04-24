import json
from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os
from progress.bar import Bar


def similarity(cfg1, cfg2):
    op1 = op_parser(cfg1)
    op2 = op_parser(cfg2)

    rename_op2, diff = rename_block(op1, op2)

    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)

    h = hemming(umatrix1, umatrix2)

    return h, diff


def compare_files(folder1, folder2):
    # Создание списка файлов для каждой папки
    files1 = os.listdir(folder1)
    files2 = os.listdir(folder2)

    max_similarity_dict = {}
    bar = Bar('Processing', max=len(files1))
    for file1 in files1:
        bar.next()
        path1 = os.path.join(folder1, file1)
        if os.path.isfile(path1):
            max_similarity = 0
            most_similar_file2 = ''
            for file2 in files2:
                path2 = os.path.join(folder2, file2)
                if os.path.isfile(path2):
                    sim, diff = similarity(path1, path2)
                    if sim > max_similarity:
                        max_similarity = sim
                        most_similar_file2 = file2
            if most_similar_file2:
                max_similarity_dict[os.path.join(file1[:-4], "_", file2[:-4])] = {"max_similarity": round(max_similarity, 5),
                                          "similar_to": most_similar_file2,
                                          "diff": diff
                                                   }
                # files2.remove(most_similar_file2)

        with open('max_similarity.json', 'w') as f:
            json.dump(max_similarity_dict, f, indent=4)
        bar.finish()


# Пример использования функции
folder1 = 'F:\\programming 2024\\Sci_Research\\cfg'
folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'
# compare_files(folder1, folder2)
