from tokenizer import TokenType, Token
from typing import Dict, List
from definitions import Symbol, SectionType, FirstPassResult
from error_handler import Zx16Errors
from constants import (
    DEFAULT_SYMBOLS,
    PSEUDO_INSTRUCTIONS,
    INSTRUCTION_FORMAT,
    RESERVED_KEYWORDS,
    TOKEN_TYPE_NAMES,
)


class FirstPass:
    """First pass of the assembler."""

    def __init__(self, tokens: List[Token], verbose: bool = False):
        self.verbose = verbose
        self.tokens = tokens
        self.symbol_table: Dict[str, Symbol] = {}
        for name, value in DEFAULT_SYMBOLS.items():
            self.define_symbol(name, value)
        self.pos = 0
        self.current_token = self.tokens[0]
        self.current_section: SectionType = (
            ".text"  # Start in the text section by default
        )
        self.section_pointers: Dict[SectionType, int] = {
            # Those are all relative to the start of each section
            ".inter": 0,
            ".text": 0,
            ".data": 0,
            ".bss": 0,
            ".mmio": 0,
        }

    def define_symbol(
        self,
        name: str,
        value: int,
        section: SectionType = None,
        line: int = 0,
        is_global: bool = False,
    ) -> bool:
        """Define a symbol."""
        if name in self.symbol_table:
            if self.symbol_table[name].defined:
                Zx16Errors.add_error(f"Symbol '{name}' already defined", line)
                return False

        self.symbol_table[name] = Symbol(
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
            TokenType.EOF, "EOF", self.current_token.line, self.current_token.column
        )

    def expect(self, *args) -> bool:
        offset = 0
        expected_types = args
        # If the last argument is an int, treat it as the offset
        if args and isinstance(args[-1], int):
            offset = args[-1]
            expected_types = args[:-1]

        tok = self.peek(offset)
        if tok.type in expected_types:
            return True

        # Build a nice error message listing all expected types
        names = ", ".join(TOKEN_TYPE_NAMES[t] for t in expected_types)
        escaped_value = tok.value.replace(chr(10), "\\n")
        Zx16Errors.add_error(
            f"Expected token type(s) {names}, got {escaped_value} ({tok.type.name})",
            tok.line,
            tok.column,
        )
        self.advance_to_newline()
        return False

    def reset(self) -> None:
        """Reset the parser to the beginning of the token list."""
        self.pos = 0
        self.current_token = self.tokens[0]

    def pointer_advance(self, size: int = 2, section: SectionType = None):
        self.section_pointers[section or self.current_section] += size

    def current_address(self) -> int:
        return self.section_pointers[self.current_section]

    def parse_constant(self):
        # If not after it becomes an identifier
        self.advance_and_delete()  # Skip the directive token
        if not self.expect(TokenType.IDENTIFIER, 0):
            return
        constant_name = self.current_token.value
        if constant_name in self.symbol_table:
            Zx16Errors.add_error(
                f"Constant '{constant_name}' already defined", self.current_token.line
            )
            self.advance_to_newline()
            return
        if constant_name in RESERVED_KEYWORDS:
            Zx16Errors.add_error(
                f"'{constant_name}' is a reserved keyword and cannot be used as a constant name",
                self.current_token.line,
            )
            self.advance_to_newline()
            return
        self.advance_and_delete()  # Skip the identifier token
        if not self.expect(TokenType.COMMA, 0):
            return
        self.advance_and_delete()  # Skip the comma
        if not self.expect(TokenType.IMMEDIATE, 0):
            return
        value = int(self.current_token.value, 0)  # Convert to integer
        self.advance_and_delete()  # skip the immediate value token
        self.define_symbol(constant_name, value, line=self.current_token.line)

    def parse_label(self):
        label_name = self.current_token.value
        self.define_symbol(
            label_name,
            self.current_address(),
            self.current_section,
            self.current_token.line,
        )
        self.advance_and_delete()

    def advance_to_newline(self):
        """Advance to the next newline or EOF."""
        while self.current_token.type not in [TokenType.NEWLINE, TokenType.EOF]:
            self.advance()

    def parse_directive(self):
        directive = self.current_token.value.lower()
        line = self.current_token.line
        self.advance()
        # Memory Layout Directives
        if directive in [".inter", ".text", ".data", ".bss", ".mmio"]:  # Sections
            self.current_section = directive
        elif directive == ".org":
            if not self.expect(TokenType.IMMEDIATE):
                return
            value = int(self.current_token.value, 0)
            if value % 2 != 0:
                Zx16Errors.add_warning(
                    f"Value {value:#04x} is not aligned (not a multiple of 2) for .org directive",
                    line,
                )
            if value < 0 or value > DEFAULT_SYMBOLS["MEM_SIZE"]:
                Zx16Errors.add_error(
                    f"Value {value:#04x} out of range for .org directive",
                    line,
                )
                self.advance_to_newline()
                return

            if value < DEFAULT_SYMBOLS["CODE_START"]:  # Inter section
                self.current_section = ".inter"
                self.section_pointers[self.current_section] = value
            elif (
                value < DEFAULT_SYMBOLS["MMIO_BASE"]
            ):  # Between inter and mmio (text section)
                self.current_section = ".text"
                self.section_pointers[self.current_section] = (
                    value - DEFAULT_SYMBOLS["CODE_START"]
                )
                Zx16Errors.add_warning(
                    f"Using .org inside the RAM/ROM area is not recommended, use .text, .data, or .bss directives instead",
                    line,
                )
            else:
                # MMIO section
                self.current_section = ".mmio"
                self.section_pointers[self.current_section] = (
                    value - DEFAULT_SYMBOLS["MMIO_BASE"]
                )

            self.advance()
        # Data Directives
        elif directive in [".byte", ".word", ".string", ".ascii", ".space", ".fill"]:
            if self.current_section == ".text":
                Zx16Errors.add_error(
                    f"{directive} directive cannot be used in the .text section",
                    line,
                )
                self.advance_to_newline()
                return
            if directive == ".byte":
                if not self.expect(TokenType.IMMEDIATE):
                    return
                while self.current_token.type == TokenType.IMMEDIATE:
                    value = int(self.current_token.value, 0)
                    if value < 0 or value > 255:
                        Zx16Errors.add_error(
                            f"Value {value:#04x} is out of range for .byte directive (0-255)",
                            line,
                        )
                        self.advance_to_newline()
                        return
                    self.pointer_advance(1)
                    self.advance()
                    if self.current_token.type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
            elif directive == ".word":
                if not self.expect(TokenType.IMMEDIATE):
                    return
                while self.current_token.type == TokenType.IMMEDIATE:
                    value = int(self.current_token.value, 0)
                    if value < 0 or value > 65535:
                        Zx16Errors.add_error(
                            f"Value {value:#04x} is out of range for .byte directive (0-65535)",
                            line,
                        )
                        self.advance_to_newline()
                        return
                    self.pointer_advance(2)
                    self.advance()
                    if self.current_token.type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
            elif directive in [".string", ".ascii"]:
                if not self.expect(TokenType.STRING):
                    return
                string_len = len(self.current_token.value)
                if directive == ".string":
                    string_len += 1  # Null terminator
                self.pointer_advance(string_len)
                self.advance()
            elif directive == ".space":
                # TODO : Range check
                if not self.expect(TokenType.IMMEDIATE):
                    return
                space_size = int(self.current_token.value)
                self.pointer_advance(space_size)
                self.advance()
            elif directive == ".fill":
                if not self.expect(TokenType.IMMEDIATE):
                    return
                fill_items = int(self.current_token.value)
                if fill_items < 0:
                    Zx16Errors.add_error(
                        f"items for .fill directive one at least ", line
                    )
                    self.advance_to_newline()
                    return
                self.advance()
                if not self.expect(TokenType.COMMA):
                    return
                self.advance()
                if not self.expect(TokenType.IMMEDIATE):
                    return
                fill_size = int(self.current_token.value, 0)
                if fill_size not in [1, 2]:
                    Zx16Errors.add_error(
                        f"Fill size must be 1 or 2 bytes, not {fill_size}",
                        line,
                    )
                    self.advance_to_newline()

                    return
                if fill_items * fill_size > 65536:
                    Zx16Errors.add_error(
                        f"Total size for .fill directive ({fill_items * fill_size}) exceeds 65536 bytes",
                        line,
                    )
                    self.advance_to_newline()
                    return
                self.advance()
                if not self.expect(TokenType.COMMA):
                    return
                self.advance()
                if not self.expect(TokenType.IMMEDIATE):
                    return
                _value = int(self.current_token.value, 0)
                # TODO: check if the value is bigger than the size
                self.pointer_advance(fill_size * fill_items)
                self.advance()
        else:
            Zx16Errors.add_error(
                f"Unknown directive '{directive}'", self.current_token.line
            )
            self.advance_to_newline()

    def parse_identifier(self):
        potential = self.current_token.value.lower()
        if potential in INSTRUCTION_FORMAT:
            self.pointer_advance(2)
        elif potential in PSEUDO_INSTRUCTIONS:
            self.pointer_advance(PSEUDO_INSTRUCTIONS[potential])
        # Keep advancing until we find a new line
        while self.current_token.type not in [TokenType.NEWLINE, TokenType.EOF]:
            self.advance()

    def calculate_memory_layout(self):
        memory_layout = {
            ".inter": 0x0000,
            ".text": 0x0020,
            ".data": 0x0000,
            ".bss": 0x0000,
            ".mmio": 0xF000,
        }
        memory_layout[".data"] = memory_layout[".text"] + self.section_pointers[".text"]
        memory_layout[".bss"] = memory_layout[".data"] + self.section_pointers[".data"]
        return memory_layout

    def handle_constants(self):
        while self.current_token.type != TokenType.EOF:
            if (
                self.current_token.type == TokenType.DIRECTIVE
                and self.current_token.value in [".equ", ".set"]
            ):
                self.parse_constant()
            self.advance()
        self.reset()
        while self.current_token.type != TokenType.EOF:
            if (
                self.current_token.type == TokenType.IDENTIFIER
                and self.current_token.value in self.symbol_table
            ):
                value = self.symbol_table[self.current_token.value].value
                self.current_token = Token(
                    TokenType.IMMEDIATE,
                    str(value),
                    self.current_token.line,
                    self.current_token.column,
                    self.current_token.width,
                )
            self.advance()
        self.reset()

    def resolve_symbols(self):
        # Adjust symbol values based on section pointers
        memory_layout = self.calculate_memory_layout()
        for _, symbol in self.symbol_table.items():
            if isinstance(symbol.value, str):
                continue
            symbol.value += memory_layout.get(symbol.section, 0)

        for token in self.tokens:
            if token.type != TokenType.IDENTIFIER:  # Only consider identifiers
                continue

            # Skip any instructions
            if (
                token.value.lower() in INSTRUCTION_FORMAT
                or token.value.lower() in PSEUDO_INSTRUCTIONS
            ):
                continue

            # Resolve symbols in the symbol table
            if token.value in self.symbol_table:
                symbol = self.symbol_table[token.value]
                token.type = TokenType.LABEL_USE
                token.value = str(symbol.value)
                token.width = 16
            else:
                Zx16Errors.add_error(
                    f"Undefined symbol: {token.value}", token.line, token.column
                )

    def execute(self) -> FirstPassResult:

        # Fill the symbol tables with the constants using .equ and .set directives
        self.handle_constants()
        # TODO: Handle ifs, in another Loop

        while self.current_token.type != TokenType.EOF:
            """FIRST PASS LOOP"""
            if self.current_token.type == TokenType.LABEL_DEF:
                self.parse_label()
            elif self.current_token.type == TokenType.IDENTIFIER:
                self.parse_identifier()
            elif self.current_token.type == TokenType.DIRECTIVE:
                self.parse_directive()

            if not self.expect(TokenType.NEWLINE, TokenType.EOF):
                return
            # Accumulate Errors
            self.advance()

        self.resolve_symbols()

        return FirstPassResult(
            tokens=self.tokens,
            symbol_table=self.symbol_table,
            memory_layout=self.calculate_memory_layout(),
        )
