from typing import List
from tokenizer import TokenType, Token
from typing import Dict, List, Literal
from error_handler import Zx16Errors
from constants import (
    DEFAULT_SYMBOLS,
    PSEUDO_INSTRUCTIONS,
    INSTRUCTION_FORMAT,
    ConstantField,
    ImmediateField,
    PunctuationField,
)
from dataclasses import dataclass
from first_pass_parser import FirstPassResult
from utils import binary_to_decimal, decimal_to_binary


class ZX16SecondPassEncoder:
    """Second Pass Encoder for ZX16 assembly language."""

    def __init__(self, data: FirstPassResult, verbose: bool = False):
        self.verbose = verbose
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
        # Print token values for debugging
        if self.verbose:
            print("Resolving symbols in tokens:")
            for token in self.tokens:
                print(f"Token: {token.value} (Type: {token.type})")

        for token in self.tokens:
            if token.type != TokenType.IDENTIFIER:
                continue

            # Skip any instructions
            if (
                token.value.lower() in INSTRUCTION_FORMAT
                or token.value.lower() in PSEUDO_INSTRUCTIONS
            ):
                continue
            # Resolve symbols in the symbol table
            if token.type == TokenType.IDENTIFIER and token.value in self.symbol_table:
                symbol = self.symbol_table[token.value]
                token.type = TokenType.IMMEDIATE
                if symbol.section == "const":
                    token.value = str(symbol.value)
                else:
                    token.was_label = True
                    token.value = str(
                        symbol.value + self.section_pointers[symbol.section]
                    )
            else:
                # If the symbol is not found, report an error
                Zx16Errors.add_error(
                    f"Undefined symbol: {token.value}", token.line, token.column
                )
                token.type = TokenType.IMMEDIATE
                token.value = "0"

    def resolve_pseudo_instructions(self, line: List[Token], idx: int) -> List[Token]:
        """Expand psuedo instruction like
        i16, la, push, pop, call, ret, inc, dec, neg, not, clr, nop
        to true instructions"""
        instruction = line[0].value.lower()

        if instruction == "li16":
            reg = line[1].value
            value = int(line[3].value)
            line = [
                Token(TokenType.IDENTIFIER, "lui", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(
                    TokenType.IMMEDIATE,
                    str(value >> 7),
                    line[0].line,
                    line[0].column,
                ),
            ]
            # build the ORI instruction tokens (low 7 bits & 0x7F)
            second_line = [
                Token(TokenType.IDENTIFIER, "ori", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[1].line, line[1].column),
                Token(TokenType.COMMA, ",", line[2].line, line[2].column),
                Token(
                    TokenType.IMMEDIATE, str(value & 0x7F), line[3].line, line[3].column
                ),
            ]
            self.lines[idx] = line  # replace the original instruction
            # insert the ORI right after, shifting the rest down
            self.lines.insert(idx + 1, second_line)

        elif instruction == "la":
            reg = line[1].value
            label = int(line[3].value)
            line = [
                Token(TokenType.IDENTIFIER, "auipc", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(
                    TokenType.IMMEDIATE,
                    str(label >> 7),
                    line[0].line,
                    line[0].column,
                ),
            ]
            second_line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[1].line, line[1].column),
                Token(TokenType.COMMA, ",", line[2].line, line[2].column),
                Token(
                    TokenType.IMMEDIATE, str(label & 0x7F), line[3].line, line[3].column
                ),
            ]
            self.lines[idx] = line  # replace the original instruction
            self.lines.insert(idx + 1, second_line)  # insert the ADDI right
        elif instruction == "push":
            reg = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x2", line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "-2", line[0].line, line[0].column),
            ]
            second_line = [
                Token(TokenType.IDENTIFIER, "sw", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "0", line[0].line, line[0].column),
                Token(TokenType.LPAREN, "(", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x2", line[0].line, line[0].column),
                Token(TokenType.RPAREN, ")", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
            self.lines.insert(idx + 1, second_line)  # insert the ADDI right
        elif instruction == "pop":
            reg = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "lw", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "0", line[0].line, line[0].column),
                Token(TokenType.LPAREN, "(", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x2", line[0].line, line[0].column),
                Token(TokenType.RPAREN, ")", line[0].line, line[0].column),
            ]
            second_line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x2", line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "2", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
            self.lines.insert(idx + 1, second_line)  # insert the ADDI right
        elif instruction == "call":
            offset = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "jal", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x1", line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(
                    TokenType.IMMEDIATE,
                    offset,
                    line[0].line,
                    line[0].column,
                    was_label=True,
                ),  # Placeholder
            ]
            self.lines[idx] = line
        elif instruction == "ret":
            line = [
                Token(TokenType.IDENTIFIER, "jr", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x1", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
        elif instruction == "inc":
            reg = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "1", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
        elif instruction == "dec":
            reg = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "-1", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
        elif instruction == "neg":
            reg = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "xori", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "-1", line[0].line, line[0].column),
            ]
            second_line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "1", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
            self.lines.insert(idx + 1, second_line)  # insert the ADDI right
        elif instruction == "not":
            reg = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "xori", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.IMMEDIATE, "-1", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
        elif instruction == "clr":
            reg = line[1].value
            line = [
                Token(TokenType.IDENTIFIER, "xor", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction
        elif instruction == "nop":
            line = [
                Token(TokenType.IDENTIFIER, "add", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x0", line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(TokenType.REGISTER, "x0", line[0].line, line[0].column),
            ]
            self.lines[idx] = line  # replace the original instruction

        return self.lines[idx]

    def write_memory(self, value: int, size: int) -> None:
        """Write a value to the memory at the specified address."""
        address = self.section_pointers[self.current_section]

        # Little endian encoding
        if 0 <= address < len(self.memory):
            if size == 1:
                self.memory[address] = value & 0xFF
            else:
                self.memory[address] = value & 0xFF
                for i in range(1, size):
                    self.memory[address + i] = (value >> 8) & 0xFF
            self.section_pointers[self.current_section] += size
        else:
            Zx16Errors.add_error(f"Memory address out of bounds: {address}", 0, 0)

    def encode_directive(self, line: List[Token]) -> None:
        """Encode a directive line."""
        # TODO: ADD .inter instead of org only access in pass 1 and pass 2
        # TODO: check org value is in the right range
        directive = line[0].value.lower()
        if directive in [".text", ".data", ".bss"]:  # Sections
            self.current_section = directive
        elif directive == ".org":
            value = int(line[1].value, 0)
            if value < 0 or value >= len(self.memory):
                Zx16Errors.add_error(
                    f"ORG value {value} out of bounds (0-65535)",
                    line[1].line,
                    line[1].column,
                )
                return
            if value < DEFAULT_SYMBOLS["CODE_START"]:
                self.current_section = ".inter"
            elif value < DEFAULT_SYMBOLS["MMIO_BASE"]:
                self.current_section = ".text"
            else:
                Zx16Errors.add_error(
                    f"ORG value {value} cannot be in MMIO range (0x{DEFAULT_SYMBOLS['MMIO_BASE']:04x}–0xFFFF)",
                    line[1].line,
                    line[1].column,
                )
                return
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
        """Encode an instruction line, reporting errors via Zx16Errors."""
        mnemonic = line[0].value.lower()
        if mnemonic not in INSTRUCTION_FORMAT:
            Zx16Errors.add_error(
                f"Unknown instruction '{mnemonic}'", line[0].line, line[0].column
            )
            return

        specs = INSTRUCTION_FORMAT[mnemonic]
        word = 0

        # 1) Lay down all constants
        for field in specs:
            if isinstance(field, ConstantField):
                word |= int(field.const_value, 2) << field.beginning

        # 2) Consume tokens for punctuation, registers, immediates
        token_idx = 1
        for field in specs:
            if isinstance(field, ConstantField):
                continue  # already handled

            if token_idx >= len(line):
                Zx16Errors.add_error(
                    f"Missing token for field {field}", line[-1].line, line[-1].column
                )
                return
            token = line[token_idx]

            # --- punctuation ---
            if isinstance(field, PunctuationField):
                if token.type is not field.expected_token:
                    Zx16Errors.add_error(
                        f"Expected punctuation {field.expected_token}, got {token.type}",
                        token.line,
                        token.column,
                    )
                    return
                token_idx += 1
                continue

            # --- register operand ---
            if field.expected_token == TokenType.REGISTER:
                if token.type is not TokenType.REGISTER:
                    Zx16Errors.add_error(
                        f"Expected REGISTER, got {token.type} for '{mnemonic}'",
                        token.line,
                        token.column,
                    )
                    return
                try:
                    reg_index = int(token.value[1])
                except (IndexError, ValueError):
                    Zx16Errors.add_error(
                        f"Invalid register syntax '{token.value}'",
                        token.line,
                        token.column,
                    )
                    return
                if not (0 <= reg_index <= 7):
                    Zx16Errors.add_error(
                        f"Register index {reg_index} out of range (0–7)",
                        token.line,
                        token.column,
                    )
                    return
                word |= reg_index << field.beginning
                token_idx += 1
                continue

            # --- immediate operand ---
            # ImmediateField inherits from OperandField and carries min_value/max_value
            if isinstance(field, ImmediateField):
                if token.type is not TokenType.IMMEDIATE:
                    Zx16Errors.add_error(
                        f"Expected IMMEDIATE, got {token.type} for '{mnemonic}'",
                        token.line,
                        token.column,
                    )
                    return
                # parse
                try:
                    imm = binary_to_decimal(
                        decimal_to_binary(int(token.value, 0), field.width),
                        signed=field.signed,
                    )
                except ValueError:
                    Zx16Errors.add_error(
                        f"Invalid immediate '{token.value}'", token.line, token.column
                    )
                    return

                # label resolution
                if token.was_label and mnemonic in [
                    "jal",
                    "j",
                    "jr",
                    "jalr",
                    "beq",
                    "bne",
                    "bz",
                    "bnz",
                    "blt",
                    "bge",
                    "bltu",
                    "bgeu",
                ]:
                    imm -= self.section_pointers[self.current_section]
                    imm = int(imm / 2)  # integer division by 2 for branch offsets

                # range check against the field’s own bounds
                if not (field.min_value <= imm <= field.max_value):
                    if token.was_label:
                        Zx16Errors.add_error(
                            f"Label out of range [{field.min_value}..{field.max_value}]",
                            token.line,
                            token.column,
                        )
                    else:
                        Zx16Errors.add_error(
                            f"Immediate {imm} out of range [{field.min_value}..{field.max_value}]",
                            token.line,
                            token.column,
                        )
                    return

                # encode: split or contiguous
                if field.allocations:
                    for alloc in field.allocations:
                        width = alloc.i_end - alloc.i_beginning + 1
                        mask = ((1 << width) - 1) << alloc.i_beginning
                        piece = (imm & mask) >> alloc.i_beginning
                        word |= piece << alloc.m_beginning
                else:
                    word |= (
                        imm & ((1 << (field.end - field.beginning + 1)) - 1)
                    ) << field.beginning

                token_idx += 1
                continue

            # If we get here, it’s an unexpected field type
            Zx16Errors.add_error(
                f"Unhandled field type {type(field).__name__} in '{mnemonic}'",
                token.line,
                token.column,
            )
            return

        # 3) Write out the two-byte instruction
        self.write_memory(word, 2)
        if self.verbose:
            print(
                f"Encoded {mnemonic}: 0x{word:04x} @ {self.current_section}:{self.section_pointers[self.current_section]}"
            )

    def execute(self) -> bytearray:
        self.resolve_symbols()
        self.lionize()
        # TODO : Resolve symbols in the lines

        for idx, line in enumerate(self.lines):
            if self.verbose:
                print(f"Processing line: {[token.value for token in line]}")
            # Look at the first token to determine the type of line
            if line[0].type == TokenType.EOF:  # End of file
                break
            elif line[0].type == TokenType.DIRECTIVE:  # Directive line
                self.encode_directive(line)
            elif line[0].type == TokenType.IDENTIFIER:  # Instruction line
                if line[0].value.lower() in PSEUDO_INSTRUCTIONS:
                    line = self.resolve_pseudo_instructions(line, idx)
                self.encode_instruction(line)

        return self.memory
