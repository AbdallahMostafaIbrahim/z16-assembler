from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal, List
import sys
from constants import TokenType, SectionType


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
class AssemblerMessage:
    """Represents an assembly error or warning."""

    message: str
    line: int
    column: int
