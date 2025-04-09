import datetime
import os

import ppdeep
from progress.bar import Bar
from run import run
import time
from progress.spinner import Spinner
import asyncio
from memory_cfg_from_exe_generator import CFGAnalyzer
# from tqdm import tqdm
# q = run(".\\coreutils-polybench-hashcat\\c09\\O0\\cap2hccapx", ".\\coreutils-polybench-hashcat\\c09\\O0\\ct3_to_ntlm")
# print("Result:", round(q, 4))
#
# f = open("./Debugging./avedick.txt", mode='a')
# f.write("Abc\n")
# f.write("Porasd\n")
# f.close()


def ppdeep_comparison(file1, file2):
    return ppdeep.compare(ppdeep.hash_from_file(file1), ppdeep.hash_from_file(file2)) / 100


# Берём один файл и сравниваем его все виды
fileName = "3mm"
filenames = os.listdir('./coreutils-polybench-hashcat/aoc/Os/')
filenames.remove('2mm')
l1 = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, c06

# bar2 = Bar('Processing', max=len(filenames))
# spinner = Spinner('Loading ')

f = open(f"./Debugging./dbg{str(datetime.datetime.now().hour)}{datetime.datetime.now().minute}.txt", mode='a')
f.write("файл1;файл2;результат\n")

filenames = filenames[:3]
# l1 = l1[:3]
# bar3 = Bar('Processing', max=len(filenames))
try:
    start_time = time.time()
    for file in filenames:
        for dirindex1 in range(0, len(l1)):
            l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
            for dirindex2 in range(1, len(l2)):
                aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}'
                bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file}'
                q = run(aq, bq)

                f.write(f'/{l1[dirindex1]}/{l2[0]}/{file}' + f';/{l1[dirindex1]}/{l2[dirindex2]}/{file}'
                        + ';' + str(round(q, 4)) + ";" + str(ppdeep_comparison(f"./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}", f"./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file}")) + '\n')
                # print(f'/{l1[dirindex1]}/{l2[0]}/{file}' + f' ; /{l1[dirindex1]}/{l2[dirindex2]}/{file}')
    end_time = time.time()
    f.close()
except KeyboardInterrupt:
    print("UserInterrupt")

finally:
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time to working: {round(execution_time, 1)} seconds")
    f.close()
    print("File is closed")



# filenames = os.listdir('./coreutils-polybench-hashcat/aoc/Os/')
# filenames.remove('2mm')
# l1 = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, c06
# # print(l1[])
#
# f = open(f"./Debugging./dbg{str(datetime.datetime.now().hour)}{datetime.datetime.now().minute}.txt", mode='a')
# for fileindex in range(1, len(filenames)):
#     for dirindex1 in range(0, len(l1)):
#         l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
#         print("len:" + str(len(l1)))
#         for dirindex2 in range(1, len(l2)):
#             aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{filenames[fileindex]}'
#             bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{filenames[fileindex + 1]}'
#             q = run(aq, bq)
#
#             f.write(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{filenames[fileindex]} ' + f'&& ./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{filenames[fileindex + 1]} '
#                     + '-> ' + str(round(q, 4)) + '\n' + '--------' + ' \n')
#
# f.close()


