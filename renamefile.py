import copy

def rename_block(data1, data2, sim_data):
    """
    Переименование блоков второго файла
    :return: dict, Massive of lens
    """
    # ВАЖНО: Делаем глубокую копию, чтобы не сломать кэшированные данные!
    data2_copy = copy.deepcopy(data2)

    used_ids = []
    for block_id2, block_data2 in data2_copy.items():
        block_data2["id"] = -1

    # sim_data теперь словарь, проходимся по нему напрямую
    for block_id1, block_data1 in sim_data.items():
        data2_copy[block_data1["similar_to"]]["id"] = block_data1["block"]
        used_ids.append(int(block_data1["block"]))

    for block_id2, block_data2 in data2_copy.items():
        if block_data2["id"] != -1:
            continue
        for i in range(1, len(data2_copy)+1):
            if i not in used_ids:
                block_data2["id"] = i
                used_ids.append(i)
                break

    # Возвращаем копию словаря без json.dumps
    return data2_copy, [len(data1), len(data2_copy)]