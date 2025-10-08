import hashlib
import json
import re
import ppdeep
import Levenshtein
# from thefuzz import fuzz


def create_hasher(hash_type="ssdeep"):
    """
    Создает функцию хеширования в зависимости от типа.
    :param hash_type: Тип хеширования ("ssdeep", "md5", "sha256" и т.д.)
    :return: Функция хеширования
    """
    if hash_type == "ssdeep":
        return ppdeep.hash
    elif hash_type == "md5":
        return lambda x: hashlib.md5(x.encode()).hexdigest()
    elif hash_type == "sha256":
        return lambda x: hashlib.sha256(x.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash type: {hash_type}")


def generalize_opcode(opcode):
    # Словари для замены
    reg_patterns = [
        r'\b(rax|rbx|rcx|rdx|rsi|rdi|rbp|rsp|r8|r9|r10|r11|r12|r13|r14|r15|'
        r'eax|ebx|ecx|edx|esi|edi|ebp|esp|'
        r'ax|bx|cx|dx|si|di|bp|sp|'
        r'al|bl|cl|dl|ah|bh|ch|dh|'
        r'rip|eflags|flags)\b'
    ]

    mem_patterns = [
        r'\[.*\]',  # любая память в квадратных скобках
        r'ptr \[.*\]',  # с указанием размера (byte ptr, word ptr и т.д.)
    ]

    const_patterns = [
        r'0x[0-9a-fA-F]+',  # hex константы
        r'\b\d+\b',  # decimal константы
    ]

    # Заменяем регистры на REG
    for pattern in reg_patterns:
        opcode = re.sub(pattern, 'REG', opcode, flags=re.IGNORECASE)

    # Заменяем память на MEM
    for pattern in mem_patterns:
        opcode = re.sub(pattern, 'MEM', opcode, flags=re.IGNORECASE)

    # Заменяем константы на CONST
    for pattern in const_patterns:
        opcode = re.sub(pattern, 'CONST', opcode, flags=re.IGNORECASE)

    return opcode



def find_group(instruction):

    groups = {
        'DTI': ["BSWAP", "CBW", "CDQ", "CDQE", "CMOVA", "CMOVAE", "CMOVB", "CMOVBE", "CMOVC", "CMOVE", "CMOVG",
                "CMOVGE", "CMOVL", "COMVLE", "CMOVNA", "CMOVNAE", "CMOVNB", "CMOVNBE", "CMOVNC", "CMOVNE", "CMOVNG",
                "CMOVNGE", "CMOVNL", "CMOVNLE", "CMOVNO", "CMOVNP", "CMOVNS", "CMOVNZ", "CMOVO", "CMOVP", "CMOVPE",
                "CMOVPO", "CMOVS", "CMOVZ", "CMPXCHG", "CMPXCHG8B", "CQO", "CQO", "CWD", "CWDE", "MOV", "MOVABS",
                "MOVABS", "AL", "AX", "GAX", "RAX", "MOVSX", "MOVZX", "POP", "POPA", "POPAD", "PUSH", "PUSHA", "PUSHAD",
                "XADD", "XCHG", "RPUSH"],
        'BAI': ["ADC", "ADD", "CMP", "DEC", "DIV", "IDIV", "IMUL", "INC", "MUL", "NEG", "SBB", "SUB", "ACMP"],
        'DAI': ["AAA", "AAD", "AAM", "AAS", "DAA", "DAS"],
        'LI': ["AND", "NOT", "OR", "XOR"],
        'SHRI': ["RCL", "RCR", "ROL", "ROR", "SAL", "SAR", "SHL", "SHLD", "SHR", "SHRD"],
        'BBI': ["BSF", "BSR", "BT", "BTC", "BTR", "BTS", "SETA", "SETAE", "SETB", "SETBE", "SETC", "SETE", "SETG",
                "SETGE", "SETL", "SETLE", "SETNA", "SETNAE", "SETNB", "SETNBE", "SETNC", "SETNE", "SETNG", "SETNGE",
                "SETNL", "SETNLE", "SETNO", "SETNP", "SETNS", "SETNZ", "SETO", "SETP", "SETPE", "SETPO", "SETS", "SETZ",
                "TEST"],
        'CTI': ["BOUND", "CALL", "ENTER", "INT", "INTO", "IRET", "JA", "JAE", "JB", "JBE", "JC", "JCXZ", "JE", "JECXZ",
                "JG", "JGE", "JL", "JLE", "JMP", "JNAE", "JNB", "JNBE", "JNC", "JNE", "JNG", "JNGE", "JNL", "JNLE",
                "JNO", "JNP", "JNS", "JNZ", "JO", "JP", "JPE", "JPO", "JS", "JZ", "CALL", "LEAVE", "LOOP", "LOOPE",
                "LOOPNE", "LOOPNZ", "LOOPZ", "RET", "CJMP", "UCALL", "IRCALL", "IRJMP", "RJMP", "RCALL"],
        'SI': ["CMPS", "CMPSB", "CMPSD", "CMPSW", "LODS", "LODSB", "LODSD", "LODSW", "MOVS", "MOVSB", "MOVSD", "MOVSW",
               "REP", "REPNE", "REPNZ", "REPE", "REPZ", "SCAS", "SCASB", "SCASD", "SCASW", "STOS", "STOSB", "STOSD",
               "STOSW"],
        'IOI': ["IN", "INS", "INSB", "INSD", "INSW", "OUT", "OUTS", "OUTSB", "OUTSD", "OUTSW"],
        'FCI': ["CLC", "CLD", "CLI", "CMC", "LAHF", "POPF", "POPFL", "PUSHF", "PUSHFL", "SAHF", "STC", "STD", "STI"],
        'SRI': ["LDS", "LES", "LFS", "LGS", "LSS"],
        'MLI': ["CPUID", "LEA", "NOP", "UD2", "XLAT", "XLATB"]
    }

    for group_name, instructions in groups.items():
        if instruction in instructions:
            return group_name
    return False


# Функция генерации JSON объекта, c добавлением хеша ssdeep
def op_parser(func, hash_type='ssdeep'):
    """
    Начальный разделитель блоков CFG
    :param func: funk
    :param path: Путь к файлу
    :param hash_type: Тип хеширования
    :return: JSON
    """
    # with open(path, 'r') as f:
    # json_text = f.read()
    # data = json.loads(json_text)
    hasher = create_hasher(hash_type)
    mi = 0
    blocks = {}
    # Проходим через элементы списка верхнего уровня
    for item in func["cfg"]:
        # Проверяем, существует ли поле "blocks"
        if "blocks" in item:
            # Если существует, проходим через элементы в "blocks"
            for block in item["blocks"]:
                opcodes = []
                opcodes2 = ""
                types = ""
                # hash_opcodes = []
                hash_opcodes2 = ""
                jumps = ""
                fails = ""

                if "ops" in block:

                    for op in block["ops"]:

                        if "opcode" in op:
                            op['opcode'] = generalize_opcode(op['opcode'])
                            opcodes.append(op["opcode"])
                            opcodes2 = opcodes2 + op["opcode"] + "; "
                            # hash_opcodes.append(hasher(op["opcode"]))
                            hash_opcodes2 = hash_opcodes2 + (op["opcode"]) + "; "
                            aaa = op["type"].upper()

                            if aaa == 'NULL':
                                types += "NULL"

                            elif find_group(aaa) == False:
                                raise NotImplementedError("'type' is not in dictionary: " + str(aaa))

                            else:
                                types += str(find_group(aaa))
                                #print("From group:", find_group(aaa))

                    if "jump" in op:
                        jumps = jumps + str(op["jump"]) + "; "

                    if "fail" in op:
                        fails = fails + str(op["fail"]) + "; "

                    mi = mi + 1
                    item = {}
                    item['id'] = mi
                    item['block'] = block["addr"]
                    item['types'] = types
                    item['opcodes'] = opcodes2
                    item['hashssdeep'] = hasher(opcodes2)  # ppdeep.hash(opcodes2)
                    item['hash'] = (hashlib.md5(opcodes2.encode())).hexdigest()
                    item['jumps'] = jumps
                    item['fails'] = fails
                    blocks[mi] = item
    myjsondata = json.dumps(blocks)
    # print("op_parser")
    return myjsondata


#! Переписать в два цикла
def find_similar_blocks(json_data1, json_data2):
    """
    Нахождение максимально похожих по степени сравнения блоков
    :param json_data1:
    :param json_data2:
    :return: JSON
    """
    data1 = json.loads(json_data1)
    data2 = json.loads(json_data2)

    similar_blocks = {}
    klen = 0
    for block_id, block_data in data1.items():
        block_hash = block_data['hashssdeep']

        hash_equal = -1
        for compare_id, compare_data in data2.items():

            if(block_data['hash'] == compare_data['hash']):
                hash_equal = 1
            else:
                hash_equal = 0

            compare_hash = compare_data['hashssdeep']
            editdistance = Levenshtein.distance()
            similarity = ppdeep.compare(block_hash, compare_hash) # fuzz.ratio(block_hash, compare_hash)

            similar_blocks[klen] = {
                'block': block_id,
                'similar_to': compare_id,
                'simcount': similarity,
                'simequal': hash_equal
                #'editdistance': #TODO расстояние на строках, графах/ p235
            }
            klen += 1
    klen = 0
    similar_blocks_output = {}

    while len(similar_blocks) != 0:
            max_simcount = -1
            max_simcount_element = {}

            first_key, first_value = similar_blocks.popitem()
            similar_blocks[first_key] = first_value
            # Если нашли совершенно идентичные по крипто-хешу
            if similar_blocks[first_key]['simequal'] == 1:
                similar_blocks_output[klen] = similar_blocks[first_key]
                blocks_to_remove = []

                # Заполняем массив индексами элементов которые нужно удалить
                for block_num, block in similar_blocks.items():
                    if block['block'] == similar_blocks_output[klen]['block'] or block['similar_to'] == similar_blocks_output[klen]['similar_to']:
                        blocks_to_remove.append(block_num)

                # Удаляем все элементы с одинаковыми значениями block и similar_to
                for block in blocks_to_remove:
                    del similar_blocks[block]
                klen += 1
                continue

            for block_num, block_val in similar_blocks.items():
                if block_val['simcount'] > max_simcount:
                    max_simcount_element[0] = similar_blocks[block_num]
                    max_simcount = block_val['simcount']
                    # !!!Проверить max_simcount = block_val['simcount'] (добавлено)

            similar_blocks_output[klen] = max_simcount_element[0]
            blocks_to_remove = []

            # Заполняем массив индексами элементов которые нужно удалить
            for block_num, block in similar_blocks.items():
                if block['block'] == similar_blocks_output[klen]['block'] or block['similar_to'] == similar_blocks_output[klen]['similar_to']:
                    blocks_to_remove.append(block_num)

            # Удаляем все элементы с одинаковыми значениями block и similar_to
            for block in blocks_to_remove:
                del similar_blocks[block]
            klen += 1
    # print("find_similar_blocks")
    return json.dumps(similar_blocks_output)


