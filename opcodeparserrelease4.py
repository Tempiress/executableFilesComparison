import json
import ppdeep
from thefuzz import fuzz, process
import pdb


# pdb.set_trace()
def op_parser(path):
    '''
    Начальный разделитель блоков CFG
    :param path:
    :return:JSON
    '''

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
                        item['block'] = block["offset"]
                        item['opcodes'] = opcodes2
                        item['hashssdeep'] = ppdeep.hash(opcodes2)
                        item['jumps'] = jumps
                        blocks[mi] = item
    myjsondata = json.dumps(blocks)
    print(myjsondata)
    return myjsondata


# Функция сравнения файлов
def cfg_comp():
    '''

    :return: JSON
    '''
    dt1 = op_parser('D:\\MyNauchWork\\cfg\\cfg_5368778757.txt')
    data1 = json.loads(dt1)
    dt2 = op_parser('D:\\MyNauchWork\\cfg\\cfg_5368778802.txt')
    data2 = json.loads(dt2)

    # будущий JSON объект
    item = {}
    ki = 0
    # Сравните блоки из первого файла со всеми блоками из второго файла
    for key1, block1 in data1.items():

        # Пропускаем, если блок1 уже был сопоставлен
        if 'matched' in block1:
            continue

        comp_res = {}
        comp_res[key1] = {}
        summar = []
        ki += 1

        for key2, block2 in data2.items():
            # Пропускаем, если блок2 уже был сопоставлен
            if 'matched' in block2:
                continue

            f_hash = fuzz.ratio(block1['hashssdeep'], block2['hashssdeep'])

            # Проверяем на первое сравнение блоков
            if (comp_res[key1] != {}):
                numb = comp_res.get(key1)
                if (numb[1] is not None and f_hash > numb[1]):
                    summar[0] = block2["block"]
                    summar[1] = f_hash
                    comp_res[key1] = summar
            else:
                summar.append(block2["block"])
                summar.append(f_hash)

                comp_res[key1] = summar

        # Обновим блок в data1 соответствующей информацией
        data1[key1]['matched'] = True
        if summar:
            data2[key2]['matched'] = True

        comp_res['block'] = block1["block"]
        comp_res["similar_to"] = summar[0] if summar else None
        comp_res["simcount"] = summar[1] if summar else None
        del comp_res[key1]
        item[ki] = comp_res
        # del data1[key1]

    # print(json.dumps(comp_res))
    print(json.dumps(item))


cfg_comp()
