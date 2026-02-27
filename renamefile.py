import copy

# def rename_block(data1, data2, sim_data):
#     """
#     Переименование блоков второго файла
#     :return: dict, Massive of lens
#     """
#     # ВАЖНО: Делаем глубокую копию, чтобы не сломать кэшированные данные!
#     data2_copy = copy.deepcopy(data2)
#
#     used_ids = []
#     for block_id2, block_data2 in data2_copy.items():
#         block_data2["id"] = -1
#
#     # sim_data теперь словарь, проходимся по нему напрямую
#     for block_id1, block_data1 in sim_data.items():
#         data2_copy[block_data1["similar_to"]]["id"] = block_data1["block"]
#         used_ids.append(int(block_data1["block"]))
#
#     for block_id2, block_data2 in data2_copy.items():
#         if block_data2["id"] != -1:
#             continue
#         for i in range(1, len(data2_copy)+1):
#             if i not in used_ids:
#                 block_data2["id"] = i
#                 used_ids.append(i)
#                 break
#
#     # Возвращаем копию словаря без json.dumps
#     return data2_copy, [len(data1), len(data2_copy)]

def rename_block(data1, data2, sim_data):
    """
    Переименование блоков второго файла
    :return: dict, Massive of lens
    """

    # Ручное копирование в 10-50 раз быстрее, чем copy.deepcopy()
    data2_copy = {k: v.copy() for k, v in data2.items()}

    # Используем SET вместо LIST для мгновенного поиска O(1)
    used_ids = set()

    for block_id2, block_data2 in data2_copy.items():
        block_data2["id"] = -1

    # sim_data теперь словарь, проходимся по нему напрямую
    for block_id1, block_data1 in sim_data.items():
        data2_copy[block_data1["similar_to"]]["id"] = block_data1["block"]
        used_ids.add(int(block_data1["block"]))

    avaliable_ids = [i for i in range(1, len(data2_copy) + 1) if i not in used_ids]
    avali_idx = 0

    for block_id2, block_data2 in data2_copy.items():
        if block_data2["id"] != -1:
            continue
        if avali_idx < len(avaliable_ids):
            new_id = avaliable_ids[avali_idx]
            block_data2["id"] = new_id
            used_ids.add(new_id)
            avali_idx += 1

    # Возвращаем копию словаря без json.dumps
    return data2_copy, [len(data1), len(data2_copy)]