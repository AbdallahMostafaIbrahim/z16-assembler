from typing import List, Literal

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional
from utils import sign_extend

SectionType = Literal[".inter", ".text", ".data", ".bss", ".mmio"]


class TokenType(Enum):
    """Token types for lexical analysis."""

    IDENTIFIER = auto()
    REGISTER = auto()
    IMMEDIATE = auto()
    LABEL_DEF = auto()
    LABEL_USE = auto()
    DIRECTIVE = auto()
    STRING = auto()
    NEWLINE = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    OPERATOR = auto()
    # TODO: Expression Support
    EOF = auto()


@dataclass
class BitFieldSpec:
    beginning: int
    end: int


@dataclass
class ConstantField(BitFieldSpec):
    const_value: str


@dataclass
class RegisterField(BitFieldSpec):
    expected_token: TokenType


@dataclass
class NumericField(BitFieldSpec):
    min_value: int
    max_value: int
    allocations: List[BitFieldSpec]

    def __init__(
        self,
        # either a simple contiguous field...
        beginning: Optional[int] = None,
        end: Optional[int] = None,
        # ...or a split field
        allocations: Optional[List[BitFieldSpec]] = None,
        # signed by default
        signed: Optional[bool] = True,
        label: Optional[bool] = False,
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
        )

        self.label = label
        self.allocations = allocations or []
        self.signed = signed

        # Compute width
        if allocations:
            width = sum(a.end - a.beginning + 1 for a in allocations)
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
    width: int = 0


@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""

    value: int
    section: SectionType | None = None
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
