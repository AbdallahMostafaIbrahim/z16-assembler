import argparse
import re
import sys
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Union, Any, Literal
from pathlib import Path
from utils import AssemblerMessage, Symbol
from tokenizer import Tokenizer, TokenType, Token


class ZX16Parser:
    """Parser for ZX16 assembly language."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = (
            self.tokens[0] if tokens else Token(TokenType.EOF, "", 1, 1)
        )

    def advance(self) -> None:
        """Move to the next token."""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]

    def advance_and_delete(self) -> None:
        """Advance to the next token and delete the current one."""
        if self.pos < len(self.tokens) - 1:
            self.tokens.pop(self.pos)
            self.current_token = (
                self.tokens[self.pos] if self.tokens else Token(TokenType.EOF, "", 1, 1)
            )
        else:
            self.current_token = Token(TokenType.EOF, "", 1, 1)

    def peek(self, offset: int = 1) -> Token:
        """Peek at the next token without advancing."""
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return Token(
            TokenType.EOF, "", self.current_token.line, self.current_token.column
        )

    def reset(self) -> None:
        """Reset the parser to the beginning of the token list."""
        self.pos = 0
        self.current_token = (
            self.tokens[0] if self.tokens else Token(TokenType.EOF, "", 1, 1)
        )
