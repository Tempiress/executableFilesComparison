import json


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
        if target_block_data["jumps"] is None or target_block_data["jumps"] == '':
            if target_block == len(data):
                continue
            else:
                next_block = str(int(target_block) + 1)
                if int(next_block) > len(data):
                    continue
                links[target_block] = {
                    "block": target_block_data["block"],
                    "NumBlock": target_block_data["id"],
                    "links": data[next_block]["block"],
                    "NumBlockLinks": data[next_block]["id"]
                }
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
            "NumBlock": target_block_data["id"],
            "links": block_links,
            "NumBlockLinks": num_block_links
            }

    return json.dumps(links)

# print(block_links('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt'))
