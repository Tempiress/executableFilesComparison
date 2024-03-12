import json
import os
import ppdeep
from thefuzz import fuzz, process
import numpy as np

def opparser(path):

    d_p = path
    c = 0

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
                    hashopcodes = []
                    hashopcodes2 = ""
                    jumps = ""

                    if "ops" in block:

                        for op in block["ops"]:

                            if "opcode" in op:
                                opcodes.append(op["opcode"])
                                opcodes2 = opcodes2 + op["opcode"] + "; "
                                hashopcodes.append(ppdeep.hash(op["opcode"]))
                                hashopcodes2 = hashopcodes2 + ppdeep.hash(op["opcode"]) + "; "

                        if "jump" in op:
                            jumps = jumps + str(op["jump"]) + "; "

                        mi = mi + 1
                        item = {}
                        item['block'] = block["offset"]
                        item['opcodes'] = opcodes2
                        item['hashssdeep'] = ppdeep.hash(opcodes2)
                        item['jumps'] = jumps
                        blocks[mi] = item
    myjsondata = json.dumps(blocks)
    print(myjsondata, "\n")
    return myjsondata


def block_links(path):
    """
    JSON со связями между блоков файла
    :param path:
    :return:
    """
    links = {}

    dt = opparser(path)
    data = json.loads(dt)

    for target_block, target_block_data in data.items():

        block_links = 0
        num_block_links = 0
        if target_block_data["jumps"] is None or target_block_data["jumps"] == '':
            continue

        target_jump = int((target_block_data["jumps"])[:-2])
        for check_block, check_block_data in data.items():

            if target_block == check_block:
                continue
            if target_jump == check_block_data["block"]:
                block_links = target_block_data["jumps"]
                num_block_links = check_block
        links[target_block] = {
            "block": target_block_data["block"],
            "links": block_links,
            "NumBlockLinks": num_block_links
            }
        # print(json.dumps(links))
    return json.dumps(links)


print(block_links('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt'))