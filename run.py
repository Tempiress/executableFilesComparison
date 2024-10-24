from cfg_from_exe_generator import call_func_graph, create_cfgs_from_exe
from linkMatrix import hemming_prog
from cfglinks_partition import links_two_program, pad_matrix, hemming_prog
import os
import glob


def deletefiles(dir):
    files = glob.glob((os.path.join(dir, '*')))

    #Удаление каждого файла
    for file in files:
        if os.path.isfile(file):
            #print(file)
            #input('Y?')
            os.remove(file)
            print(f"Deleted file: {file}")
        else:
            print(f"skip dir: {file}")


def run(p1, p2):

    workdir1 = ".\\lcfg\\"
    workdir2 = ".\\lcfg2\\"
    deletefiles(workdir1)
    deletefiles(workdir2)
    create_cfgs_from_exe(p1, workdir1)
    create_cfgs_from_exe(p2, workdir2)

    cfglinks_path1 = ".\\lks1.txt"
    cfglinks_path2 = ".\\lks2.txt"
    call_func_graph(p1, cfglinks_path1)
    call_func_graph(p2, cfglinks_path2)

    matrix1, matrix2 = links_two_program(workdir1, workdir2, cfglinks_path1, cfglinks_path2)
    matrix1, matrix2 = pad_matrix(matrix1, matrix2)
    hh = hemming_prog(matrix1, matrix2)
    return hh


#p1 = input("Program 1: ")
#p2 = input("Program 2: ")
#print("\n similarity of this programs is:", run(p1, p2))
# run(".\\HW8.exe", ".\\HW3.exe")

