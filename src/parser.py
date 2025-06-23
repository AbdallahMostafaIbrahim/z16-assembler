from typing import List
from tokenizer import TokenType, Token
from typing import Dict, List, Literal
from utils import  Symbol, SectionType
from constants import DEFAULT_SYMBOLS

class ZX16Parser:
    """Parser for ZX16 assembly language."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.symbol_table: Dict[str, Symbol] = {}
        self.pos = 0
        self.current_token = (
            self.tokens[0] if tokens else Token(TokenType.EOF, "", 1, 1)
        )
        self.current_section: Literal[".inter", ".text", ".data", ".bss"] = ".text"
        self.section_pointers: Dict[str, int] = {
            # Those are all relative to the start of each section
            ".inter": 0x0000,
            ".text": 0x0000,
            ".data": 0x0000,
            ".bss": 0x0000,
        }
        self.memory_layout = {
            ".text": DEFAULT_SYMBOLS["CODE_START"],
            ".data": 0x0000,
            ".bss": 0x0000,
        }
        self.lines:List[List[Token]] = []  # List of lines with tokens

    def define_symbol(
        self,
        name: str,
        value: int,
        section: SectionType,
        line: int = 0,
        is_global: bool = False,
    ) -> bool:
        """Define a symbol."""
        if name in self.symbol_table:
            if self.symbol_table[name].defined:
                self.add_error(f"Symbol '{name}' already defined", line)
                return False

        self.symbol_table[name] = Symbol(
            name=name,
            value=value,
            section=section,
            defined=True,
            global_symbol=is_global,
            line=line,
        )
        return True

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
    def pointer_advance(self, size: int = 2, section: SectionType = None):
        self.section_pointers[section or self.current_section] += size
    def current_address(self) -> int:
        return self.section_pointers[self.current_section]
    def parse_constant(self) -> Dict[str, Symbol] :
            # If not after it becomes an identifier
            if self.peek().type != TokenType.IDENTIFIER:
                self.add_error("Expected identifier after directive", self.current_token.line)
                return
            self.advance_and_delete()
            identifier = self.current_token.value
            if self.peek().type != TokenType.COMMA:
                self.add_error("Expected comma after identifier", self.current_token.line)
                return
            self.advance_and_delete()  # Skip the comma
            if self.peek().type not in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                self.add_error(
                    "Expected immediate or character value after comma",
                    self.current_token.line,
                )
                return
            self.advance_and_delete()  # Move to the value token
            value = int(self.current_token.value, 0)  # Convert to integer
            self.define_symbol(identifier, value, "const", self.current_token.line)
            self.advance_and_delete()  # Move to the next token
            return self.symbol_table
    def parse_label(self):
        label_name = self.current_token.value
        self.define_symbol(
            label_name,
            self.current_address(),
            self.current_section,
            self.current_token.line,
        )
        self.advance_and_delete()
    def parse_directive(self):
        directive = self.current_token.value.lower()
        line = self.current_token.line
        # Memory Layout Directives
        if directive in [".text", ".data", ".bss"]:  # Sections
            self.current_section = directive
            self.advance()
        elif directive == ".org":  # ORG :(
            if self.current_section not in [".text", ".inter"]:
                self.add_error(
                    f".org directive can only be used in the .text section, not in {self.current_section}. It works like .space in the .text section",
                    line,
                )
                return
            
            if self.peek().type != TokenType.IMMEDIATE:
                self.add_error("Expected immediate value after .org directive", line)
                return
            self.advance()  # Move to the immediate value
            value = int(self.current_token.value, 0)
            if value % 2 != 0:
                self.add_error(
                    f"Value {value:#04x} is not aligned (not a multiple of 2) for .org directive",
                    line,
                )
                return
            if value < 0 or value >= DEFAULT_SYMBOLS["STACK_TOP"]:
                self.add_error(
                    f"Value {value:#04x} out of range for .org directive (RAM, ROM, interrupt)",
                    line,
                )
                return

            if value < DEFAULT_SYMBOLS["CODE_START"]:
                self.current_section = ".inter"
                self.section_pointers[".inter"] = value
            else:
                self.current_section = ".text"
                self.section_pointers[".text"] = value - DEFAULT_SYMBOLS["CODE_START"]

            self.advance()
        # Data Directives
        elif directive in [".byte", ".word", ".string", ".ascii", ".space",".fill"]:
            if self.current_section not in [".data", ".bss"]:
                self.add_error(
                    f"{directive} directive can only be used in the .data or .bss sections, not in {self.current_section}",
                    line,
                )
                return
            if directive in [".byte"]:
                if self.peek().type not in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                    self.add_error(
                        f"Expected immediate or character value after {directive} directive",
                        line,
                    )
                    return
                while self.peek().type in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                    self.advance()
                    value = int(self.current_token.value, 0)
                    if value < 0 or value > 255:
                        self.add_error(
                            f"Value {value:#04x} is out of range for .byte directive (0-255)",
                            line,
                        )
                        return
                    self.pointer_advance(1)
                    if self.peek().type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
                if self.current_token.type == TokenType.COMMA:
                    self.add_error(
                        f"Unexpected token '{self.peek().value}' after {directive} directive",
                        self.peek().line,
                    )
                    self.advance()
                self.advance()
            elif directive in [".word"]:
                if self.peek().type not in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                    self.add_error(
                        f"Expected immediate or character value after {directive} directive",
                        line,
                    )
                    return
                while self.peek().type in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                    self.advance()
                    value = int(self.current_token.value, 0)
                    if value < 0 or value > 65535:
                        self.add_error(
                            f"Value {value:#04x} is out of range for .word directive (0-65535)",
                            line,
                        )
                        return
                    self.pointer_advance(2)
                    if self.peek().type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
                if self.current_token.type == TokenType.COMMA:
                    self.add_error(
                        f"Unexpected token '{self.peek().value}' after {directive} directive",
                        self.peek().line,
                    )
                    self.advance()
                self.advance()
            elif directive in [".string", ".ascii"]:
                if self.peek().type != TokenType.STRING:
                    self.add_error(f"Expected string after {directive}", line)
                    return
                while self.peek().type == TokenType.STRING:
                    self.advance()
                    string_len = len(self.current_token.value)
                    string= self.current_token.value
                    if directive == ".string":
                        string_len += 1  # Null terminator
                    self.pointer_advance(string_len)
                    if self.peek().type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
                if self.current_token.type == TokenType.COMMA:
                    self.add_error(
                        f"Unexpected token '{self.peek().value}' after {directive} directive",
                        self.peek().line,
                    )
                    self.advance()
                self.advance()   
            elif directive == ".space":
                if self.peek().type != TokenType.IMMEDIATE:
                    self.add_error(f"Expected size after .space directive", line)
                    return
                self.advance()
                space_size = int(self.current_token.value)
                self.pointer_advance(space_size)
                self.advance()
            elif directive == ".fill":
                if self.peek().type != TokenType.IMMEDIATE:
                    self.add_error(f"Expected size after .fill directive", line)
                    return
                self.advance()
                fill_items = int(self.current_token.value)
                if fill_items < 0:
                    self.add_error(f"items for .fill directive one at least ", line)
                    return
                if self.peek().type != TokenType.COMMA:
                    self.add_error(f"Expected comma after size in .fill directive", line)
                    return
                self.advance()
                if self.peek().type != TokenType.IMMEDIATE:
                    self.add_error(f"Expected fill value after comma in .fill directive", line)
                    return
                self.advance()
                fill_size = int(self.current_token.value, 0)
                if fill_items * fill_size > 65536:
                    self.add_error(
                        f"Total size for .fill directive ({fill_items * fill_size}) exceeds 65536 bytes",
                        line,
                    )
                    return
                if  self.peek().type != TokenType.COMMA:
                    self.add_error(f"Expected comma after fill value in .fill directive", line)
                    return
                self.advance()
                if self.peek().type != TokenType.IMMEDIATE:
                    self.add_error(f"Expected fill value after comma in .fill directive", line)
                    return
                self.advance()
                self.pointer_advance(fill_size * fill_items)
                self.advance()
        else:
            self.add_error(f"Unknown directive '{directive}'", self.current_token.line)
            self.advance()
    def calculate_memory_layout(self):
        self.memory_layout[".data"] = (
            self.section_pointers[".text"] + DEFAULT_SYMBOLS["CODE_START"]
        )
        self.memory_layout[".bss"] = (
            self.memory_layout[".data"] + self.section_pointers[".data"]
        )
    def lionize(self):
        """Organize tokens into lines."""
        current_line = []
        for token in self.tokens:
            if token.type == TokenType.NEWLINE:
                if current_line:
                    self.lines.append(current_line)
                    current_line = []
            else:
                current_line.append(token)
        if current_line:
            self.lines.append(current_line)
        
        