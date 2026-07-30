"""
Instruction normalisation and block-similarity matching.
"""

import hashlib
import re
import sys
import code_rust

from src.core.config import AnalysisConfig
from src.core.hashing import (
    create_hasher,
    cached_ppdeep_compare,
    cached_levenshtein,
    lazy_tlsh_diff,
    lazy_nilsimsa_compare,
    lazy_fuzz_ratio,
)


_REGISTER_PATTERN = re.compile(
    r'\b(rax|rbx|rcx|rdx|rsi|rdi|rbp|rsp|r8|r9|r10|r11|r12|r13|r14|r15|'
    r'eax|ebx|ecx|edx|esi|edi|ebp|esp|'
    r'ax|bx|cx|dx|si|di|bp|sp|'
    r'al|bl|cl|dl|ah|bh|ch|dh|'
    r'rip|eflags|flags)\b',
    re.IGNORECASE,
)

_MEMORY_PATTERN_BRACKET = re.compile(r'\[.*\]', re.IGNORECASE)
_MEMORY_PATTERN_PTR = re.compile(r'ptr \[.*\]', re.IGNORECASE)
_CONST_HEX_PATTERN = re.compile(r'0x[0-9a-fA-F]+', re.IGNORECASE)
_CONST_DEC_PATTERN = re.compile(r'\b\d+\b', re.IGNORECASE)


def generalize_instruction(opcode: str) -> str:
    """Replace registers/memory/constants with normalised tokens (REG, MEM, CONST)."""
    opcode = _REGISTER_PATTERN.sub('REG', opcode)
    opcode = _MEMORY_PATTERN_PTR.sub('MEM', opcode)
    opcode = _MEMORY_PATTERN_BRACKET.sub('MEM', opcode)
    opcode = _CONST_HEX_PATTERN.sub('CONST', opcode)
    opcode = _CONST_DEC_PATTERN.sub('CONST', opcode)
    return opcode


class GroupInstructions:
    """Maps x86 instruction mnemonics into 13 semantic groups."""

    INSTRUCTION_GROUPS = {
        'DTI': [
            "BSWAP", "CBW", "CDQ", "CDQE", "CMOV", "CMOVA", "CMOVAE", "CMOVB",
            "CMOVBE", "CMOVC", "CMOVE", "CMOVG", "CMOVGE", "CMOVL", "COMVLE",
            "CMOVNA", "CMOVNAE", "CMOVNB", "CMOVNBE", "CMOVNC", "CMOVNE",
            "CMOVNG", "CMOVNGE", "CMOVNL", "CMOVNLE", "CMOVNO", "CMOVNP",
            "CMOVNS", "CMOVNZ", "CMOVO", "CMOVP", "CMOVPE", "CMOVPO", "CMOVS",
            "CMOVZ", "CMPXCHG", "CMPXCHG8B", "CQO", "CWD", "CWDE", "MOV",
            "MOVABS", "MOVSX", "MOVZX", "POP", "POPA", "POPAD", "PUSH", "PUSHA",
            "PUSHAD", "UPUSH", "RPUSH", "XADD", "XCHG",
        ],
        'BAI': ["ADC", "ADD", "CMP", "DEC", "DIV", "IDIV", "IMUL", "INC",
                "MUL", "NEG", "SBB", "SUB", "ACMP"],
        'DAI': ["AAA", "AAD", "AAM", "AAS", "DAA", "DAS"],
        'LI':  ["AND", "NOT", "OR", "XOR"],
        'SHRI': ["RCL", "RCR", "ROL", "ROR", "SAL", "SAR", "SHL", "SHLD",
                 "SHR", "SHRD"],
        'BBI': ["BSF", "BSR", "BT", "BTC", "BTR", "BTS", "SETA", "SETAE",
                "SETB", "SETBE", "SETC", "SETE", "SETG", "SETGE", "SETL",
                "SETLE", "SETNA", "SETNAE", "SETNB", "SETNBE", "SETNC", "SETNE",
                "SETNG", "SETNGE", "SETNL", "SETNLE", "SETNO", "SETNP", "SETNS",
                "SETNZ", "SETO", "SETP", "SETPE", "SETPO", "SETS", "SETZ", "TEST"],
        'CTI': ["BOUND", "CALL", "ENTER", "INT", "INTO", "IRET", "JA", "JAE",
                "JB", "JBE", "JC", "JCXZ", "JE", "JECXZ", "JG", "JGE", "JL",
                "JLE", "JMP", "UJMP", "JNAE", "JNB", "JNBE", "JNC", "JNE",
                "JNG", "JNGE", "JNL", "JNLE", "JNO", "JNP", "JNS", "JNZ", "JO",
                "JP", "JPE", "JPO", "JS", "JZ", "LEAVE", "LOOP", "LOOPE",
                "LOOPNE", "LOOPNZ", "LOOPZ", "RET", "CJMP", "UCALL", "IRCALL",
                "IRJMP", "RJMP", "RCALL"],
        'SI':  ["CMPS", "CMPSB", "CMPSD", "CMPSW", "LODS", "LODSB", "LODSD",
                "LODSW", "MOVS", "MOVSB", "MOVSD", "MOVSW", "REP", "REPNE",
                "REPNZ", "REPE", "REPZ", "SCAS", "SCASB", "SCASD", "SCASW",
                "STOS", "STOSB", "STOSD", "STOSW"],
        'IOI': ["IN", "INS", "INSB", "INSD", "INSW", "OUT", "OUTS", "OUTSB",
                "OUTSD", "OUTSW"],
        'FCI': ["CLC", "CLD", "CLI", "CMC", "LAHF", "POPF", "POPFL", "PUSHF",
                "PUSHFL", "SAHF", "STC", "STD", "STI"],
        'SRI': ["LDS", "LES", "LFS", "LGS", "LSS"],
        'MLI': ["CPUID", "LEA", "NOP", "UD2", "XLAT", "XLATB"],
        'UNKNOWN': ["IO", "ILL", "LOAD", "STORE", "TRAP", "MJMP", "SWI"],
    }

    _mnemonic_to_group: dict = {}
    _group_names: list = []

    def __init__(self):
        if not GroupInstructions._mnemonic_to_group:
            for gname, mnems in GroupInstructions.INSTRUCTION_GROUPS.items():
                for mnem in mnems:
                    GroupInstructions._mnemonic_to_group[mnem.upper()] = gname
            GroupInstructions._group_names = list(GroupInstructions.INSTRUCTION_GROUPS.keys())

    @classmethod
    def find_group(cls, mnemonic: str):
        return cls._mnemonic_to_group.get(mnemonic.upper(), False)

    @classmethod
    def group_index(cls, group_name: str) -> int:
        return cls._group_names.index(group_name)

    @staticmethod
    def group_short_code(group_index: str) -> str:
        idx = int(group_index)
        return str(idx) if idx < 10 else chr(ord('A') + idx - 10)


def parse_function_blocks(func_cfg: dict, config: AnalysisConfig) -> dict:
    """Parse a function CFG into normalised basic blocks."""
    groups = GroupInstructions()
    hasher = create_hasher(config.hash_type)
    block_index = 0
    parsed_blocks = {}

    for cfg_item in func_cfg.get("cfg", []):
        if "blocks" not in cfg_item:
            continue
        for block in cfg_item.get("blocks", []):
            if "ops" not in block:
                continue

            raw_opcodes = []
            normalised_opcodes = []
            type_sequence = ""
            jump_targets = ""
            fail_targets = ""
            group_code_sequence = ""

            for op in block["ops"]:
                if "opcode" not in op:
                    continue
                base_opcode = op['opcode']
                opcode = base_opcode

                if config.instructions_mode in ('generalize', 'both'):
                    opcode = generalize_instruction(base_opcode)

                if config.instructions_mode in ('group', 'group_only', 'both'):
                    op_type = op.get("type", "null")
                    if op_type == 'null':
                        opcode = 'NULL'
                        group_name = 'NULL'
                    else:
                        group_name = groups.find_group(op_type)
                        if group_name is not False:
                            parts = opcode.split(maxsplit=1)
                            if len(parts) > 1:
                                opcode = f"{group_name} {parts[1]}"
                        else:
                            raise NotImplementedError(f"'type' not in dictionary: {op_type}")

                if config.instructions_mode == 'none':
                    opcode = base_opcode

                raw_opcodes.append(base_opcode)
                normalised_opcodes.append(opcode)

                op_type = op.get("type", "null")
                if op_type == 'null':
                    type_sequence += "NULL"
                    group_code_sequence += "D"
                else:
                    gname = groups.find_group(op_type)
                    type_sequence += str(gname)
                    group_code_sequence += groups.group_short_code(str(groups.group_index(gname)))

                if op.get("jump"):
                    jump_targets += str(op["jump"]) + ";"
                if op.get("fail"):
                    fail_targets += str(op["fail"]) + ";"

            block_index += 1
            opcodes_str = "; ".join(normalised_opcodes) + "; " if normalised_opcodes else ""
            parsed_blocks[block_index] = {
                'id': block_index,
                'block': block["addr"],
                'opcodes': opcodes_str,
                'fuzzyhash': (
                    hasher(opcodes_str.encode())
                    if config.instructions_mode != 'group_only'
                    else ''
                ),
                'hash': hashlib.md5(
                    ("; ".join(raw_opcodes) + "; " if raw_opcodes else "").encode()
                ).hexdigest(),
                'jumps': jump_targets,
                'fails': fail_targets,
                'number_group': group_code_sequence,
            }

    return parsed_blocks


def match_similar_blocks(blocks_a: dict, blocks_b: dict, config: AnalysisConfig) -> dict:
    # Вызываем сверхбыструю функцию на Rust
    raw_matches = code_rust.match_similar_blocks_rust(
        blocks_a, blocks_b, config.instructions_mode, config.hash_type
    )

    # Форматируем результат в нужный для обратной совместимости словарь
    matched = {}
    for idx, (bid_a, bid_b, similarity, simequal) in enumerate(raw_matches):
        matched[idx] = {
            'block': bid_a,
            'similar_to': bid_b,
            'simcount': similarity,
            'simequal': simequal,
            'editdistance': 0  # (или передать из Rust при необходимости)
        }
    return matched
