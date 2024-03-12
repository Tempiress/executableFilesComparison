import json
import os
import ppdeep
from  opcodeparser import *
from thefuzz import fuzz, process
import numpy as np


def block_links(path):
    """
    JSON со связями между блоков файла
    :param path:
    :return:
    """
    links = {}

    dt = op_parser(path)
    data = json.loads(dt)

    for target_block, target_block_data in data.items():

        block_links = []
        num_block_links = []
        if target_block_data["jumps"] is None or target_block_data["jumps"] == '':
            continue

        target_jump = int((target_block_data["jumps"])[:-2])
        for check_block, check_block_data in data.items():

            if target_block == check_block:
                continue
            if target_jump == check_block_data["block"]:
                block_links.append(target_block_data["jumps"])
                num_block_links.append(check_block)
        links[target_block] = {
            "block": target_block_data["block"],
            "links": block_links,
            "NumBlockLinks": num_block_links
            }
    return json.dumps(links)


#print(blocklinks('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt'))
print("blocklinsk")
sab = op_parser('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt')
print(sab)