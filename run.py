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
from pathlib import Path

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


def extract_features(p1, p2):
    p1, p2 = str(p1), str(p2)
    print("Compare two programs:" + p1 + " " + p2)
    cfg_analyzer = CFGAnalyzer()
    print("Analyze Executable...")
    print("Analyze Executable p1...")
    p1_funcs = cfg_analyzer.analyze_executable(p1)
    print("Analyze Executable p2...")
    p2_funcs = cfg_analyzer.analyze_executable(p2)

    print("get call graphs...")
    lks1 = cfg_adder(cfg_analyzer.get_call_graph(p1), p1_funcs)
    lks2 = cfg_adder(cfg_analyzer.get_call_graph(p2), p2_funcs)
    return p1_funcs, p2_funcs, lks1, lks2

def run_with_features(p1_funcs, p2_funcs, lks1, lks2, config):
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


     p5 = "./coreutils-polybench-hashcat/g10/O2/expr"
     p6 = "./coreutils-polybench-hashcat/aoc/O2/expr"

     python1 = "./train_programs/python-3.12.7-amd64.exe"
     python2 = "./train_programs/python-3.14.3-amd64.exe"
     #score = run_asm2vec_comparison(p1, p2)

     #print(f"{'-' * 10}\n Asm2vecCuda resut:\n{score}{'-'* 10}")
     #cfg1 = AnalysisConfig(hash_type='nilsimsa', instructions_mode='generalize')

     #cfg1 = AnalysisConfig(hash_type='ssdeep', instructions_mode='generalize', bin1_path=p5, bin2_path=p6, compare_mode='GPU')
     #q = run(p5, p6, cfg1)
     #print("Results:", round(q, 4))

     #finish = datetime.datetime.now()
     #print('Время работы: ' + str(finish - start))

     
     clear_files_dir = Path("./coreutils-polybench-hashcat/aoc/O0/")
     obf_files_dir = Path("./all_obf/")
    
     clear_files = os.listdir(clear_files_dir)

     if os.path.exists("./Debug/results.txt"):
         with open("./Debug/results.txt", "r", encoding="utf-8") as f:
             results_content = f.read()
         clear_files = list(filter(lambda x: x not in results_content, clear_files))

     hash_types = ['ssdeep', 'nilsimsa']
     instructions_modes = ['generalize', 'group', 'both']
     compare_modes = ['GPU', 'custom']
     with open("./Debug/results.txt", "a", encoding="utf-8") as f:
        with open("./Debug/error.txt", "a", encoding="utf-8") as err_f: 
            for filename in clear_files:
                print("-" * 50)
                if filename in os.listdir(obf_files_dir):
                    p1_path = Path.joinpath(clear_files_dir, filename)
                    p2_path = Path.joinpath(obf_files_dir, filename)
                    
                    try:
                        print(f"Extracting features for {filename}...")
                        p1_funcs, p2_funcs, lks1, lks2 = extract_features(p1_path, p2_path)
                    except Exception as e:
                        print(f"Failed to extract features for {filename}: {e}")
                        err_f.write(f"Feature extraction error: {str(filename)}: {e} \n")
                        err_f.flush()
                        continue

                    for hash_type in hash_types:
                        for instruction_mode in instructions_modes:
                            for compare_mode in compare_modes:
                                try:
                                    cfg = AnalysisConfig(hash_type = hash_type, instructions_mode = instruction_mode, compare_mode = compare_mode, bin1_path = str(p1_path), bin2_path = str(p2_path))
                                    res = run_with_features(p1_funcs, p2_funcs, lks1, lks2, cfg)
                                    print(f"=========> result: h_type: {hash_type} // i_mode: {instruction_mode} // c_mode: {compare_mode} // filename: {str(filename)}: {round(res, 4)} <=========") 
                                    f.write(f"result: h_type: {hash_type} // i_mode: {instruction_mode} // c_mode: {compare_mode} // filename: {str(filename)}: {round(res, 4)} \n")
                                    f.flush()
                                except Exception as e:
                                    print(f"=========> error: h_type: {hash_type} // i_mode: {instruction_mode} // c_mode: {compare_mode} // filename: {str(filename)}: {e} <=========")                           
                                    err_f.write(f"error: h_type: {hash_type} // i_mode: {instruction_mode} // c_mode: {compare_mode} // filename: {str(filename)}: {e} \n")
                                    err_f.flush()
        print("-" * 50)
        
        

     




