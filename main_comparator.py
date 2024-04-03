from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os


def similarity(cfg1, cfg2):
    # print("1.op_parser")
    op1 = op_parser(cfg1)
    op2 = op_parser(cfg2)

    rename_op2 = rename_block(op1, op2)
    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
    h = hemming(umatrix1, umatrix2)
    return h

print("hemming:")
sim = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')
print(sim)
# similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778762.txt')

simus = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778817.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778922.txt')
print('  simus: ', simus)


def compare_files_in_directory(directory1, directory2):
    # Получаем список файлов в папке directory
    files1 = [f for f in os.listdir(directory1) if f.endswith('.txt')]
    files2 = [f for f in os.listdir(directory2) if f.endswith('.txt')]

    # Сравниваем все файлы попарно
    for i in range(len(files1)):
        for j in range(len(files2)):
            file1_path = os.path.join(directory1, files1[i])
            file2_path = os.path.join(directory2, files2[j])
            with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
                sim = similarity(file1_path, file2_path)
                print(f"Хеммингово расстояние между {files1[i]} и {files2[j]}: {round(sim,4)}")


compare_files_in_directory('F:\programming 2024\Sci_Research\cfg', 'F:\programming 2024\Sci_Research\cfg2')

















# print(find_similar_blocks(op1, op2))
# print("matrix 1:")
# matrix1 = create_matrix(b_links1)
# print(matrix1)
# print("matrix 2:")
# matrix2 = create_matrix(b_links2)
# print(matrix2)