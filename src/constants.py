from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal, List
import sys


class TokenType(Enum):
    """Token types for lexical analysis."""

    IDENTIFIER = auto()
    REGISTER = auto()
    IMMEDIATE = auto()
    LABEL = auto()
    DIRECTIVE = auto()
    STRING = auto()
    CHARACTER = auto()
    NEWLINE = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    OPERATOR = auto()
    EOF = auto()


class Opcode(Enum):
    """ZX16 opcode."""

    R_TYPE = 0b000
    I_TYPE = 0b001
    B_TYPE = 0b010
    S_TYPE = 0b011
    L_TYPE = 0b100
    J_TYPE = 0b101
    U_TYPE = 0b110
    SYS_TYPE = 0b111


TRUE_INSTRUCTIONS = {
    # R-Type
    "add": Opcode.R_TYPE,
    "sub": Opcode.R_TYPE,
    "slt": Opcode.R_TYPE,
    "sltu": Opcode.R_TYPE,
    "sll": Opcode.R_TYPE,
    "srl": Opcode.R_TYPE,
    "sra": Opcode.R_TYPE,
    "or": Opcode.R_TYPE,
    "and": Opcode.R_TYPE,
    "xor": Opcode.R_TYPE,
    "mv": Opcode.R_TYPE,
    "jr": Opcode.R_TYPE,
    "jalr": Opcode.R_TYPE,
    # I-Type
    "addi": Opcode.I_TYPE,
    "slti": Opcode.I_TYPE,
    "sltui": Opcode.I_TYPE,
    "slli": Opcode.I_TYPE,
    "srli": Opcode.I_TYPE,
    "srai": Opcode.I_TYPE,
    "ori": Opcode.I_TYPE,
    "andi": Opcode.I_TYPE,
    "xori": Opcode.I_TYPE,
    "li": Opcode.I_TYPE,
    # B-Type
    "beq": Opcode.B_TYPE,
    "bne": Opcode.B_TYPE,
    "bz": Opcode.B_TYPE,
    "bnz": Opcode.B_TYPE,
    "blt": Opcode.B_TYPE,
    "bge": Opcode.B_TYPE,
    "bltu": Opcode.B_TYPE,
    "bgeu": Opcode.B_TYPE,
    # S-Type
    "sb": Opcode.S_TYPE,
    "sw": Opcode.S_TYPE,
    # L-Type
    "lb": Opcode.L_TYPE,
    "lw": Opcode.L_TYPE,
    "lbu": Opcode.L_TYPE,
    # J-Type
    "j": Opcode.J_TYPE,
    "jal": Opcode.J_TYPE,
    # U-Type
    "lui": Opcode.U_TYPE,
    "auipc": Opcode.U_TYPE,
    # SYS-Type
    "ecall": Opcode.SYS_TYPE,
}


@dataclass
class MemoryAllocation:
    # Memory allocation
    m_beginning: int = None
    m_end: int = None
    # Immediate Allocation
    i_beginning: int = None
    i_end: int = None


# TODO: See if this can be a parent class for Placeholder
@dataclass
class Placeholder:
    """Represents the operands of an instruction."""

    expected_token: TokenType = None
    const_value: str = None
    allocations: List[MemoryAllocation] = None
    beginning: int = 0
    end: int = 0
    # TODO: add immediate value range


INSTRUCTION_FORMAT = {
    # R-Type Instructions (opcode 000)
    "add": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0000", beginning=12, end=15),  # funct4
    ],
    "sub": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0001", beginning=12, end=15),  # funct4
    ],
    "slt": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="001", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0010", beginning=12, end=15),  # funct4
    ],
    "sltu": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="010", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0011", beginning=12, end=15),  # funct4
    ],
    "sll": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="011", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0100", beginning=12, end=15),  # funct4
    ],
    "srl": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="011", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0101", beginning=12, end=15),  # funct4
    ],
    "sra": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="011", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0110", beginning=12, end=15),  # funct4
    ],
    "or": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="100", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="0111", beginning=12, end=15),  # funct4
    ],
    "and": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="101", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="1000", beginning=12, end=15),  # funct4
    ],
    "xor": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="110", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd/rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="1001", beginning=12, end=15),  # funct4
    ],
    "mv": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="111", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="1010", beginning=12, end=15),  # funct4
    ],
    "jr": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(const_value="000", beginning=9, end=11),  # rs2 (zero)
        Placeholder(const_value="1011", beginning=12, end=15),  # funct4
    ],
    "jalr": [
        Placeholder(const_value="000", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(const_value="1100", beginning=12, end=15),  # funct4
    ],
    # I-Type Instructions (opcode 001)
    "addi": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.IMMEDIATE, beginning=9, end=15),  # imm7
    ],
    "slti": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="001", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.IMMEDIATE, beginning=9, end=15),  # imm7
    ],
    "sltui": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="010", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.IMMEDIATE, beginning=9, end=15),  # imm7
    ],
    "slli": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="011", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=9, end=12
        ),  # imm7 (bits[6:4]=001)
        Placeholder(const_value="001", beginning=13, end=15),  # funct4 (bits[3:0]=000)
    ],
    "srli": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="011", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=9, end=12
        ),  # imm7 (bits[6:4]=010)
        Placeholder(const_value="010", beginning=13, end=15),
    ],
    "srai": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="011", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=9, end=12
        ),  # imm7 (bits[6:4]=100)
        Placeholder(const_value="100", beginning=13, end=15),
    ],
    "ori": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="100", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.IMMEDIATE, beginning=9, end=15),  # imm7
    ],
    "andi": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="101", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.IMMEDIATE, beginning=9, end=15),  # imm7
    ],
    "xori": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="110", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.IMMEDIATE, beginning=9, end=15),  # imm7
    ],
    "li": [
        Placeholder(const_value="001", beginning=0, end=2),  # opcode
        Placeholder(const_value="111", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.IMMEDIATE, beginning=9, end=15),  # imm7
    ],
    # B-Type Instructions (opcode 010)
    "beq": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
    ],
    "bne": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="001", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
    ],
    "bz": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="010", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
        # rs2 is ignored
    ],
    "bnz": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="011", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
        # rs2 is ignored
    ],
    "blt": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="100", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
    ],
    "bge": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="101", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
    ],
    "bltu": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="110", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
    ],
    "bgeu": [
        Placeholder(const_value="010", beginning=0, end=2),  # opcode
        Placeholder(const_value="111", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[4:1]
    ],
    # S-Type Instructions (opcode 011)
    "sb": [
        Placeholder(const_value="011", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[3:0]
        Placeholder(expected_token=TokenType.LPAREN),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.RPAREN),
    ],
    "sw": [
        Placeholder(const_value="011", beginning=0, end=2),  # opcode
        Placeholder(const_value="001", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rs1
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[3:0]
        Placeholder(expected_token=TokenType.LPAREN),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs2
        Placeholder(expected_token=TokenType.RPAREN),
    ],
    # L-Type Instructions (opcode 100)
    "lb": [
        Placeholder(const_value="100", beginning=0, end=2),  # opcode
        Placeholder(const_value="000", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[3:0]
        Placeholder(expected_token=TokenType.LPAREN),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs1
        Placeholder(expected_token=TokenType.RPAREN),
    ],
    "lw": [
        Placeholder(const_value="100", beginning=0, end=2),  # opcode
        Placeholder(const_value="001", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[3:0]
        Placeholder(expected_token=TokenType.LPAREN),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs1
        Placeholder(expected_token=TokenType.RPAREN),
    ],
    "lbu": [
        Placeholder(const_value="100", beginning=0, end=2),  # opcode
        Placeholder(const_value="100", beginning=3, end=5),  # funct3
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=12, end=15
        ),  # offset[3:0]
        Placeholder(expected_token=TokenType.LPAREN),
        Placeholder(expected_token=TokenType.REGISTER, beginning=9, end=11),  # rs1
        Placeholder(expected_token=TokenType.RPAREN),
    ],
    # J-Type Instructions (opcode 101)
    "j": [
        Placeholder(const_value="101", beginning=0, end=2),  # opcode
        Placeholder(
            expected_token=TokenType.IMMEDIATE,
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=1, i_end=3),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=4, i_end=9),
            ],
        ),
        Placeholder(const_value="0", beginning=15, end=15),  # link bit = 0
    ],
    "jal": [
        Placeholder(const_value="101", beginning=0, end=2),  # opcode
        Placeholder(expected_token=TokenType.REGISTER, beginning=3, end=5),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE,
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=0, i_end=2),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=3, i_end=8),
            ],
        ),
        Placeholder(const_value="1", beginning=15, end=15),  # link bit = 1
    ],
    # U-Type Instructions (opcode 110)
    "lui": [
        Placeholder(const_value="110", beginning=0, end=2),  # opcode
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE,
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=7, i_end=9),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=10, i_end=15),
            ],
        ),
        Placeholder(const_value="0", beginning=15, end=15),  # flag = 0
    ],
    "auipc": [
        Placeholder(const_value="110", beginning=0, end=2),  # opcode
        Placeholder(expected_token=TokenType.REGISTER, beginning=6, end=8),  # rd
        Placeholder(expected_token=TokenType.COMMA),
        Placeholder(
            expected_token=TokenType.IMMEDIATE,
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=7, i_end=9),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=10, i_end=15),
            ],
        ),
        Placeholder(const_value="1", beginning=15, end=15),  # flag = 1
    ],
    # SYS-Type Instructions (opcode 111)
    "ecall": [
        Placeholder(const_value="111", beginning=0, end=2),  # opcode
        Placeholder(
            expected_token=TokenType.IMMEDIATE, beginning=6, end=15
        ),  # service IMMEDIATE[15:6]
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

DEFAULT_SYMBOLS = {
    "RESET_VECTOR": 0x0000,
    "INT_VECTORS": 0x0000,  # Interrupt vector table start
    "CODE_START": 0x0020,  # Default code start
    "MMIO_BASE": 0xF000,  # Memory-mapped I/O base
    "MMIO_SIZE": 0x1000,  # MMIO region size
    "STACK_TOP": 0xEFFE,  # Default stack top
    "MEM_SIZE": 0x10000,  # Total memory size (64KB)
}

SectionType = Literal[".text", ".data", ".bss", "const"]
