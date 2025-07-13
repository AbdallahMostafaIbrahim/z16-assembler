from typing import List
from tokenizer import TokenType, Token
from typing import Dict, List
from error_handler import Zx16Errors
from constants import (
    DEFAULT_SYMBOLS,
    INSTRUCTION_FORMAT,
    PSEUDO_INSTRUCTIONS,
    ConstantField,
    NumericField,
    PunctuationField,
    RegisterField,
    TOKEN_TYPE_NAMES,
)
from utils import sign_extend
from definitions import SectionType


class SecondPass:
    def __init__(
        self, tokens: Token, memory_layout: Dict["str", int], verbose: bool = False
    ):
        self.verbose = verbose

        self.current_section: SectionType = ".text"
        self.section_pointers = memory_layout

        self.tokens = tokens
        self.lines: List[List[Token]] = []  # List of lines with tokens
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

    def resolve_pseudo_instructions(self, line: List[Token], idx: int) -> List[Token]:
        """Expand psuedo instruction like
        i16, la, push, pop, call, ret, inc, dec, neg, not, clr, nop
        to true instructions"""

        # TODO: Do validation of pseudo instructions

        instruction = line[0].value.lower()

        if instruction == "li16":
            reg = line[1].value
            value = int(line[3].value)
            lui_imm = value >> 7
            addi_imm = value & 0x7F

            # Check if the addi_imm is signed
            if addi_imm & 0x40:
                lui_imm += 1
            line = [
                Token(TokenType.IDENTIFIER, "lui", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(
                    TokenType.IMMEDIATE, str(lui_imm), line[0].line, line[0].column, 9
                ),
            ]
            # build the ADDI instruction tokens (low 7 bits & 0x7F)
            second_line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[1].line, line[1].column),
                Token(TokenType.COMMA, ",", line[2].line, line[2].column),
                Token(
                    TokenType.IMMEDIATE, str(addi_imm), line[3].line, line[3].column, 7
                ),
            ]
            self.lines[idx] = line  # replace the original instruction
            # insert the ADDI right after, shifting the rest down
            self.lines.insert(idx + 1, second_line)

        elif instruction == "la":
            reg = line[1].value
            if line[3].type != TokenType.LABEL_USE:
                Zx16Errors.add_error(
                    f"LA instruction expects a label, got {line[3].value}",
                    line[3].line,
                    line[3].column,
                )
                return line
            label = int(line[3].value) - self.section_pointers[self.current_section]
            lui_imm = label >> 7
            addi_imm = label & 0x7F
            # Check if the addi_imm is signed
            if addi_imm & 0x40:
                lui_imm += 1
            line = [
                Token(TokenType.IDENTIFIER, "auipc", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[0].line, line[0].column),
                Token(TokenType.COMMA, ",", line[0].line, line[0].column),
                Token(
                    TokenType.IMMEDIATE, str(lui_imm), line[0].line, line[0].column, 9
                ),
            ]
            second_line = [
                Token(TokenType.IDENTIFIER, "addi", line[0].line, line[0].column),
                Token(TokenType.REGISTER, reg, line[1].line, line[1].column),
                Token(TokenType.COMMA, ",", line[2].line, line[2].column),
                Token(
                    TokenType.IMMEDIATE, str(addi_imm), line[3].line, line[3].column, 7
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
                    TokenType.LABEL_USE,
                    offset,
                    line[0].line,
                    line[0].column,
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
        directive = line[0].value.lower()
        if directive in [".inter", ".text", ".data", ".bss", ".mmio"]:  # Sections
            self.current_section = directive
        elif directive == ".org":
            value = int(line[1].value, 0)
            if value < DEFAULT_SYMBOLS["CODE_START"]:
                self.current_section = ".inter"
                self.section_pointers[".inter"] = value
            elif value < DEFAULT_SYMBOLS["MMIO_BASE"]:
                self.current_section = ".text"
                self.section_pointers[".text"] = value
            else:
                self.current_section = "MMIO"
                self.section_pointers["MMIO"] = value

        elif directive in [".byte", ".word", ".string", ".ascii", ".space", ".fill"]:
            if directive == ".byte":
                for operand in line[1:]:
                    if operand.type == TokenType.COMMA or operand.type == TokenType.EOF:
                        continue
                    value = int(operand.value, 0)
                    self.write_memory(value, 1)
            elif directive == ".word":
                for operand in line[1:]:
                    if operand.type == TokenType.COMMA or operand.type == TokenType.EOF:
                        continue
                    value = int(operand.value, 0)
                    self.write_memory(value, 2)
            elif directive in [".string", ".ascii"]:
                value = line[1].value
                for char in value:
                    self.write_memory(ord(char), 1)
                if directive == ".string":
                    self.write_memory(0, 1)  # Null terminator for strings
            elif directive == ".space":
                for i in range(int(line[1].value)):
                    self.write_memory(0, 1)  # Fill with zeros
            elif directive == ".fill":
                fill_items = int(line[1].value, 0)  # Number of items to fill
                fill_size = int(line[3].value, 0)  # Size of each item in bytes
                fill_value = int(line[5].value, 0)  # Value to fill with
                for _ in range(fill_items):  # For each item
                    self.write_memory(fill_value, fill_size)

    def encode_instruction(self, line: List[Token]) -> None:
        """Encode an instruction line, reporting errors via Zx16Errors."""
        mnemonic = line[0].value.lower()
        if mnemonic not in INSTRUCTION_FORMAT:
            Zx16Errors.add_error(
                f"Unknown instruction '{mnemonic}'", line[0].line, line[0].column
            )
            return
        fields = INSTRUCTION_FORMAT[mnemonic]
        word = 0  # Initialize the instruction word

        # Lay down all constants
        for field in fields:
            if isinstance(field, ConstantField):
                word |= int(field.const_value, 2) << field.beginning

        # Consume tokens for punctuation, registers, immediates
        token_idx = 1
        for field in fields:
            if isinstance(field, ConstantField):  # Skip constants, they are already set
                continue

            if token_idx >= len(line):
                Zx16Errors.add_error(
                    f"Missing token(s) for field {TOKEN_TYPE_NAMES[field.expected_token]}",
                    line[-1].line,
                    line[-1].column,
                )
                return
            token = line[token_idx]

            # Punctuation
            if isinstance(field, PunctuationField):
                if token.type is not field.expected_token:
                    Zx16Errors.add_error(
                        f"Expected token {TOKEN_TYPE_NAMES[field.expected_token]}, got {TOKEN_TYPE_NAMES[field.expected_token]}",
                        token.line,
                        token.column,
                    )
                    return
                token_idx += 1
                continue

            # Register operand
            if isinstance(field, RegisterField):
                if token.type is not TokenType.REGISTER:
                    Zx16Errors.add_error(
                        f"Expected token REGISTER, got {TOKEN_TYPE_NAMES[field.expected_token]} for '{mnemonic}'",
                        token.line,
                        token.column,
                    )
                    return
                reg_index = int(token.value[1])
                word |= reg_index << field.beginning
                token_idx += 1
                continue

            # Immediate
            if isinstance(field, NumericField):
                if field.label ^ (token.type is TokenType.LABEL_USE):
                    Zx16Errors.add_error(
                        f"Expected token {TOKEN_TYPE_NAMES[TokenType.IMMEDIATE]}, got {TOKEN_TYPE_NAMES[token.type]} for '{mnemonic}'",
                        token.line,
                        token.column,
                    )
                    return
                if (not field.label) ^ (token.type is TokenType.IMMEDIATE):
                    Zx16Errors.add_error(
                        f"Expected token {TOKEN_TYPE_NAMES[TokenType.LABEL_USE]}, got {TOKEN_TYPE_NAMES[token.type]} for '{mnemonic}'",
                        token.line,
                        token.column,
                    )
                    return

                imm = int(token.value, 0)
                if field.label:
                    imm -= self.section_pointers[self.current_section]
                    imm = int(imm / 2)
                checker = sign_extend(imm, token.width, field.signed)
                if not (field.min_value <= checker <= field.max_value):
                    Zx16Errors.add_error(
                        f"Immediate value {imm} out of range [{field.min_value}, {field.max_value}] for '{mnemonic}'",
                        token.line,
                        token.column,
                    )
                    return
                # encode: split or contiguous
                if field.allocations:
                    prev_width = 0
                    for alloc in field.allocations:
                        width = alloc.end - alloc.beginning + 1
                        mask = ((1 << width) - 1) << prev_width
                        word |= (imm & mask) << (alloc.beginning - prev_width)
                        prev_width += width

                else:
                    width = field.end - field.beginning + 1
                    mask = (1 << width) - 1
                    word |= (imm & mask) << field.beginning
                token_idx += 1
                continue

            # If we get here, it’s an unexpected field type, this should not happen
            Zx16Errors.add_error(
                f"Unhandled field type {type(field).__name__} in '{mnemonic}'",
                token.line,
                token.column,
            )
            return

        if token_idx < len(line):
            Zx16Errors.add_error(
                f"Unexpected token(s) after instruction '{mnemonic}'",
                line[token_idx].line,
                line[token_idx].column,
            )
            return
        # 3) Write out the two-byte instruction
        self.write_memory(word, 2)
        # DEBUG MODE
        # if self.verbose:
        #     print(
        #         f"Encoded {mnemonic}: 0x{word:04X} 0b{word:016b} @ {self.current_section}:{self.section_pointers[self.current_section]} or address {self.section_pointers[self.current_section]:04X}"
        #     )

    def execute(self) -> bytearray:
        self.lionize()

        for idx, line in enumerate(self.lines):
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
