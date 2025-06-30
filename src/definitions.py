from typing import List, Literal

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

SectionType = Literal[".text", ".data", ".bss", "const"]


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
        self.signed = signed

        # Compute width
        if allocations:
            width = sum(a.i_end - a.i_beginning + 1 for a in allocations)
        else:
            width = end - beginning + 1
        self.width = width
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


@dataclass
class Token:
    """Represents a lexical token."""

    type: TokenType
    value: str
    line: int
    column: int
    was_label: bool = False


@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""

    name: str
    value: int
    section: SectionType
    defined: bool = False
    global_symbol: bool = False
    line: int = 0


@dataclass
class FirstPassResult:
    """Contains the results of the first pass parsing."""

    tokens: List[Token]
    symbol_table: Dict[str, Symbol]
    memory_layout: Dict[str, int]


class OutputFormat(Enum):
    """Supported output formats."""

    BINARY = "bin"
    INTEL_HEX = "hex"
    VERILOG = "verilog"
    MEMORY = "mem"
