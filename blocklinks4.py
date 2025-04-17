import json
import logging

import orjson


def block_links(json_data1):
    """
    JSON со связями между блоков файла
    :param json_data1:
    :return:
    """
    data = orjson.loads(json_data1)
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
    # print("block_links")
    return orjson.dumps(links)

# print(block_links('.\\cfg\\cfg_5368778762.txt'))
