from dataclasses import dataclass
from enum import Enum
from typing import Literal


@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""

    name: str
    value: int
    defined: bool = False
    global_symbol: bool = False
    line: int = 0


@dataclass
class AssemblerMessage:
    """Represents an assembly error or warning."""

    message: str
    line: int
    column: int


class InstructionFormat(Enum):
    """ZX16 instruction formats."""

    R_TYPE = 0b000
    I_TYPE = 0b001
    B_TYPE = 0b010
    S_TYPE = 0b011
    L_TYPE = 0b100
    J_TYPE = 0b101
    U_TYPE = 0b110
    SYS_TYPE = 0b111
