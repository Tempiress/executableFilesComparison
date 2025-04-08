import glob
import os
import time

from cfg_from_exe_generator import call_func_graph, create_cfgs_from_exe
from cfglinks_partition import links_two_program
from memory_cfg_from_exe_generator import CFGAnalyzer
from similarity import hemming_prog
import asyncio


async def deletefiles(dir):
    files = glob.glob((os.path.join(dir, '*')))

    # Удаление каждого файла
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
            # print(f"Deleted file: {file}") # Для отладки очищения файлов рабочих директорий
        else:
            print(f"skip dir: {file}")


async def run(p1, p2):
    # print("Compare two programs:" + p1 + " " + p2)
    # 1. Создание папок с CFG файлами с помощью Radare2
    # workdir1 = ".\\cfg1\\"
    # workdir2 = ".\\cfg2\\"
    # await deletefiles(workdir1)
    # await deletefiles(workdir2)
    # await create_cfgs_from_exe(p1, workdir1)
    # await create_cfgs_from_exe(p2, workdir2)

    cfga = CFGAnalyzer()
    p1_funcs = await cfga.analyze_executable(p1)
    p2_funcs = await cfga.analyze_executable(p2)

    # Создание файла связей блоков (Imports)

    lks1 = await cfga.get_call_graph(p1)
    lks2 = await cfga.get_call_graph(p1)

    matrix1, matrix2 = links_two_program(p1_funcs, p2_funcs, lks1, lks2)
    # u = hemming_prog(matrix1, matrix2)

    if len(matrix1) < len(matrix2):
        hh = hemming_prog(matrix1, matrix2, max(len(matrix1), len(matrix2)), p1_funcs, p2_funcs)
    else:
        hh = hemming_prog(matrix2, matrix1, max(len(matrix1), len(matrix2)), p1_funcs, p2_funcs)

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

start_time = time.time()

q = asyncio.run(run("./coreutils-polybench-hashcat/c08/O0/expander", "./coreutils-polybench-hashcat/c08/O2/expander"))
print("Resultss:", round(q, 4))

end_time = time.time()
print(end_time - start_time)
