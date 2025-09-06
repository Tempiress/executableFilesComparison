#blocklinks4.py
import json
import logging


def block_links(json_data1):
    """
    JSON со связями между блоков файла
    :param json_data1:
    :return:
    """
    data = json.loads(json_data1)
    links = {}

    for target_block, target_block_data in data.items():

        block_links = 0
        num_block_links = 0
        # Если нет блока добавляем на след блок
        if target_block_data["jumps"] is None or target_block_data["jumps"] == '':

            next_block = str(int(target_block) + 1)
            if int(next_block) <= len(data):
                links[target_block] = {
                    "block": target_block_data["block"],
                    "NumBlock": target_block_data["id"],
                    "links": data[next_block]["block"],
                    "NumBlockLinks": data[next_block]["id"],
                    "fail": '',
                    "NumBlockFail": -1
                    }
            continue

        try:
            target_jump = int(target_block_data["jumps"].rstrip('; '))
        except ValueError:
            logging.warning(f"Invalid jump value in block {target_block}")

        target_fail = ''

        if target_block_data["fails"] != '':
            try:
                target_fail = int(target_block_data["fails"].rstrip('; '))
            except ValueError:
                logging.warning(f"Invalid fail value in block {target_block}")
        nbf = -1

        for check_block, check_block_data in data.items():
            if target_block == check_block:
                continue
            if target_jump == check_block_data["block"]:
                block_links = target_jump
                num_block_links = check_block
        links[target_block] = {
            "block": target_block_data["block"],
            "NumBlock": target_block_data["id"],
            "links": block_links,
            "NumBlockLinks": num_block_links,
            "fail": target_fail,
            "NumBlockFail": nbf
            }

        if target_fail != '':
            for check_block, check_block_data in data.items():
                if target_fail == check_block:
                    continue
                if target_fail == check_block_data["block"]:
                    nbf = check_block
            links[target_block]["fail"] = target_fail
            links[target_block]["NumBlockFail"] = nbf

    return json.dumps(links)

# print(block_links('.\\cfg\\cfg_5368778762.txt'))


# cfg_from_exe_generator
import r2pipe
import os
import logging


async def create_cfgs_from_exe(exe_dist, save_path):
    """
    Извлекает CFG из исполняемого файла с помощью Radare2.
    :param exe_dist: Путь к исполняемому файлу.
    :param save_path: Директория для сохранения CFG.
    """

    # Open the binary
    try:
        r2 = r2pipe.open(exe_dist, flags=["-2"])

        # Perform initial analysis
        r2.cmd("aaa")
        # List functions
        functions = r2.cmdj("aflj")
        if not functions:
            raise ValueError("No functions found in the binary.")
    except Exception as e:
        logging.error(f"Error processing file {exe_dist}: {e}")

    # function_address = functions[0]
    # r2.cmd(f"agf @ {function_address}")
    # print(functions[0]["addr"])

    if not os.path.exists(".\\cfg1"): os.mkdir(".\\cfg1")
    if not os.path.exists(".\\cfg2"): os.mkdir(".\\cfg2")

    # Iterate through functions and generate CFGs
    for func in functions:
        function_address = func["offset"]
        name = func["name"]
        r2.cmd(f"agf @ {function_address}")

        # Extract and save CFG information to a text document
        cfg_info = r2.cmd(f"agj {function_address}")
        # with open(save_path + f"cfg_{function_address}.txt", "w") as file:
        with open(save_path + f"{name}.txt", "w") as file:
            file.write(cfg_info)

    r2.quit()


async def call_func_graph(exe_dist, save_name):
    """
    Создание файла связей блоков (Imports)
    :param exe_dist:
    :param save_name:
    :return: file
    """
    r2 = r2pipe.open(exe_dist, flags=["-2"])
    r2.cmd("aaa")
    cflinks = r2.cmd("agCj")
    with open(save_name, "w") as fl:
        fl.write(cflinks)
    r2.quit()

# call_func_graph(".\\HW3.exe", ".\\cfgcflinks2")
# create_cfgs_from_exe(".\\sources\\Homework2.exe", ".\\cfg2\\")
# Close Radare2
# r2.quit()




# main_pairs_compare.py 

import copy
import os
from progress.bar import Bar
from similarity import similarity


def main_compare8(folder1, folder2, matrix1, matrix2):
    # Создание списка файлов для каждой папки
    # P1 = os.listdir(folder1)
    # P2 = os.listdir(folder2)
    Pairs = []
    _P1_files = {file: os.path.join(folder1, file) for file in os.listdir(folder1)}
    _P2_files = {file: os.path.join(folder2, file) for file in os.listdir(folder2)}

    P1_files = {}
    for file in range(1, len(matrix1[0])):
        P1_files[matrix1[0][file]] = os.path.join(folder1, matrix1[0][file] + ".txt")

    P2_files = {}
    for file2 in range(1, len(matrix2[0])):
        P2_files[matrix2[0][file2]] = os.path.join(folder2, matrix2[0][file2] + ".txt")

    for file1 in P1_files:
        for file2 in P2_files:
            Pairs.append([file1, file2])

    # ff = open('./Debug/twoFuncDebug/res.txt', 'w')
    PairWithSim = []
    # bar = Bar('Processing', max=len(P1_files))
    for f, g in Pairs:
        join = f + ':' + g
        o1 = os.path.join(folder1, f + '.txt')
        o2 = os.path.join(folder2, g + '.txt')
        ssim, lndf = similarity(o1, o2)
        lf = lndf[0]
        lg = lndf[1]

        PairWithSim.append({"pair": join,
                            "sim": ssim,
                            "num_block_in_first": lf,
                            "num_block_in_second": lg
                            })

    # ff.write(str(PairWithSim))
    k = 1
    # for p in PairWithSim:
        # ff.write(str(k) + ". " + str(p["pair"]) + "   --->   " + str(p["sim"]) + "\n")
        # k += 1

    # ff.close()
    # II
    counter = 0
    p1_nodes = []
    p2_nodes = []

    # Цикл по короткому из списков функций (P1 или P2)
    min_len_p = min(len(P1_files), len(P2_files))
    index_of_short = -1
    if(min_len_p == len(P1_files)):
        arr_with_min_len_p = P1_files
        index_of_short = 0
    else:
        arr_with_min_len_p = P2_files
        index_of_short = 1

    for short_p in arr_with_min_len_p:
        max_sim = float('inf')
        max_sim_element = None
        # bar.next()
        TempPairs = []
        # Цикл по всем парам с sim
        for pr in PairWithSim:
            if pr["pair"].split(":")[index_of_short] == short_p and pr["sim"] < max_sim:
                max_sim = pr["sim"]
                max_sim_element = pr
                if(pr["sim"] == 0):
                    TempPairs.append(pr)

        el = max_sim_element  # PairWithSim[1]
        p1_nodes.append({"new_label": counter,
                        "old_label": el["pair"].split(":")[0]
                        })
        p2_nodes.append({"new_label": counter,
                        "old_label": el["pair"].split(":")[1]
                        })

        z = 0
        while z < len(PairWithSim):
            if (PairWithSim[z]["pair"].split(":")[0]) == el["pair"].split(":")[0]:
                PairWithSim.remove(PairWithSim[z])
                continue

            if(PairWithSim[z]["pair"].split(":")[1]) == el["pair"].split(":")[1]:
                PairWithSim.remove(PairWithSim[z])
                continue
            z += 1

        counter += 1
    return p1_nodes, p2_nodes


def main_compare(folder1, folder2, matrix1, matrix2):
    # Создание списка файлов для каждой папки
    P1_files = {}
    for file in range(1, len(matrix1[0])):
        P1_files[matrix1[0][file]] = os.path.join(folder1, matrix1[0][file] + ".txt")

    P2_files = {}
    for file2 in range(1, len(matrix2[0])):
        P2_files[matrix2[0][file2]] = os.path.join(folder2, matrix2[0][file2] + ".txt")

    # Генерация всех возможных пар
    Pairs = []
    for file1 in P1_files:
        for file2 in P2_files:
            Pairs.append((file1, file2))

    # Сравнение всех пар
    PairWithSim = []
    for f, g in Pairs:
        o1 = os.path.join(folder1, f + '.txt')
        o2 = os.path.join(folder2, g + '.txt')

        # Сравнение функций
        ssim, lndf = similarity(o1, o2)
        PairWithSim.append({
            "pair": (f, g),
            "sim": ssim,
            "num_block_in_first": lndf[0],
            "num_block_in_second": lndf[1]
        })




    # Сортировка пар по убыванию схожести
    PairWithSim.sort(key=lambda x: x["sim"], reverse=True)

    # Выбор оптимальных пар
    used_p1 = set()
    used_p2 = set()
    p1_nodes = []
    p2_nodes = []
    counter = 0

    for pair in PairWithSim:
        f, g = pair["pair"]
        if f not in used_p1 and g not in used_p2:
            p1_nodes.append({
                "new_label": counter,
                "old_label": f
            })
            p2_nodes.append({
                "new_label": counter,
                "old_label": g
            })
            used_p1.add(f)
            used_p2.add(g)
            counter += 1

    return p1_nodes, p2_nodes


def hxconverter(num):
    nm = int(num[4:], 16)
    result = "cfg_" + str(nm) + ".txt"
    return result


def important_main_compare(folder1, folder2, matrix1, matrix2 ):
    # print("Процесс создания словарей файлов для каждой папки")
    P1_files = {file: os.path.join(folder1, file) for file in os.listdir(folder1)}
    P2_files = {file: os.path.join(folder2, file) for file in os.listdir(folder2)}

    # P1_files = {}
    # for file in range(1, len(matrix1[0])):
     # P1_files[matrix1[0][file]] = os.path.join(folder1, matrix1[0][file] + ".txt")

    # P2_files = {}
    # for file2 in range(1, len(matrix2[0])):
     # P2_files[matrix2[0][file2]] = os.path.join(folder2, matrix2[0][file2] + ".txt")

    # Сортируем файлы по ключам
    sorted_P1_files = dict(sorted(P1_files.items(), key=lambda x: x[0]))
    sorted_P2_files = dict(sorted(P2_files.items(), key=lambda x: x[0]))

    P1_files_temp = copy.copy(P1_files)
    P2_files_temp = copy.copy(P2_files)
    print("Длина словаря P1 =>", len(P1_files))
    print("Длина словаря P2 =>", len(P2_files))

    p1_nodes = []
    p2_nodes = []
    print("Создание массивов меток....")
    bar = Bar('Processing', max=len(P1_files))
    # ff = open('result.txt', 'w')

    for file1, path1 in sorted_P1_files.items():
        max_sim = float('inf')
        max_sim_element = None

        for file2, path2 in sorted_P2_files.items():
            ssim, lndf = similarity(path1, path2)
            # print("file1 = ", file1, "file2 = ", file2, "Result = ", ssim)
            # ff.write(" file1 = " + file1 + " file2 = " + file2 + " Result = " + str(ssim) + "\n")
            if ssim < max_sim:
                max_sim = ssim
                max_sim_element = {"pair": f"{file1}:{file2}", "sim": ssim, "num_block_in_third": lndf[0], "num_block_in_second": lndf[1]}
        if max_sim_element:
            p1_nodes.append({"new_label": len(p1_nodes), "old_label": max_sim_element["pair"].split(":")[0]})
            p2_nodes.append({"new_label": len(p2_nodes), "old_label": max_sim_element["pair"].split(":")[1]})
            del P1_files_temp[max_sim_element["pair"].split(":")[0]]
            del P2_files_temp[max_sim_element["pair"].split(":")[1]]
        bar.next()
    bar.finish()
    # ff.close()

    return p1_nodes, p2_nodes



# opcodeparser.py

import hashlib
import json

import ppdeep
from thefuzz import fuzz


def create_hasher(hash_type="ssdeep"):
    """
    Создает функцию хеширования в зависимости от типа.
    :param hash_type: Тип хеширования ("ssdeep", "md5", "sha256" и т.д.)
    :return: Функция хеширования
    """
    if hash_type == "ssdeep":
        return ppdeep.hash
    elif hash_type == "md5":
        return lambda x: hashlib.md5(x.encode()).hexdigest()
    elif hash_type == "sha256":
        return lambda x: hashlib.sha256(x.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash type: {hash_type}")


# Функция генерации JSON объекта, c добавлением хеша ssdeep
def op_parser(path, hash_type='ssdeep'):
    """
    Начальный разделитель блоков CFG
    :param path: Путь к файлу
    :param hash_type: Тип хеширования
    :return: JSON
    """

    hasher = create_hasher(hash_type)
    with open(path, 'r') as f:
        json_text = f.read()
        data = json.loads(json_text)
        mi = 0
        blocks = {}
        # Проходим через элементы списка верхнего уровня
        for item in data:
            # Проверяем, существует ли поле "blocks"
            if "blocks" in item:
                # Если существует, проходим через элементы в "blocks"
                for block in item["blocks"]:
                    opcodes = []
                    opcodes2 = ""
                    hash_opcodes = []
                    hash_opcodes2 = ""
                    jumps = ""
                    fails = ""

                    if "ops" in block:

                        for op in block["ops"]:

                            if "opcode" in op:
                                opcodes.append(op["opcode"])
                                opcodes2 = opcodes2 +  op["opcode"] + "; "
                                hash_opcodes.append(ppdeep.hash(op["opcode"]))
                                hash_opcodes2 = hash_opcodes2 +  (op["opcode"]) + "; "

                        if "jump" in op:
                            jumps = jumps + str(op["jump"]) + "; "

                        if "fail" in op:
                            fails = fails + str(op["fail"]) + "; "

                        mi = mi + 1
                        item = {}
                        item['id'] = mi
                        item['block'] = block["offset"]
                        item['opcodes'] = opcodes2
                        item['hashssdeep'] = hasher(opcodes2) # ppdeep.hash(opcodes2)
                        item['hash'] = (hashlib.md5(opcodes2.encode())).hexdigest()
                        item['jumps'] = jumps
                        item['fails'] = fails
                        blocks[mi] = item
    myjsondata = json.dumps(blocks)
    return myjsondata


#! Переписать в два цикла
def find_similar_blocks(json_data1, json_data2):
    """
    Нахождение максимально похожих по степени сравнения блоков
    :param json_data1:
    :param json_data2:
    :return: JSON
    """
    data1 = json.loads(json_data1)
    data2 = json.loads(json_data2)

    similar_blocks = {}
    klen = 0
    for block_id, block_data in data1.items():
        block_hash = block_data['hashssdeep']

        hash_equal = -1
        for compare_id, compare_data in data2.items():

            if(block_data['hash'] == compare_data['hash']):
                hash_equal = 1
            else:
                hash_equal = 0

            compare_hash = compare_data['hashssdeep']

            similarity = fuzz.ratio(block_hash, compare_hash)

            similar_blocks[klen] = {
                'block': block_id,
                'similar_to': compare_id,
                'simcount': similarity,
                'simequal': hash_equal
            }
            klen += 1
    klen = 0
    similar_blocks_output = {}

    while len(similar_blocks) != 0:
            max_simcount = 0
            max_simcount_element = {}

            # Если нашли совершенно идентичные по крипто-хешу
            first_key, first_value = similar_blocks.popitem()
            similar_blocks[first_key] = first_value
            if similar_blocks[first_key]['simequal'] == 1:
                similar_blocks_output[klen] = similar_blocks[first_key]
                blocks_to_remove = []

                # Заполняем массив индексами элементов которые нужно удалить
                for block_num, block in similar_blocks.items():
                    if block['block'] == similar_blocks_output[klen]['block'] or block['similar_to'] == similar_blocks_output[klen]['similar_to']:
                        blocks_to_remove.append(block_num)

                # Удаляем все элементы с одинаковыми значениями block и similar_to
                for block in blocks_to_remove:
                    del similar_blocks[block]
                klen += 1
                continue

            for block_num, block_val in similar_blocks.items():
                if block_val['simcount'] > max_simcount:
                    max_simcount_element[0] = similar_blocks[block_num]
                    # !!!Проверить max_simcount = block_val['simcount']

            similar_blocks_output[klen] = max_simcount_element[0]
            blocks_to_remove = []

            # Заполняем массив индексами элементов которые нужно удалить
            for block_num, block in similar_blocks.items():
                if block['block'] == similar_blocks_output[klen]['block'] or block['similar_to'] == similar_blocks_output[klen]['similar_to']:
                    blocks_to_remove.append(block_num)

            # Удаляем все элементы с одинаковыми значениями block и similar_to
            for block in blocks_to_remove:
                del similar_blocks[block]
            klen += 1

    return json.dumps(similar_blocks_output)




# renamefile.py

import json


def rename_block(data1, data2, sim):
    """
    Переименование блоков второго файла
    :return: JSON, Massive of lens
    """

    sim_data = json.loads(sim)

    used_ids = []
    for block_id2, block_data2 in data2.items():
        block_data2["id"] = -1

    for block_id1, block_data1 in sim_data.items():
        data2[block_data1["similar_to"]]["id"] = block_data1["block"]
        used_ids.append(int(block_data1["block"]))

    for block_id2, block_data2 in data2.items():
        if block_data2["id"] != -1:
            continue
        for i in range(1, len(data2)+1):
            if i not in used_ids:
                block_data2["id"] = i
                used_ids.append(i)
                break

    return json.dumps(data2), [len(data1), len(data2)] # abs(len(data1) - len(data2))


#similarity.py

import json
import os

import numpy as np

from blocklinks4 import *
from opcodeparser import *
from renamefile import *


def create_matrix2(json_data1, json_data2):
    """
    Генерация матрицы
    :param json_data1, json_data2:
    :return:
    """

    data1 = json.loads(json_data1)
    data2 = json.loads(json_data2)
    size_matrix = max(len(data1), len(data2)) + 2

    matrix1 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data1.items():
        matrix1[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1
        matrix1[int(block_data["NumBlock"])][int(block_data["NumBlockFail"])] = 1

    matrix2 = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data2.items():
        matrix2[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1
        matrix2[int(block_data["NumBlock"])][int(block_data["NumBlockFail"])] = 1

    return matrix1, matrix2


def similarity(cfg1, cfg2):
    """
     Число Хемминга (0-идентич., 1- не иднетич.)
    :param: cfg1 cfg2
    :return: double, difference
    """
    op1 = op_parser(cfg1)
    op2 = op_parser(cfg2)

    data1 = json.loads(op1)
    data2 = json.loads(op2)
    sim_array = find_similar_blocks(op1, op2)
    rename_op2, diff = rename_block(data1, data2, sim_array)

    sim_dict = json.loads(sim_array)
    b_links1 = block_links(op1)
    b_links2 = block_links(rename_op2)

    size_matrix0 = min(len(data1), len(data2)) + 1
    max_size_matrix = max(len(data1), len(data2)) + 1
    umatrix1, umatrix2 = create_matrix2(b_links1, b_links2)
    size_matrix = len(umatrix1)

    A = 0
    B = 0

    try:
        keys = lambda _key: [key for key, value in sim_dict.items() if value.get("block") == _key]
    except Exception as ex:
        print("Error in keys:", ex)
    m = keys(str(1))
    # q = sim_dict[m[0]]
    try:
        sim = lambda i: 1 if len(keys(i)) > 0 and sim_dict[keys(i)[0]]["simequal"] == 1 else (sim_dict[keys(i)[0]]["simcount"]) / 100 if len(keys(i)) > 0 else 0
    except IndexError as ex:
        print(" Список keys(i) пуст. Проверьте данные в sim_dict.", ex)

    for i in range(1, size_matrix0):
        for j in range(1, size_matrix0):

            A0 = (sim(str(i)) + sim(str(j)))
            A += (1 ^ (umatrix1[i][j] ^ umatrix2[i][j])) * A0

    C = (float(A) / ((max_size_matrix - 1) * (max_size_matrix - 1) * 2))
    return C, diff




def create_matrix(json_data1):
    """
    Генерация матрицы
    :param json_data1:
    :return:
    """
    # dt = block_links(json_data1)
    data = json.loads(json_data1)
    size_matrix = len(data) + 2

    matrix = np.zeros((size_matrix, size_matrix), dtype=int)

    for block_id, block_data in data.items():
        matrix[int(block_data["NumBlock"])][int(block_data["NumBlockLinks"])] = 1

    return matrix





def hemming_prog(matrix1, matrix2, maxlen, folder1, folder2):
    size_matrix = len(matrix1)
    # folder1 = ".\\cfg1\\"
    # folder2 = ".\\cfg2\\"
    difference_count = 0
    A = 0
    B = 0
    q = []
    for i in range(1, size_matrix):
        for j in range(1, size_matrix):
            # A0 = (similarity(matrix1[0][i], matrix2[0][j]) + similarity(matrix1[0][j], matrix2[0][i]))


            A0 = (similarity(os.path.join(folder1, matrix1[0][i] + ".txt"),
                             os.path.join(folder2, matrix2[0][i] + ".txt"))[0] + similarity(
                os.path.join(folder1, matrix1[0][j] + ".txt"), os.path.join(folder2, matrix2[0][j] + ".txt"))[0])

            A += (1 ^ (matrix1[i][j] ^ matrix2[i][j])) * A0

    # A0 = (similarity(os.path.join(folder1, matrix1[0][i] + ".txt"),os.path.join(folder1, matrix2[0][j] + ".txt")) + similarity(os.path.join(folder1, matrix1[0][j] + ".txt"),os.path.join(folder1, matrix2[0][i] + ".txt")))
    # os.path.join(folder1, matrix1[0][i] + ".txt")

    C = (float(A) / ((maxlen - 1) * (maxlen - 1) * 2))  #

    return C



#main.py

import datetime
import os
from progress.bar import Bar
from run import run
import time
from progress.spinner import Spinner
import asyncio
from tqdm import tqdm
# q = run(".\\coreutils-polybench-hashcat\\c09\\O0\\cap2hccapx", ".\\coreutils-polybench-hashcat\\c09\\O0\\ct3_to_ntlm")
# print("Result:", round(q, 4))
#
# f = open("./Debugging./avedick.txt", mode='a')
# f.write("Abc\n")
# f.write("Porasd\n")
# f.close()

# Берём один файл и сравниваем его все виды
filenames = os.listdir('./coreutils-polybench-hashcat/aoc/Os/')
filenames.remove('2mm')
l1 = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, c06

# bar2 = Bar('Processing', max=len(filenames))
# spinner = Spinner('Loading ')

f = open(f"./Debugging./dbg{str(datetime.datetime.now().hour)}{datetime.datetime.now().minute}.txt", mode='a')
f.write("файл1;файл2;результат\n")

filenames = filenames[:2:]
# l1 = l1[:2:]
# print(l1)


async def process_file(file, l1, f):
    for dirindex1 in range(0, len(l1)):
        l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
        for dirindex2 in range(1, len(l2)):
            # spinner.next()
            aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}'
            bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file}'
            q = await run(aq, bq)
            # print(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file};./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file};{str(round(q, 4))}\n')
            f.write(f'/{l1[dirindex1]}/{l2[0]}/{file};/{l1[dirindex1]}/{l2[dirindex2]}/{file};{str(round(q, 4))}\n')


async def main():

    # spinner = Spinner('Loading ')
    #bar3 = Bar('Processing', max=len(filenames))
    start_time = time.time()

    tasks = []
    for file in tqdm(filenames, desc="fileproc"):
        tasks.append(process_file(file, l1, f))
    await asyncio.gather(*tasks)
    # time_now = time.time() - start_time
    # print(f"\ntime lasted: {round(time_now,2 )}")
    # print("\n")


    # bar3.finish()
    # spinner.finish()
    f.close()
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time to working: {round(execution_time, 2)} seconds")



if __name__ == "__main__":
    asyncio.run(main())

