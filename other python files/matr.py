import json
import numpy as np

# Ваши JSON-объекты
json_object1 = {
    "1": {"block": 5368778762, "opcodes": "jmp 0x140014a80; ", "hashssdeep": "3:gvWzVIEd0F:gvm5OF", "jumps": "5368793728; "},
    "2": {"block": 5368793728, "opcodes": "mov qword [rsp + 0x18], r8; mov qword [rsp + 0x10], rdx; mov qword [rsp + 8], rcx; push rbp; push rdi; sub rsp, 0xe8; lea rbp, [rsp + 0x20]; lea rcx, [rip + 0x245a5]; call 0x140011ad2; jmp 0x140014abd; ", "hashssdeep": "6:jI3pE3xTIic7XwRtYDtKnAWiwNKeCVm54:mSYAA+Y1", "jumps": "5368793789; "},
    "3": {"block": 5368793771, "opcodes": "mov rax, qword [rbp + 0xe0]; add rax, 0x48; mov qword [rbp + 0xe0], rax; ", "hashssdeep": "3:3T2hM68wVJE3tEdJFLWJ+K8wV4:juh8w3E36L60K8wW", "jumps": ""}
}

json_object2 = {
    "1": {"block": 5368778762, "opcodes": "jmp 0x140014a80; ", "hashssdeep": "3:gvWzVIEd0F:gvm5OF", "jumps": "5368793728; "},
    "2": {"block": 5368793728, "opcodes": "mov qword [rsp + 0x18], r8; mov qword [rsp + 0x10], rdx; mov qword [rsp + 8], rcx; push rbp; push rdi; sub rsp, 0xe8; lea rbp, [rsp + 0x20]; lea rcx, [rip + 0x245a5]; call 0x140011ad2; jmp 0x140014abd; ", "hashssdeep": "6:jI3pE3xTIic7XwRtYDtKnAWiwNKeCVm54:mSYAA+Y1", "jumps": "5368793789; "},
    "3": {"block": 5368793771, "opcodes": "mov rax, qword [rbp + 0xe0]; add rax, 0x48; mov qword [rbp + 0xe0], rax; ", "hashssdeep": "3:3T2hM68wVJE3tEdJFLWJ+K8wV4:juh8w3E36L60K8wW", "jumps": ""}
}

json_object3 = {
    1: {"block": 5368778762, "similar_to": 5368778802, "simcount": 74},
    2: {"block": 5368793728, "similar_to": 5368787280, "simcount": 19},
    3: {"block": 5368793771, "similar_to": 5368778802, "simcount": 22},
    4: {"block": 5368793789, "similar_to": 5368787280, "simcount": 19},
    5: {"block": 5368793805, "similar_to": 5368778802, "simcount": 24},
    6: {"block": 5368793834, "similar_to": 5368778802, "simcount": 27}
}

# Получаем список всех блоков из обоих объектов
blocks_json1 = set(json_object1.keys())
blocks_json2 = set(json_object2.keys())
all_blocks = blocks_json1.union(blocks_json2)

# Создаем матрицу инцидентности
incident_matrix = np.zeros((len(all_blocks), len(all_blocks)), dtype=int)

# Заполняем матрицу инцидентности на основе второго JSON-объекта
for key, value in json_object3.items():
    row_index = list(all_blocks).index(value["block"])
   col_index = list(all_blocks).index(value["similar_to"])
   incident_matrix[row_index, col_index] = value["simcount"]

# Выводим матрицу инцидентности
print(incident_matrix)
