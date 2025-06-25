from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal, List, Optional
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


@dataclass
class MemoryAllocation:
    # Memory allocation
    m_beginning: int = None
    m_end: int = None
    # Immediate Allocation
    i_beginning: int = None
    i_end: int = None


@dataclass
class BitFieldSpec:
    beginning: int
    end: int


@dataclass
class ConstantField(BitFieldSpec):
    const_value: str


@dataclass
class OperandField(BitFieldSpec):
    expected_token: TokenType


@dataclass
class ImmediateField(OperandField):
    min_value: int
    max_value: int
    allocations: List[MemoryAllocation]

    def __init__(
        self,
        # either a simple contiguous field...
        beginning: Optional[int] = None,
        end: Optional[int] = None,
        # ...or a split field
        allocations: Optional[List[MemoryAllocation]] = None,
        # signed by default
        signed: bool = True,
        # override bounds
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ):
        # Validate arguments
        if allocations and (beginning is not None or end is not None):
            raise ValueError("Use either allocations or beginning/end, not both")
        if not allocations and (beginning is None or end is None):
            raise ValueError("Must specify beginning and end if no allocations")

        # Call parent for bit‐layout info
        super().__init__(
            beginning=beginning or 0,
            end=end or 0,
            expected_token=TokenType.IMMEDIATE,
        )

        self.allocations = allocations or []

        # Compute width
        if allocations:
            width = sum(a.i_end - a.i_beginning + 1 for a in allocations)
        else:
            width = end - beginning + 1

        # Determine bounds
        if min_value is not None and max_value is not None:
            self.min_value, self.max_value = min_value, max_value
        else:
            if signed:
                self.min_value = -(1 << (width - 1))
                self.max_value = (1 << (width - 1)) - 1
            else:
                self.min_value = 0
                self.max_value = (1 << width) - 1

    def __repr__(self):
        if self.allocations:
            return (
                f"<ImmediateField split bits={self.allocations} "
                f"range=[{self.min_value}..{self.max_value}]>"
            )
        return (
            f"<ImmediateField bits={self.beginning}-{self.end} "
            f"range=[{self.min_value}..{self.max_value}]>"
        )


@dataclass
class PunctuationField:
    expected_token: TokenType


INSTRUCTION_FORMAT: List[PunctuationField | BitFieldSpec] = {
    "add": [
        ConstantField(0, 2, "000"),  # opcode
        ConstantField(3, 5, "000"),  # funct3
        OperandField(6, 8, TokenType.REGISTER),  # rd/rs1
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),  # rs2
        ConstantField(12, 15, "0000"),  # funct4
    ],
    "sub": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "000"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0001"),
    ],
    "slt": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "001"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0010"),
    ],
    "sltu": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "010"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0011"),
    ],
    "sll": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "011"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0100"),
    ],
    "srl": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "011"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0101"),
    ],
    "sra": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "011"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0110"),
    ],
    "or": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "100"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "0111"),
    ],
    "and": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "101"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1000"),
    ],
    "xor": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "110"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1001"),
    ],
    "mv": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "111"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1010"),
    ],
    "jr": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "000"),
        OperandField(6, 8, TokenType.REGISTER),
        ConstantField(9, 11, "000"),  # rs2 = zero
        ConstantField(12, 15, "1011"),
    ],
    "jalr": [
        ConstantField(0, 2, "000"),
        ConstantField(3, 5, "000"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        ConstantField(12, 15, "1100"),
    ],
    # I-Type Instructions (opcode 001)
    "addi": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "000"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 15),
    ],
    "slti": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "001"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 15),
    ],
    "sltui": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "010"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 15),
    ],
    "slli": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "011"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 12),  # shift amount[2:0]
        ConstantField(13, 15, "001"),
    ],
    "srli": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "011"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 12),
        ConstantField(13, 15, "010"),
    ],
    "srai": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "011"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 12),
        ConstantField(13, 15, "100"),
    ],
    "ori": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "100"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 15),
    ],
    "andi": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "101"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 15),
    ],
    "xori": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "110"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 15),
    ],
    "li": [
        ConstantField(0, 2, "001"),
        ConstantField(3, 5, "111"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(9, 15),
    ],
    # B-Type Instructions (opcode 010)
    "beq": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "000"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
    ],
    "bne": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "001"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
    ],
    "bz": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "010"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
    ],
    "bnz": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "011"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
    ],
    "blt": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "100"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
    ],
    "bge": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "101"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(12, 15, TokenType.IMMEDIATE),
    ],
    "bltu": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "110"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
    ],
    "bgeu": [
        ConstantField(0, 2, "010"),
        ConstantField(3, 5, "111"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
    ],
    # S-Type Instructions (opcode 011)
    "sb": [
        ConstantField(0, 2, "011"),
        ConstantField(3, 5, "000"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
        PunctuationField(TokenType.LPAREN),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    "sw": [
        ConstantField(0, 2, "011"),
        ConstantField(3, 5, "001"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
        PunctuationField(TokenType.LPAREN),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    # L-Type Instructions (opcode 100)
    "lb": [
        ConstantField(0, 2, "100"),
        ConstantField(3, 5, "000"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
        PunctuationField(TokenType.LPAREN),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    "lw": [
        ConstantField(0, 2, "100"),
        ConstantField(3, 5, "001"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
        PunctuationField(TokenType.LPAREN),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    "lbu": [
        ConstantField(0, 2, "100"),
        ConstantField(3, 5, "100"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(12, 15),
        PunctuationField(TokenType.LPAREN),
        OperandField(9, 11, TokenType.REGISTER),
        PunctuationField(TokenType.RPAREN),
    ],
    # J-Type Instructions (opcode 101)
    "j": [
        ConstantField(0, 2, "101"),
        ImmediateField(
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=1, i_end=3),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=4, i_end=9),
            ],
        ),
        ConstantField(15, 15, "0"),
    ],
    "jal": [
        ConstantField(0, 2, "101"),
        OperandField(3, 5, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=0, i_end=2),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=3, i_end=8),
            ],
        ),
        ConstantField(15, 15, "1"),
    ],
    # U-Type Instructions (opcode 110)
    "lui": [
        ConstantField(0, 2, "110"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=7, i_end=9),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=10, i_end=15),
            ],
            signed=False,
        ),
        ConstantField(15, 15, "0"),
    ],
    "auipc": [
        ConstantField(0, 2, "110"),
        OperandField(6, 8, TokenType.REGISTER),
        PunctuationField(TokenType.COMMA),
        ImmediateField(
            allocations=[
                MemoryAllocation(m_beginning=3, m_end=5, i_beginning=7, i_end=9),
                MemoryAllocation(m_beginning=9, m_end=14, i_beginning=10, i_end=15),
            ],
            signed=False,
        ),
        ConstantField(15, 15, "1"),
    ],
    # SYS-Type Instructions (opcode 111)
    "ecall": [
        ConstantField(0, 2, "111"),
        ImmediateField(6, 15),
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
