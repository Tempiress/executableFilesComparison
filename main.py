import datetime
import os

import ppdeep
import r2pipe
import tlsh

from run import run
import time
import concurrent.futures
from functools import partial

from progress.bar import Bar
from progress.spinner import Spinner
import asyncio
from memory_cfg_from_exe_generator import CFGAnalyzer
# from tqdm import tqdm


def ppdeep_comparison(file1, file2):
    return ppdeep.compare(ppdeep.hash_from_file(file1), ppdeep.hash_from_file(file2)) / 100


def process_file_pair(aq, bq, file, l1_dir, l2_dir0, l2_dir, f):
    try:

        s_prog_time = time.time()
        q = run(aq, bq)

        e_prog_time = time.time()
        delta_prog_time = round(e_prog_time - s_prog_time, 1)
        print(f"RES: {round(q,5)} Time: {delta_prog_time}")
        s_p_prog_time = time.time()
        ppdeep_compare = ppdeep_comparison(aq, bq)
        e_p_prog_time = time.time()
        delta_ppdeep_time = round(e_p_prog_time - s_p_prog_time, 1)

        file_size_aq = round(os.path.getsize(aq) / 1024, 1)
        file_size_bq = round(os.path.getsize(bq) / 1024, 1)

        tlsh_s_time = time.time()
        tlsh_diff = tlsh.diff(tlsh.hash(open(aq, 'rb').read()), tlsh.hash(open(bq, 'rb').read()))
        tlsh_e_time = time.time()
        delta_tlsh_time = round(tlsh_e_time - tlsh_s_time, 1)
        result_line = f"{l1_dir}/{l2_dir0}/{file};{l1_dir}/{l2_dir}/{file};{file_size_aq};{file_size_bq};{round(q, 4)};{ppdeep_compare};{tlsh_diff};{delta_prog_time};{delta_ppdeep_time};{delta_tlsh_time}\n"

        # Блокировка для безопасной записи в файл
        with lock:
            f.write(result_line)
            f.flush()

    except Exception as e:
        print(f"Error processing {aq} and {bq}: {e}")



def start_program():
    # Берём один файл и сравниваем его все виды
    fileName = "3mm"
    filenames = os.listdir('./coreutils-polybench-hashcat/aoc/Os/')
    filenames.remove('2mm')
    # filenames = ["base32"]
    l1 = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, c06
    # l1 = ["aoc"]
    output_file = f"./Debugging./dbg{str(datetime.datetime.now().hour)}{datetime.datetime.now().minute}.txt"
    # f.write("файл1;файл2;вес1;вес2;рез_программы;рез_ppdeep;время_сравн_прогр;время_сравн_ppdeep\n")

    global lock
    lock = threading.Lock()

    with open(output_file, mode="a") as f:
        f.write("файл1;файл2;вес1;вес2;рез_программы;рез_ppdeep;рез_tlsh;время_сравн_прогр;время_сравн_ppdeep;время_сравн_tlsh\n")
        f.flush()
        start_time = time.time()
        try:
            # ProcessPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                futures = []
                for file in filenames:
                    for dirindex1 in range(0, len(l1)):
                        l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
                        # l2 = ["O0", "O1", "O2"]

                        for dirindex2 in range(1, len(l2)):
                            aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}'
                            bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file}'

                            futures.append(
                                executor.submit(
                                    process_file_pair, aq, bq, file, l1[dirindex1], l2[0], l2[dirindex2], f
                                )
                            )

                for future in concurrent.futures.as_completed(futures):
                    future.result()
                #concurrent.futures.wait(futures)
        except KeyboardInterrupt:
            print("UserInterrupt")

        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Time to working: {round(execution_time, 1)} seconds")
            f.close()
            print("File is closed")
        # except KeyboardInterrupt:
        #     print("UserInterrupt")
        #
        # finally:
        #     end_time = time.time()
        #     execution_time = end_time - start_time
        #     print(f"Time to working: {round(execution_time, 1)} seconds")
        #     f.close()
        #     print("File is closed")



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

if __name__ == '__main__':
    import threading
    try:
        start_program()
    except KeyboardInterrupt:
        print("Keyboard interrupt")

