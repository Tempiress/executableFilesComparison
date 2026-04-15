import logging
import time


# def block_links(json_data1):
#     """
#     JSON со связями между блоков файла
#     :param json_data1:
#     :return:
#     """
#     data = json_data1 # orjson.loads(json_data1)
#     links = {}
#
#     for target_block, target_block_data in data.items():
#         block_links = 0
#         num_block_links = 0
#         # Если нет блока добавляем на след блок
#         if target_block_data["jumps"] is None or target_block_data["jumps"] == '':
#
#             next_block = int(target_block) + 1
#             if int(next_block) <= len(data):
#                 links[target_block] = {
#                     "block": target_block_data["block"],
#                     "NumBlock": target_block_data["id"],
#                     "links": data[next_block]["block"],
#                     "NumBlockLinks": data[next_block]["id"],
#                     "fail": '',
#                     "NumBlockFail": -1
#                     }
#             continue
#
#         try:
#             target_jump = int(target_block_data["jumps"].rstrip('; '))
#         except ValueError:
#             logging.warning(f"Invalid jump value in block {target_block}")
#
#         target_fail = ''
#
#         if target_block_data["fails"] != '':
#             try:
#                 target_fail = int(target_block_data["fails"].rstrip('; '))
#             except ValueError:
#                 logging.warning(f"Invalid fail value in block {target_block}")
#         nbf = -1
#
#         for check_block, check_block_data in data.items():
#             if target_block == check_block:
#                 continue
#             if target_jump == check_block_data["block"]:
#                 block_links = target_jump
#                 num_block_links = check_block
#         links[target_block] = {
#             "block": target_block_data["block"],
#             "NumBlock": target_block_data["id"],
#             "links": block_links,
#             "NumBlockLinks": num_block_links,
#             "fail": target_fail,
#             "NumBlockFail": nbf
#             }
#
#         if target_fail != '':
#             for check_block, check_block_data in data.items():
#                 if target_fail == check_block:
#                     continue
#                 if target_fail == check_block_data["block"]:
#                     nbf = check_block
#             links[target_block]["fail"] = target_fail
#             links[target_block]["NumBlockFail"] = nbf
#     # print("block_links")
#     return links #orjson.dumps(links)

def block_links(json_data1):
    """
    JSON со связями между блоков файла
    :param json_data1:
    :return:
    """
    data = json_data1  # orjson.loads(json_data1)
    links = {}

    # -- создаём индекс адресов один раз O(N) --
    addr_to_key = {block_data["block"]: block_key for block_key, block_data in data.items()}

    for target_block, target_block_data in data.items():
        block_links = 0
        num_block_links = 0
        nbf = -1
        target_fail = ''

        # Если нет jump — линейный переход на следующий блок
        if target_block_data["jumps"] is None or target_block_data["jumps"] == '':
            next_block = int(target_block) + 1
            if next_block <= len(data):
                links[target_block] = {
                    "block": target_block_data["block"],
                    "NumBlock": target_block_data["id"],
                    "links": data[next_block]["block"],
                    "NumBlockLinks": data[next_block]["id"],
                    "fail": '',
                    "NumBlockFail": -1
                }
            continue

        # Парсим адрес jump
        try:
            target_jump = int(target_block_data["jumps"].rstrip('; '))
        except ValueError:
            logging.warning(f"Invalid jump value in block {target_block}")
            with open(f"error_log{time.time()}.txt", "a") as f:
                f.write(f"Invalid jump value in block {target_block}\n")
            continue

        # Парсим адрес fail (для условных переходов)
        if target_block_data["fails"] != '':
            try:
                target_fail = int(target_block_data["fails"].rstrip('; '))
            except ValueError:
                logging.warning(f"Invalid fail value in block {target_block}")
                with open(f"error_log{time.time()}.txt", "a") as f:
                    f.write(f"Invalid fail value in block {target_block}\n")
                continue

        # -- O(1)-поиск блока назначения jump --
        if target_jump in addr_to_key:
            found_key = addr_to_key[target_jump]
            if target_block != found_key:
                block_links = target_jump
                num_block_links = found_key

        links[target_block] = {
            "block": target_block_data["block"],
            "NumBlock": target_block_data["id"],
            "links": block_links,
            "NumBlockLinks": num_block_links,
            "fail": target_fail,
            "NumBlockFail": nbf
        }

        # -- O(1)-поиск блока назначения fail --
        if target_fail != '':
            if target_fail in addr_to_key:
                found_key = addr_to_key[target_fail]
                if target_block != found_key:
                    links[target_block]["fail"] = target_fail
                    links[target_block]["NumBlockFail"] = data[found_key]["id"]

    # print("block_links")
    return links  # orjson.dumps(links)
