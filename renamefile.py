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