import glob
import os
from cfg_from_exe_generator import call_func_graph, create_cfgs_from_exe
from cfglinks_partition import links_two_program
from similarity import hemming_prog


def deletefiles(dir):
    files = glob.glob((os.path.join(dir, '*')))

    # Удаление каждого файла
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
            # print(f"Deleted file: {file}") # Для отладки очищения файлов рабочих директорий
        else:
            print(f"skip dir: {file}")


def run(p1, p2):
    a = '4203440;'
    b = a.rstrip(";")
    print("Compare two programs:" + p1 + " " + p2)
    # 1. Создание папок с CFG файлами с помощью Radare2
    workdir1 = ".\\cfg1\\"
    workdir2 = ".\\cfg2\\"
    deletefiles(workdir1)
    deletefiles(workdir2)
    create_cfgs_from_exe(p1, workdir1)
    create_cfgs_from_exe(p2, workdir2)

    # Создание файла связей блоков (Imports)
    cfglinks_path1 = ".\\lks1.txt"
    cfglinks_path2 = ".\\lks2.txt"
    call_func_graph(p1, cfglinks_path1)
    call_func_graph(p2, cfglinks_path2)

    matrix1, matrix2 = links_two_program(workdir1, workdir2, cfglinks_path1, cfglinks_path2)
    # u = hemming_prog(matrix1, matrix2)

    if len(matrix1) < len(matrix2):
        hh = hemming_prog(matrix1, matrix2, max(len(matrix1), len(matrix2)), workdir1, workdir2)
    else:
        hh = hemming_prog(matrix2, matrix1, max(len(matrix1), len(matrix2)), workdir2, workdir1)

     # matrix1, matrix2 = pad_matrix(matrix1, matrix2)
     # hh = hemming_prog(matrix1, matrix2)
    return hh


# JsonHemmingPair(".\pairsComparison\similar_pairs.json", ".\pairsComparison\sim_p_with_hemming.json")
# JsonHemmingPair(".\pairsComparison\different_pairs.json", ".\pairsComparison\diff_p_with_hemming.json")
# q = run(".\\coreutils-polybench-hashcat\\aoc\\O0\\covariance", ".\\coreutils-polybench-hashcat\\aoc\\O0\\combinator")
# q = run(".\\coreutils-polybench-hashcat\\c07\\O0\\bicg", ".\\coreutils-polybench-hashcat\\c07\\O0\\dirname")
# q = run(".\\coreutils-polybench-hashcat\\aoc\\O0\\cutb", ".\\coreutils-polybench-hashcat\\aoc\\O2\\cutb")
# q = run(".\\coreutils-polybench-hashcat\\c09\\O0\\cap2hccapx", ".\\coreutils-polybench-hashcat\\c09\\O0\\ct3_to_ntlm")
# q = run(".\\coreutils-polybench-hashcat\\aoc\O0\\expander", ".\\coreutils-polybench-hashcat\\c08\\O2\\chmod")
# q = run("HW3.exe", ".\\HW8.exe")

# print("Result:", round(q, 4))

