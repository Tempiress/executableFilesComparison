import glob
import os
import time
import tlsh
import ppdeep
import concurrent.futures
import datetime
from cfg_from_exe_generator import call_func_graph, create_cfgs_from_exe
from cfglinks_partition import links_two_program
from memory_cfg_from_exe_generator import CFGAnalyzer
from similarity import hemming_prog
import asyncio
from config import AnalysisConfig
import subprocess
import sys
import re
import random
import torch
import numpy as np


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


set_seed(42)

def deletefiles(dir):
    files = glob.glob((os.path.join(dir, '*')))

    # Удаление каждого файла
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
            # print(f"Deleted file: {file}") # Для отладки очищения файлов рабочих директорий
        else:
            print(f"skip dir: {file}")



def cfg_adder(call_graph, p_funcs):
    exiting_names = {func["name"] for func in call_graph}

    for p_func in p_funcs.values():
        pfunc_name = p_func['cfg'][0]['name']
        if pfunc_name not in exiting_names:
            new_item = {
                "name": p_func["name"],
                "size": p_func["cfg"][0]["size"],
                "imports": {}
            }
            call_graph.append(new_item)
            exiting_names.add(pfunc_name)

    return call_graph


def run(p1, p2, config):

    print("Compare two programs:" + p1 + " " + p2)
    # 1. Создание папок с CFG файлами с помощью Radare2
    cfg_analyzer = CFGAnalyzer()
    print("Analyze Executable...")
    print("Analyze Executable p1...")
    p1_funcs = cfg_analyzer.analyze_executable(p1)
    print("Analyze Executable p2...")
    p2_funcs = cfg_analyzer.analyze_executable(p2)

    print("get call graphs...")
    # Создание файла связей блоков (Imports)
    lks1 = cfg_analyzer.get_call_graph(p1)
    lks2 = cfg_analyzer.get_call_graph(p2)

    # Создание файла связей блоков (Imports)
    lks1 = cfg_adder(cfg_analyzer.get_call_graph(p1), p1_funcs)
    lks2 = cfg_adder(cfg_analyzer.get_call_graph(p2), p2_funcs)

    matrix1, matrix2 = links_two_program(p1_funcs, p2_funcs, lks1, lks2, config=config)

    if len(matrix1) < len(matrix2):
        hh = hemming_prog(matrix1, matrix2, max(len(matrix1), len(matrix2)), p1_funcs, p2_funcs, config=config)
    else:
        hh = hemming_prog(matrix2, matrix1, max(len(matrix1), len(matrix2)), p2_funcs, p1_funcs, config=config)

    return hh




def run_asm2vec_comparison(exe_path1, exe_path2):
    # 1. Путь к Python в виртуальном окружении с PyTorch
    venv_python = r"H:\ResearchWorkCUDA\venv2\Scripts\python.exe"

    # 2. Путь к скрипту сравнения
    script_path = r"H:\ResearchWorkCUDA\asm2vec-pytorch-master\compare_full_binaries.py"
    # 3. Путь к модели
    model_path = r"H:\ResearchWorkCUDA\asm2vec-pytorch-master\model_optim.pt"

    cmd = [
        venv_python,
        script_path,
        "--bin1", exe_path1,
        "--bin2", exe_path2,
        "--model", model_path
    ]


    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        output = result.stdout
        return output
    except subprocess.SubprocessError as e:
        print(f"Ошибка при запуске скрипта: {e}")
        return 0.0


if __name__ == '__main__':
     start = datetime.datetime.now()

     obf_p1 = "H:/programming2026/ResearchWorkCUDA/all_obf/3mm"


     p1 = "./coreutils-polybench-hashcat/aoc/O0/3mm"
     p2 = "./coreutils-polybench-hashcat/g10/O2/3mm"
     p2 = "./coreutils-polybench-hashcat/aoc/O2/3mm"


     p_cp1 = "./coreutils-polybench-hashcat/aoc/O0/combinatorX"
     p_cp2 = "./coreutils-polybench-hashcat/aoc/O2/combinatorX"

     exe1 = r"H:\ResearchWorkCUDA\asm2vec-pytorch-master\pycharm64.exe"
     exe2 = r"H:\ResearchWorkCUDA\asm2vec-pytorch-master\Cleanmgr+.exe"


     p5 = "./coreutils-polybench-hashcat/g10/O2/wc"
     p6 = "./coreutils-polybench-hashcat/aoc/O2/wc"
     #score = run_asm2vec_comparison(p1, p2)

     #print(f"{'-' * 10}\n Asm2vecCuda resut:\n{score}{'-'* 10}")
     #cfg1 = AnalysisConfig(hash_type='nilsimsa', instructions_mode='group')

     cfg1 = AnalysisConfig(hash_type='ssdeep', instructions_mode='group', bin1_path=p1, bin2_path=p1, compare_mode='GPU')
     q = run(p1, p1, cfg1)
     print("Results:", round(q, 4))

     finish = datetime.datetime.now()
     print('Время работы: ' + str(finish - start))
     #cfg2 = AnalysisConfig(hash_type='sha256', instructions_mode='group')
     #q = run(p1, p2, config=AnalysisConfig(hash_type='sha256', instructions_mode='group'))

     #cfg3 = AnalysisConfig(hash_type='ssdeep', instructions_mode='both')
     #q = run(p1, p2, config=AnalysisConfig(hash_type='ssdeep', instructions_mode='both'))
     # result_ssdeep_both = run(p1, p2, config=cfg3)
     #cfg = AnalysisConfig(hash_type="ssdeep", instructions_mode="both")
     #q = run("./coreutils-polybench-hashcat/aoc/O0/3mm", "./coreutils-polybench-hashcat/aoc/O2/3mm", config=cfg)
     # q = run("./coreutils-polybench-hashcat/aoc/O0/keyspace", "./coreutils-polybench-hashcat/aoc/O2/keyspace")
     #q = run("./coreutils-polybench-hashcat/aoc/O2/b2sum", "./coreutils-polybench-hashcat/aoc/O2/b2sum")
     # q = run("./coreutils-polybench-hashcat/aoc/O2/b2sum", "./coreutils-polybench-hashcat/aoc/O2/b2sum")
     # q = run("./coreutils-polybench-hashcat/aoc/O0/date", "./coreutils-polybench-hashcat/g07/O1/df")
     #print("Results:", round(q, 4))
     #end_time = time.time()
     #print(round(end_time - start_time, 4))
    # h_types = ["ssdeep", "nilsimsa" ]
    # i_modes = ["none", "generalize", "group"]
    #
    # run_set = {}
    # i = 0
    # for h_type in h_types:
    #     for i_m in i_modes:
    #         cfg = AnalysisConfig(hash_type=h_type, instructions_mode=i_m)
    #         q = run("./coreutils-polybench-hashcat/aoc/O0/3mm", "./coreutils-polybench-hashcat/aoc/O2/3mm", config=cfg)
    #         print(f"set: |hash_type: {h_type}| instruction_mode: {i_m}")
    #         print("Result:", round(q, 4))
    #         run_set[i] = {
    #             "h_type": h_type,
    #             "i_m": i_m,
    #             "result:": round(q, 4)
    #         }
    #         i+=1
    #
    # print(1)



# -------------------------------------------
#block_hash = 'fc646b194d96a62b53ea6b5ee098dd56d39c7bd5dd9e5d72378dcf5fc4adb844'
#compare_hash = '4fb62730a0ebdcb2dc9c87cfbbc632b13d92a6b00f27c77531c3eea9cfd8cda7'
#similarity = ppdeep.compare(block_hash, compare_hash)  # fuzz.ratio(block_hash, compare_hash)
#start_time = time.time()
# q = run("./coreutils-polybench-hashcat/c08/O0/expander", "./coreutils-polybench-hashcat/c08/O0/expander")


# f1 = ppdeep.hash_from_file(".\\requirements.txt")
# f2 = ppdeep.hash_from_file(".\\requirementscopy.txt")
# print(f1)
# print(f2)
# print(ppdeep.compare(f1, f2)/100)

#f1 = tlsh.hash("weyaquiryawo;yiaseghsehgdkrg;jdfhnbh;rthweyaquiryawo;yiaseghsehgdkrg;jdfhnbh;rthweyaquiryawo;yiaseghsehgdkrg;jdfhnbh;rthweyaquiryawo;yiaseghsehgdkrg;jdfhnbh;rthweyaquiryawo;yiaseghsehgdkrg;jdfhnbh;rthweyaquiryawo;yiaseghsehgdkrg;jdfhnbh;rthweyaquiryawo;yiaseghsehgdkrg;jdfhnbh;rth".encode())
#f2 = tlsh.hash("mrbrlkjb;rjiboeierutjbdf;ljktgsk;rtnbst'[bjmrbrlkjb;rjiboeierutjbdf;ljktgsk;rtnbst'[bj[nesrjgjsg'lgejsgmrbrlkjb;rjiboeierutjbdf;ljktgsk;rtnbst'[bj[nesrjgjsg'lgejsgmrbrlkjb;rjiboeierutjbdf;ljktgsk;rtnbst'[bj[nesrjgjsg'lgejsgmrbrlkjb;rjiboeierutjbdf;ljktgsk;rtnbst'[bj[nesrjgjsg'lgejsgmrbrlkjb;rjiboeierutjbdf;ljktgsk;rtnbst'[bj[nesrjgjsg'lgejsg[nesrjgjsg'lgejsg".encode())
#file1 = ".\\coreutils-polybench-hashcat\\aoc\O0\\dir"
#file2 = ".\\coreutils-polybench-hashcat\\aoc\\O2\\dir"
#f1 = tlsh.hash(open(file1, 'rb').read())
#f2 = tlsh.hash(open(file2, 'rb').read())

#print(abs((300 - tlsh.diff(f1, f2) )/300) )
# print( max(0, (300 - tlsh.diff(f1, f2))/300))
# f1 = fuzzyhashlib.sdhash("agkjsekgjd'rpgier")
# print(f1)
