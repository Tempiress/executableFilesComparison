import hashlib
import json
import time
import re
import pyssdeep
import Levenshtein
import tlsh
from thefuzz import fuzz
import sys
from functools import lru_cache
sys.path.append(r"D:\programming2025\MyResearch\pyLZJD")
from pyLZJD import lzjd
import sdhash
from nilsimsa import Nilsimsa, compare_digests


@lru_cache(maxsize=100000)
def cached_ppdeep_compare(hash1, hash2):
    return pyssdeep.compare(hash1, hash2)

@lru_cache(maxsize=100000)
def cached_levenshtein(str1, str2):
    return Levenshtein.distance(str1, str2)


def create_hasher(hash_type):
    if hash_type == "ssdeep":
        return pyssdeep.get_hash_buffer  # ssdeep hashing
    elif hash_type == "tlsh":
        def tlsh_wrapper(data):
            if len(data) < 50:
                data += b' ' * (50 - len(data))  # дополняем пробелами
            return tlsh.hash(data)

        return tlsh_wrapper
    elif hash_type == "lzjd":
        return lzjd.hash  # lzjd должен быть импортирован
    elif hash_type == "nilsimsa":
        def nilsimsa_wrapper(data):
            n = Nilsimsa(data)
            return n.hexdigest()

        return nilsimsa_wrapper
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


class GroupInstructions:
    groups = {
        'DTI': ["BSWAP", "CBW", "CDQ", "CDQE", "CMOV", "CMOVA", "CMOVAE", "CMOVB", "CMOVBE", "CMOVC", "CMOVE", "CMOVG",
                "CMOVGE", "CMOVL", "COMVLE", "CMOVNA", "CMOVNAE", "CMOVNB", "CMOVNBE", "CMOVNC", "CMOVNE", "CMOVNG",
                "CMOVNGE", "CMOVNL", "CMOVNLE", "CMOVNO", "CMOVNP", "CMOVNS", "CMOVNZ", "CMOVO", "CMOVP", "CMOVPE",
                "CMOVPO", "CMOVS", "CMOVZ", "CMPXCHG", "CMPXCHG8B", "CQO", "CQO", "CWD", "CWDE", "MOV", "MOVABS",
                "MOVABS", "AL", "AX", "GAX", "RAX", "MOVSX", "MOVZX", "POP", "POPA", "POPAD", "UPUSH", "PUSH", "PUSHA",
                "PUSHAD",
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
                "JG", "JGE", "JL", "JLE", "JMP", "UJMP", "JNAE", "JNB", "JNBE", "JNC", "JNE", "JNG", "JNGE", "JNL", "JNLE",
                "JNO", "JNP", "JNS", "JNZ", "JO", "JP", "JPE", "JPO", "JS", "JZ", "CALL", "LEAVE", "LOOP", "LOOPE",
                "LOOPNE", "LOOPNZ", "LOOPZ", "RET", "CJMP", "UCALL", "IRCALL", "IRJMP", "RJMP", "RCALL"],
        'SI': ["CMPS", "CMPSB", "CMPSD", "CMPSW", "LODS", "LODSB", "LODSD", "LODSW", "MOVS", "MOVSB", "MOVSD", "MOVSW",
               "REP", "REPNE", "REPNZ", "REPE", "REPZ", "SCAS", "SCASB", "SCASD", "SCASW", "STOS", "STOSB", "STOSD",
               "STOSW"],
        'IOI': ["IN", "INS", "INSB", "INSD", "INSW", "OUT", "OUTS", "OUTSB", "OUTSD", "OUTSW"],
        'FCI': ["CLC", "CLD", "CLI", "CMC", "LAHF", "POPF", "POPFL", "PUSHF", "PUSHFL", "SAHF", "STC", "STD", "STI"],
        'SRI': ["LDS", "LES", "LFS", "LGS", "LSS"],
        'MLI': ["CPUID", "LEA", "NOP", "UD2", "XLAT", "XLATB"],
        'UNKNOWN': ["IO", "ILL", "LOAD", "STORE", "TRAP", "MJMP", "SWI"]
    }

    def find_group(self, instruction: str):
        instruction = instruction.upper()
        for group_name, instructions in self.groups.items():
            if instruction in instructions:
                return group_name
        return False

    def find_group_index(self, group: str):
        return list(self.groups).index(group)

    def group_number_parser(self, group: str):
        g = int(group)
        if g < 10:
            return group
        elif g == 10:
            return "A"
        elif g == 11:
            return "B"
        elif g == 12:
            return "C"
        elif g == 13:
            return "D"


# Функция генерации JSON объекта, c добавлением хеша ssdeep
def op_parser(func, config):
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

    gi = GroupInstructions()
    hasher = create_hasher(config.hash_type)
    mi = 0
    blocks = {}
    # Проходим через элементы списка верхнего уровня
    for item in func["cfg"]:
        # Проверяем, существует ли поле "blocks"
        if "blocks" in item:
            # Если существует, проходим через элементы в "blocks"
            for block in item["blocks"]:
                opcodes = ""
                opcodes2 = ""
                types = ""
                # hash_opcodes = []
                hash_opcodes2 = ""
                jumps = ""
                fails = ""
                group_numbers = ""

                if "ops" in block:
                    for op in block["ops"]:
                        if "opcode" in op:
                            # Получаем базовый опкод
                            base_opcode = op['opcode']
                            opcode = base_opcode


                            # Обработка режимов
                            if config.instructions_mode in ['generalize', 'both']:
                                opcode = generalize_opcode(base_opcode)

                            if config.instructions_mode in ['group', 'group_only', 'both']:
                                # opcode = gi.find_group(opcode) or opcode
                                aaa = op.get("type", "null")
                                if aaa == 'null':
                                    opcode = 'NULL'
                                    group_name = 'NULL'
                                else:
                                    found_group = gi.find_group(aaa)
                                    # opcode = opcode.replace(aaa, found_group)
                                    if found_group is not False:
                                        parts = opcode.split(maxsplit=1)

                                        if len(parts) > 1:
                                            opcode = f"{found_group} {parts[1]}"

                                    else:
                                        raise NotImplementedError("'type' is not in dictionary: " + str(aaa))
                            

                            if config.instructions_mode in ['none']:
                                # Если режим не generalize и не group, оставляем как есть
                                opcode = base_opcode

                            opcodes = opcodes + base_opcode + "; "
                            opcodes2 = opcodes2 + opcode + "; "
                            # hash_opcodes.append(hasher(op["opcode"]))
                            hash_opcodes2 = hash_opcodes2 + opcode + "; "
                            # op["type"]
                            aaa = op.get("type", "null")

                            if aaa == 'null':
                                types += "NULL"
                                group_numbers += "D"
                            else:
                                types += str(gi.find_group(aaa))
                                group_numbers += gi.group_number_parser(str(gi.find_group_index(gi.find_group(aaa))))

                    if "jump" in op:
                        jumps = jumps + str(op["jump"]) + ";"

                    if "fail" in op:
                        fails = fails + str(op["fail"]) + ";"

                    mi = mi + 1
                    item = {}
                    item['id'] = mi
                    item['block'] = block["addr"]
                    #item['types'] = types
                    item['opcodes'] = opcodes2
                    item['fuzzyhash'] = hasher(opcodes2.encode()) if config.instructions_mode != 'group_only' else ''
                    item['hash'] = (hashlib.md5(opcodes.encode())).hexdigest()
                    item['jumps'] = jumps
                    item['fails'] = fails
                    item['number_group'] = group_numbers
                    blocks[mi] = item
    #myjsondata = json.dumps(blocks)

    return blocks #myjsondata


def find_similar_blocks(json_data1, json_data2, config):
    """
    Нахождение максимально похожих по степени сравнения блоков
    :param json_data1:
    :param json_data2:
    :return: JSON
    """

    data1 = json_data1
    data2 = json_data2

    all_pairs = []
    klen = 0
    for block_id, block_data in data1.items():
        block_hash = block_data['fuzzyhash']


        for compare_id, compare_data in data2.items():
            compare_hash = compare_data['fuzzyhash']

            hash_equal = 1 if block_data['hash'] == compare_data['hash'] else 0

            if hash_equal == 1:
                similarity = 100  # ppdeep выдаёт 100 для идентичных хэшей
                edit_dist = 0
            else:
                if config.instructions_mode in ["group_only"]:
                    edit_dist = cached_levenshtein(block_data["number_group"], compare_data["number_group"])
                    # group_only: не используем fuzzyhash, только Левенштейн по group-последовательности
                    # Порядок элементов совпадает с читающим кодом: [0]=hash_equal,[1]=is_same_addr,[2]=similarity,[3]=-edit_dist,[4]=block_id,[5]=compare_id
                    all_pairs.append((hash_equal,
                        1 if block_data['block'] == compare_data['block'] else 0,
                        0,          # similarity=0 (fuzzyhash не считаем)
                        -edit_dist,
                        block_id,
                        compare_id
                        ))
                    continue

                    
                if config.hash_type == 'ssdeep':
                    similarity = cached_ppdeep_compare(block_hash, compare_hash)  # fuzz.ratio(block_hash, compare_hash)
                elif config.hash_type == 'tlsh':
                    similarity = tlsh.diff(block_hash, compare_hash)
                elif config.hash_type == 'lzjd':
                    similarity = lzjd.sim(block_hash, compare_hash)
                elif config.hash_type == 'nilsimsa':
                    similarity = compare_digests(block_hash, compare_hash)

                else:
                    similarity = fuzz.ratio(block_hash, compare_hash)

                edit_dist = cached_levenshtein(block_data["number_group"], compare_data["number_group"])

            # ДОБАВЛЯЕМ В ВИДЕ КОРТЕЖА (tuple)
            # Порядок: [0]=hash_equal, [1]=is_same_addr, [2]=similarity, [3]=-edit_dist, [4]=block_id, [5]=compare_id
            # Минус перед edit_dist нужен, чтобы сортировка по убыванию поставила наименьшее расстояние наверх
            all_pairs.append((hash_equal,
                              1 if block_data['block'] == compare_data['block'] else 0,
                              similarity,
                              -edit_dist,
                              block_id,
                              compare_id))



    # Сортируем:
    # 1. Сначала крипто-хэш
    # 2. ПОТОМ СОВПАДЕНИЕ АДРЕСОВ - это гарантирует 100% для одинаковых функций
    # 3. Потом simcount (по убыванию)
    # 4. Редакционное расстояние (по возрастанию)
    # all_pairs.sort(key=lambda x: (x['simequal'], x['is_same_id'], x['simcount'], -x['editdistance']), reverse=True)
    all_pairs.sort(reverse=True)


    similar_blocks_output = {}
    used_blocks1 = set()
    used_blocks2 = set()
    klen = 0

    for pair in all_pairs:
        b1 = pair[4] # pair['block']
        b2 = pair[5] # pair['similar_to']

        if b1 not in used_blocks1 and b2 not in used_blocks2:
            similar_blocks_output[klen] = {
                'block': b1,
                'similar_to': b2,
                'simcount': pair[2],
                'simequal': pair[0],
                'editdistance': -pair[3]
            }
            used_blocks1.add(b1)
            used_blocks2.add(b2)
            klen += 1

    return similar_blocks_output
