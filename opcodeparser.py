import json
import ppdeep
from thefuzz import fuzz, process
import numpy as np


# Функция генерации JSON объекта, c добавлением хеша ssdeep
def op_parser(path):
    """
    Начальный разделитель блоков CFG
    :param path:
    :return: JSON
    """
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

                    if "ops" in block:

                        for op in block["ops"]:

                            if "opcode" in op:
                                opcodes.append(op["opcode"])
                                opcodes2 = opcodes2 + op["opcode"] + "; "
                                hash_opcodes.append(ppdeep.hash(op["opcode"]))
                                hash_opcodes2 = hash_opcodes2 + ppdeep.hash(op["opcode"]) + "; "

                        if "jump" in op:
                            jumps = jumps + str(op["jump"]) + "; "

                        mi = mi + 1
                        item = {}
                        item['id'] = mi
                        item['block'] = block["offset"]
                        item['opcodes'] = opcodes2
                        item['hashssdeep'] = ppdeep.hash(opcodes2)
                        item['jumps'] = jumps
                        blocks[mi] = item
    myjsondata = json.dumps(blocks)
    return myjsondata


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

    for block_id, block_data in data1.items():
        block_hash = block_data['hashssdeep']
        max_similarity = 0
        max_similar_to = ""

        for compare_id, compare_data in data2.items():

            compare_hash = compare_data['hashssdeep']
            if compare_id in similar_blocks.values():
                continue

            similarity = fuzz.ratio(block_hash, compare_hash)
            if similarity > max_similarity:
                max_similarity = similarity
                max_similar_to = compare_id

        similar_blocks[block_id] = {
            'block': block_id,
            'similar_to': max_similar_to,
            'simcount': max_similarity
        }

    return json.dumps(similar_blocks)





op = op_parser('F:\\programming 2024\\Sci_Research\\cfg\\cfg_5368778757.txt')
jl= json.loads(op)
print(len(jl))


#result = find_similar_blocks('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')
