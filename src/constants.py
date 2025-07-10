from typing import List, Set, Dict
from definitions import (
    TokenType,
    BitFieldSpec,
    ConstantField,
    RegisterField,
    NumericField,
    PunctuationField,
)
import time

INSTRUCTION_FORMAT: Dict[str, List[PunctuationField | BitFieldSpec]] = {
    "add": [
        ConstantField(0, 2, "000"),  # opcode
        ConstantField(3, 5, "000"),  # funct3
        RegisterField(6, 8, TokenType.REGISTER),  # rd/rs1
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),  # rs2
        ConstantField(12, 15, "0000"),  # funct4
    ],
    "sub": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "000"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0001"),
    ],
    "slt": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "001"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0010"),
    ],
    "sltu": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "010"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0011"),
    ],
    "sll": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "011"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0100"),
    ],
    "srl": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "011"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0101"),
    ],
    "sra": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "011"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0110"),
    ],
    "or": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "100"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0111"),
    ],
    "and": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "101"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1000"),
    ],
    "xor": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "110"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1001"),
    ],
    "mv": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "111"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1010"),
    ],
    "jr": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "000"),
        RegisterField(6, 8, TokenType.REGISTER),
        ConstantField(9, 11, "000"),  # rs2 = zero
        ConstantField(12, 15, "1011"),
    ],
    "jalr": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "000"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1100"),
    ],
    # I-Type Instructions (opcode 001)
    "addi": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "000"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 15),
    ],
    "slti": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "001"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 15),
    ],
    "sltui": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "010"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 15),
    ],
    "slli": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "011"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 12),  # shift amount[2:0]
        ConstantField(13, 15, "001"),
    ],
    "srli": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "011"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 12),
        ConstantField(13, 15, "010"),
    ],
    "srai": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "011"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 12),
        ConstantField(13, 15, "100"),
    ],
    "ori": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "100"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 15),
    ],
    "andi": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "101"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 15),
    ],
    "xori": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "110"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 15),
    ],
    "li": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "111"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(9, 15),
    ],
    # B-Type Instructions (opcode 010)
    "beq": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "000"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    "bne": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "001"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    "bz": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "010"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    "bnz": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "011"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    "blt": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "100"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    "bge": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "101"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    "bltu": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "110"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    "bgeu": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "111"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15, label=True),
    ],
    # S-Type Instructions (opcode 011)
    "sb": [
        ConstantField(0, 2, "011"),
        ConstantField(3, 5, "000"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15),
        PunctuationField(TokenType.LPAREN),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    "sw": [
        ConstantField(0, 2, "011"),
        ConstantField(3, 5, "001"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15),
        PunctuationField(TokenType.LPAREN),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    # L-Type Instructions (opcode 100)
    "lb": [
        ConstantField(0, 2, "100"),
        ConstantField(3, 5, "000"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15),
        PunctuationField(TokenType.LPAREN),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    "lw": [
        ConstantField(0, 2, "100"),
        ConstantField(3, 5, "001"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15),
        PunctuationField(TokenType.LPAREN),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    "lbu": [
        ConstantField(0, 2, "100"),
        ConstantField(3, 5, "100"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(12, 15),
        PunctuationField(TokenType.LPAREN),
        RegisterField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    "j": [
        ConstantField(0, 2, "101"),
        NumericField(
            allocations=[
                BitFieldSpec(beginning=3, end=5),
                BitFieldSpec(beginning=9, end=14),
            ],
            label=True,
        ),
        ConstantField(15, 15, "0"),
    ],
    "jal": [
        ConstantField(0, 2, "101"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(
            allocations=[
                BitFieldSpec(beginning=3, end=5),
                BitFieldSpec(beginning=9, end=14),
            ],
            label=True,
        ),
        ConstantField(15, 15, "1"),
    ],
    # U-Type Instructions (opcode 110)
    "lui": [
        ConstantField(0, 2, "110"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(
            allocations=[
                BitFieldSpec(beginning=3, end=5),
                BitFieldSpec(beginning=9, end=14),
            ],
            signed=False,
        ),
        ConstantField(15, 15, "0"),
    ],
    "auipc": [
        ConstantField(0, 2, "110"),
        RegisterField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        NumericField(
            allocations=[
                BitFieldSpec(beginning=3, end=5),
                BitFieldSpec(beginning=9, end=14),
            ],
            signed=False,
        ),
        ConstantField(15, 15, "1"),
    ],
    # SYS-Type Instructions (opcode 111)
    "ecall": [
        ConstantField(0, 2, "111"),
        NumericField(6, 15),
    ],
}
# Pseudo-instructions sizes in bytes
PSEUDO_INSTRUCTIONS = {
    "li16": 4,
    "la": 4,
    "push": 4,
    "pop": 4,
    "call": 2,
    "ret": 2,
    "inc": 2,
    "dec": 2,
    "neg": 4,
    "not": 2,
    "clr": 2,
    "nop": 2,
}
current_date = time.strftime("%Y-%m-%d", time.localtime())
current_time = time.strftime("%H:%M:%S", time.localtime())

DEFAULT_SYMBOLS = {
   "__ZX16__" : 1,
    "__ASSEMBLER__": "zx16asm",
    "__VERSION__": "1.0.0",
    "__DATE__": current_date,
    "__TIME__": current_time,
    "__WORD_SIZE__" :2,
    "__DATA_SIZE__ ": 16,
    "__ADDR_SIZE__ " : 16,
    "T0": 0,
    "RA": 1,
    "SP": 2,
    "S0": 3,
    "S1": 4,
    "T1": 5,
    "A0": 6,
    "A1": 7,
    "RESET_VECTOR": 0x0000,
    "INT_VECTORS": 0x0000,  # Interrupt vector table start
    "CODE_START": 0x0020,  # Default code start
    "MMIO_BASE": 0xF000,  # Memory-mapped I/O base
    "MMIO_SIZE": 0x1000,  # MMIO region size
    "STACK_TOP": 0xEFFE,  # Default stack top
    "MEM_SIZE": 0x10000,  # Total memory size (64KB)
}

char_tokens = {
    ",": TokenType.COMMA,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "+": TokenType.OPERATOR,
    "-": TokenType.OPERATOR,
    "*": TokenType.OPERATOR,
    "/": TokenType.OPERATOR,
    "%": TokenType.OPERATOR,
    "^": TokenType.OPERATOR,
    "|": TokenType.OPERATOR,
    "&": TokenType.OPERATOR,
    "~": TokenType.OPERATOR,
}
RESERVED_KEYWORDS = (
    INSTRUCTION_FORMAT.keys() | PSEUDO_INSTRUCTIONS.keys() | DEFAULT_SYMBOLS.keys()
)

TOKEN_TYPE_NAMES = {
    TokenType.IDENTIFIER: "identifier",
    TokenType.REGISTER: "register",
    TokenType.IMMEDIATE: "immediate",
    TokenType.LABEL_DEF: "label definition",
    TokenType.LABEL_USE: "label use",
    TokenType.DIRECTIVE: "directive",
    TokenType.STRING: "string",
    TokenType.NEWLINE: "newline",
    TokenType.COMMA: "comma",
    TokenType.LPAREN: "left parenthesis",
    TokenType.RPAREN: "right parenthesis",
    TokenType.OPERATOR: "operator",
    TokenType.EOF: "end of file",
}
