from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from main_comparator import similarity
from linkMatrix import *
import os


print("hemming:")
#sim = similarity('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')
#print(sim)
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


# compare_files_in_directory('D:\MyNauchWork\cfg')