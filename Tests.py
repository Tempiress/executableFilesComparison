import copy

from cfg_from_exe_generator import create_cfgs_from_exe, call_func_graph
from cfglinks_partition import links_two_program, pad_matrix
from similarity import hemming_prog


def Test1():
    folder1 = '.\\cfg1'
    folder2 = '.\\cfg2'

    cfglinks_path = "cfgcflinks.txt"
    cfglinks_path2 = "HW8_cfgcflinks.txt"

    matrix1, matrix2 = links_two_program(folder1, folder2, cfglinks_path, cfglinks_path2)
    matrix1, matrix2 = pad_matrix(matrix1, matrix2)
    hh = hemming_prog(matrix1, matrix2)
    print("Done!")
    return hh


def Test2():
    # call_func_graph(".\\C++programs\\OddChecker1.exe", ".\\C++programs\\OddChecker1_cfgcflinks.txt\\")
    # call_func_graph(".\\C++programs\\OddChecker_O1.exe", ".\\C++programs\\OddChecker_O1_cfgcflinks.txt\\")
    # Create clear program
    # create_cfgs_from_exe(".\\C++programs\\OddChecker1.exe", "F:\\programming 2024\\Sci_Research\\C++programs\\cfgs1\\")
    folder1 = 'F:\\programming 2024\\Sci_Research\\C++programs\\cfgs1\\'
    cfglinks_path = "F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker1_cfgcflinks.txt\\"

    # Create optimized O1 program
    # create_cfgs_from_exe(".\\Sci_Research\\C++programs\\OddChecker_O1.exe", ".\\C++programs\\cfgs2\\")
    folder2 = 'F:\\programming 2024\\Sci_Research\\C++programs\\cfgs2\\'
    cfglinks_path2 = "F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker_O1_cfgcflinks.txt\\"
    matrix1, matrix2 = links_two_program(folder1, folder2, cfglinks_path, cfglinks_path2)
    matrix1, matrix2 = pad_matrix(matrix1, matrix2)
    hh = hemming_prog(matrix1, matrix2)
    return hh


def Test3():
    # call_func_graph(".\\C++programs\\OddChecker1.exe", ".\\C++programs\\OddChecker1_cfgcflinks.txt\\")
    # Create clear program
    # create_cfgs_from_exe("F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker1.exe", ".\\C++programs\\cfgs1\\")
    folder1 = '.\\C++programs\\cfgs1'
    cfglinks_path = ".\\C++programs\\OddChecker1_cfgcflinks.txt"


    matrix1, matrix2 = links_two_program(folder1, folder1, cfglinks_path, cfglinks_path)
    # matrix1, matrix2 = pad_matrix(matrix1, matrix2)
    hh = hemming_prog(matrix1, matrix2)
    return hh


def Test4():
    folder1 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg1'
    folder2 = 'F:\\programming 2024\\Sci_Research\\TestSets\\cfg2'
    cfglinks_path = "F:\\programming 2024\\Sci_Research\\C++programs\\OddChecker1_cfgcflinks.txt"
    matrix1, matrix2 = links_two_program(folder1, folder1, cfglinks_path, cfglinks_path)
    # matrix1, matrix2 = pad_matrix(matrix1, matrix2)
    hh = hemming_prog(matrix1, matrix2)
    return hh


def Test5():
    folder1 = 'F:\\programming 2024\\Sci_Research\\cfg1'
    folder2 = 'F:\\programming 2024\\Sci_Research\\cfg2'
    # Create clear program
    create_cfgs_from_exe(".\\HW8.exe", ".\\cfg1\\")
    create_cfgs_from_exe(".\\HW3.exe", ".\\cfg2\\")

    call_func_graph(".\\HW8.exe", ".\\a.txt")
    call_func_graph(".\\HW3.exe", ".\\b.txt")

    cfglinks_path1 = ".\\a.txt"
    cfglinks_path2 = ".\\b.txt"

    matrix1, matrix2 = links_two_program(folder1, folder2, cfglinks_path1, cfglinks_path2)
    matrix1, matrix2 = pad_matrix(matrix1, matrix2)
    hh = hemming_prog(matrix1, matrix2)
    return hh