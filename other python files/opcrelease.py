import json

import ppdeep
from thefuzz import fuzz


def opparcer(path):

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
    return myjsondata


#Функция сравнения блоков
def compare_blocks(block1, block2):
    print(block1['hashssdeep'], block2['hashssdeep'])
    return fuzz.ratio(block1['hashssdeep'], block2['hashssdeep'])


#Функция сравнения файлов
def cfgcomp():
    dt1 = opparcer('D:\\MyNauchWork\\cfg\\cfg_5368778757.txt')
    data1 = json.loads(dt1)
    dt2 = opparcer('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt')
    data2 = json.loads(dt2)
    
    comp_res = {}
    # Сравните блоки из первого файла со всеми блоками из второго файла
    for key1, block1 in data1.items():
        comp_res[key1] = {}
        for key2, block2 in data2.items():
            comp_res[key1][key2] = fuzz.ratio(block1['hashssdeep'], block2['hashssdeep'])


    print(json.dumps(comp_res, indent=4))
cfgcomp()








