from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from linkMatrix import *
import os

def similarity(cfg1, cfg2):
    #print("1.op_parser")
    op1 = op_parser(cfg1)
    op2 = op_parser(cfg2)
    #print(op1, "\n")

    #print("2.rename_block")
    rename_op2 = rename_block(op1, op2)
    #print(rename_op2)
    #print("3.block_links: ")
    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    #print(b_links2)

    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
    #print("_______________union_matrix______________")
    #print(umatrix1)
    #print("\n")
    #print(umatrix2)

    #print("hemming:")
    h = hemming(umatrix1, umatrix2)
    #print(h)
    return h

print("hemming:")
sim = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')
print(sim)
#similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778762.txt')

simus = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778817.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778922.txt')
print('  simus: ', simus)
def compare_files_in_directory(directory):
    # Получаем список файлов в папке directory
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]

    # Сравниваем все файлы попарно
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            file1_path = os.path.join(directory, files[i])
            file2_path = os.path.join(directory, files[j])
            with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
                sim = similarity(file1_path, file2_path)
                print(f"Хэммингово расстояние между {files[i]} и {files[j]}: {sim}")


compare_files_in_directory('D:\MyNauchWork\cfg')

















# print(find_similar_blocks(op1, op2))
# print("matrix 1:")
# matrix1 = create_matrix(b_links1)
# print(matrix1)
# print("matrix 2:")
# matrix2 = create_matrix(b_links2)
# print(matrix2)