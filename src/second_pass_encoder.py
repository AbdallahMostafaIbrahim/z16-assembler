from typing import List
from tokenizer import TokenType, Token
from typing import Dict, List, Literal
from definitions import Symbol, SectionType
from error_handler import Zx16Errors
from constants import (
    DEFAULT_SYMBOLS,
    TRUE_INSTRUCTIONS,
    PSEUDO_INSTRUCTIONS,
    INSTRUCTION_FORMAT,
)
from dataclasses import dataclass
from first_pass_parser import FirstPassResult


class ZX16SecondPassEncoder:
    """Second Pass Encoder for ZX16 assembly language."""

    def __init__(self, data: FirstPassResult):
        self.tokens = data.tokens
        self.symbol_table = data.symbol_table
        self.lines: List[List[Token]] = []  # List of lines with tokens
        self.current_section: Literal[".inter", ".text", ".data", ".bss"] = ".text"
        self.section_pointers: Dict[str, int] = {
            # Those are all relative to the start of each section
            ".inter": data.memory_layout[".inter"],
            ".text": data.memory_layout[".text"],
            ".data": data.memory_layout[".data"],
            ".bss": data.memory_layout[".bss"],
        }

        self.memory = bytearray(65536)  # Data to be assembled (64KB)

    def advance_pointer(self, size=2) -> None:
        """Advance the section pointer by the given size."""
        if self.current_section in self.section_pointers:
            self.section_pointers[self.current_section] += size
        else:
            Zx16Errors.add_error(f"Unknown section: {self.current_section}", 0, 0)

    def lionize(self) -> None:
        """Convert tokens into lines for processing."""
        current_line: List[Token] = []
        for token in self.tokens:
            if token.type == TokenType.NEWLINE:
                if current_line:
                    self.lines.append(current_line)
                    current_line = []
            else:
                current_line.append(token)
        if current_line:
            self.lines.append(current_line)

    def resolve_symbols(self):
        for token in self.tokens:
            if token.type != TokenType.IDENTIFIER:
                continue

            # Skip any instructions
            if token.value in TRUE_INSTRUCTIONS or token.value in PSEUDO_INSTRUCTIONS:
                continue

            # Resolve symbols in the symbol table
            if token.type == TokenType.IDENTIFIER and token.value in self.symbol_table:
                symbol = self.symbol_table[token.value]
                token.type = TokenType.IMMEDIATE
                token.was_label = True
                token.value = str(symbol.value + self.section_pointers[symbol.section])
            else:
                # If the symbol is not found, report an error
                Zx16Errors.add_error(
                    f"Undefined symbol: {token.value}", token.line, token.column
                )
                token.type = TokenType.IMMEDIATE
                token.value = "0"

    def write_memory(self, value: int, size: int) -> None:
        """Write a value to the memory at the specified address."""
        address = self.section_pointers[self.current_section]

        if 0 <= address < len(self.memory):
            # zext
            if size == 1:
                self.memory[address] = value & 0xFF
            else:
                # litte endian
                self.memory[address] = value & 0xFF
                for i in range(1, size):
                    self.memory[address + i] = (value >> 8) & 0xFF
            self.section_pointers[self.current_section] += size
        else:
            Zx16Errors.add_error(f"Memory address out of bounds: {address}", 0, 0)

    def encode_directive(self, line: List[Token]) -> None:
        """Encode a directive line."""
        # TODO: ADD .inter instead of org only access in pass 1 nad pass 2
        directive = line[0].value.lower()
        if directive in [".text", ".data", ".bss"]:  # Sections
            self.current_section = directive
        elif directive == ".org":
            value = int(line[1].value, 0)
            if value < DEFAULT_SYMBOLS["CODE_START"]:
                self.current_section = ".inter"
            else:
                self.current_section = ".text"
            self.section_pointers[self.current_section] = value
        elif directive in [".byte", ".word", ".string", ".ascii", ".space", ".fill"]:
            if directive in [".byte"]:
                for operand in line[1:]:
                    if operand.type == TokenType.COMMA:
                        continue
                    value = int(operand.value, 0)
                    self.write_memory(value, 1)
            elif directive in [".word"]:
                for operand in line[1:]:
                    if operand.type == TokenType.COMMA:
                        continue
                    value = int(self.current_token.value, 0)
                    self.write_memory(value, 2)
            elif directive in [".string", ".ascii"]:
                value = line[1].value
                for char in value:
                    self.write_memory(ord(char), 1)
                if directive == ".string":
                    self.write_memory(0, 1)
            elif directive == ".space":
                for i in range(int(line[1].value)):
                    self.write_memory(0, 1)
            elif directive == ".fill":
                fill_items = int(line[1].value, 0)
                fill_size = int(line[3].value, 0)
                fill_value = int(line[5].value, 0)
                for i in range(fill_items):
                    for _ in range(fill_size):
                        self.write_memory(fill_value, fill_size)

    def encode_instruction(self, line: List[Token]) -> None:
        """Encode an instruction line."""
        instruction = line[0].value.lower()
        if instruction in INSTRUCTION_FORMAT:
            word = 0
            placeholders = INSTRUCTION_FORMAT[instruction]

            for placeholder in placeholders:
                if placeholder.const_value:
                    word |= int(placeholder.const_value, 2) << placeholder.beginning

            tokenPointer = 1
            placeholderPointer = 0
            while tokenPointer < len(line) and placeholderPointer < len(placeholders):
                token = line[tokenPointer]
                placeholder = placeholders[placeholderPointer]
                if placeholder.const_value:
                    placeholderPointer += 1
                    continue
                if token.type == placeholder.expected_token:
                    if placeholder.expected_token == TokenType.IMMEDIATE:
                        value = int(token.value, 0)
                        if token.was_label:
                            value -= self.section_pointers[self.current_section]
                        if placeholder.allocations:
                            for allocation in placeholder.allocations:
                                masked = (
                                    value
                                    & (
                                        int(
                                            "1"
                                            * (
                                                allocation.i_end
                                                - allocation.i_beginning
                                                + 1
                                            ),
                                            2,
                                        )
                                        << allocation.i_beginning
                                    )
                                ) >> allocation.i_beginning

                                word |= masked << allocation.m_beginning
                        else:
                            word |= value << placeholder.beginning

                    elif placeholder.expected_token == TokenType.REGISTER:
                        reg_index = int(token.value[1])
                        if reg_index < 0 or reg_index > 7:
                            Zx16Errors.add_error(
                                f"Invalid register {token.value}",
                                token.line,
                                token.column,
                            )
                            return
                        word |= reg_index << placeholder.beginning

                    tokenPointer += 1
                    placeholderPointer += 1
                    continue

                Zx16Errors.add_error(
                    f"Expected token {placeholder.expected_token} but got {token.type} for instruction {instruction}",
                    token.line,
                    token.column,
                )
                return
            self.write_memory(word, 2)

        # For now, we assume all instructions are 2 bytes long

    def execute(self):
        self.resolve_symbols()
        self.lionize()
        for line in self.lines:
            print(f"Processing line: {[token.value for token in line]}")
            if line[0].type == TokenType.EOF:
                break
            elif line[0].type == TokenType.DIRECTIVE:
                self.encode_directive(line)
            elif line[0].type == TokenType.IDENTIFIER:
                self.encode_instruction(line)
        # Write memory to binary file
        with open("output.bin", "wb") as f:
            f.write(bytes(self.memory))
