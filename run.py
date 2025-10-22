import glob
import os
import time
import tlsh
import ppdeep
import concurrent.futures

from cfg_from_exe_generator import call_func_graph, create_cfgs_from_exe
from cfglinks_partition import links_two_program
from memory_cfg_from_exe_generator import CFGAnalyzer
from similarity import hemming_prog
import asyncio
from config import AnalysisConfig

def deletefiles(dir):
    files = glob.glob((os.path.join(dir, '*')))

    # Удаление каждого файла
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
            # print(f"Deleted file: {file}") # Для отладки очищения файлов рабочих директорий
        else:
            print(f"skip dir: {file}")



def cfgAdder(call_graph, p_funcs):
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
    cfga = CFGAnalyzer()
    print("Analyze Executable...")
    p1_funcs = cfga.analyze_executable(p1)
    p2_funcs = cfga.analyze_executable(p2)


    print("get call graphs...")
    # Создание файла связей блоков (Imports)
    lks1 = cfga.get_call_graph(p1)
    lks2 = cfga.get_call_graph(p2)

    # Создание файла связей блоков (Imports)
    lks1 = cfgAdder(cfga.get_call_graph(p1), p1_funcs)
    lks2 = cfgAdder(cfga.get_call_graph(p2), p2_funcs)


    matrix1, matrix2 = links_two_program(p1_funcs, p2_funcs, lks1, lks2, config=config)
    # u = hemming_prog(matrix1, matrix2)

    if len(matrix1) < len(matrix2):
        hh = hemming_prog(matrix1, matrix2, max(len(matrix1), len(matrix2)), p1_funcs, p2_funcs, config=config)
    else:
        hh = hemming_prog(matrix2, matrix1, max(len(matrix1), len(matrix2)), p2_funcs, p1_funcs, config=config)

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



if __name__ == '__main__':
     #block_hash = 'fc646b194d96a62b53ea6b5ee098dd56d39c7bd5dd9e5d72378dcf5fc4adb844'
     #compare_hash = '4fb62730a0ebdcb2dc9c87cfbbc632b13d92a6b00f27c77531c3eea9cfd8cda7'
     #similarity = ppdeep.compare(block_hash, compare_hash)  # fuzz.ratio(block_hash, compare_hash)
     #start_time = time.time()
     # q = run("./coreutils-polybench-hashcat/c08/O0/expander", "./coreutils-polybench-hashcat/c08/O0/expander")
     p1 = "./coreutils-polybench-hashcat/aoc/O0/3mm"
     p2 = "./coreutils-polybench-hashcat/aoc/O2/3mm"
     cfg1 = AnalysisConfig(hash_type='ssdeep', instructions_mode='group')

     # cfg1 = AnalysisConfig(hash_type='md5', instructions_mode='generalize')
     q = run(p1, p2, cfg1)
     print("Results:", round(q, 4))

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
    # h_types = ["ssdeep", "md5", "sha256" ]
    # i_modes = ["none", "generalize", "group", "both"]
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
