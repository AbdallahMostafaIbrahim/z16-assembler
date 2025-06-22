import argparse
import sys
from typing import Dict, List, Literal
from utils import AssemblerMessage, Symbol, SectionType
from tokenizer import Tokenizer, TokenType
from parser import ZX16Parser
from constants import TRUE_INSTRUCTIONS, PSEUDO_INSTRUCTIONS, DEFAULT_SYMBOLS


class ZX16Assembler:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[AssemblerMessage] = []
        self.warnings: List[AssemblerMessage] = []
        self.parser: ZX16Parser = None
        self.symbol_table: Dict[str, Symbol] = {}

        self.section_pointers: Dict[str, int] = {
            # Those are all relative to the start of each section
            ".base": 0x0000,
            ".text": 0x0000,
            ".data": 0x0000,
            ".bss": 0x0000,
        }
        self.current_section: Literal[".base", ".text", ".data", ".bss"] = ".text"

        # Memory layout for the assembler, still needs to be calculated after pass 1
        self.memory_layout = {
            ".text": DEFAULT_SYMBOLS["CODE_START"],
            ".data": 0x0000,
            ".bss": 0x0000,
        }

        self.data = bytearray(65536)  # Data to be assembled (64KB)

    def add_error(
        self,
        message: str,
        line: int,
        column: int = 0,
    ) -> None:
        """Add an error to the error list."""
        self.errors.append(AssemblerMessage(message, line, column))

    def add_warning(
        self,
        message: str,
        line: int,
        column: int = 0,
    ) -> None:
        """Add a warning to the warning list."""
        self.warnings.append(AssemblerMessage(message, line, column))

    def print_errors(self) -> None:
        """Print all errors and warnings."""
        for error in self.errors:
            print(f"Error at line {error.line}: {error.message}", file=sys.stderr)

        for warning in self.warnings:
            print(f"Warning at line {warning.line}: {warning.message}", file=sys.stderr)

        if self.errors:
            print(
                f"\nAssembly failed with {len(self.errors)} errors, {len(self.warnings)} warnings.",
                file=sys.stderr,
            )
        elif self.warnings:
            print(f"\nAssembly completed with {len(self.warnings)} warnings.")
        else:
            print("Assembly completed successfully.")

    def current_address(self) -> int:
        return self.section_pointers[self.current_section]

    def pointer_advance(self, size: int = 2, section: SectionType = None):
        self.section_pointers[section or self.current_section] += size

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

    def parse_constant(self):
        p = self.parser
        if p.peek().type != TokenType.IDENTIFIER:
            self.add_error("Expected identifier after directive", p.current_token.line)
            return
        p.advance_and_delete()
        identifier = p.current_token.value
        if p.peek().type != TokenType.COMMA:
            self.add_error("Expected comma after identifier", p.current_token.line)
            return
        p.advance_and_delete()  # Skip the comma
        if p.peek().type not in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
            self.add_error(
                "Expected immediate or character value after comma",
                p.current_token.line,
            )
            return
        p.advance_and_delete()  # Move to the value token
        value = int(p.current_token.value, 0)  # Convert to integer
        self.define_symbol(identifier, value, "const", p.current_token.line)
        p.advance_and_delete()  # Move to the next token

    def parse_label(self):
        p = self.parser
        label_name = p.current_token.value
        self.define_symbol(
            label_name,
            self.current_address(),
            self.current_section,
            p.current_token.line,
        )
        p.advance_and_delete()

    def parse_directive(self):
        p = self.parser
        directive = p.current_token.value.lower()
        line = p.current_token.line

        # Memory Layout Directives
        if directive in [".text", ".data", ".bss"]:  # Sections
            self.current_section = directive
            p.advance()
        elif directive == ".org":  # ORG :(
            if self.current_section not in [".text", ".base"]:
                self.add_error(
                    f".org directive can only be used in the .text section, not in {self.current_section}. It works like .space in the .text section",
                    line,
                )
                return
            if p.peek().type != TokenType.IMMEDIATE:
                self.add_error("Expected immediate value after .org directive", line)
                return
            p.advance()  # Move to the immediate value
            value = int(p.current_token.value, 0)
            # TODO: Check if the value aligns aka is a multiple of 2
            if value < 0 or value >= DEFAULT_SYMBOLS["STACK_TOP"]:
                self.add_error(
                    f"Value {value:#04x} out of range for .org directive (RAM, ROM, interrupt)",
                    line,
                )
                return

            if value < DEFAULT_SYMBOLS["CODE_START"]:
                self.current_section = ".base"
                self.section_pointers[".base"] = value
            else:
                self.section_pointers[".text"] = value - DEFAULT_SYMBOLS["CODE_START"]

            p.advance()
        # Data Directives
        elif directive in [".byte", ".word"]:
            if p.peek().type not in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                self.add_error(
                    f"Expected immediate or character value after {directive} directive",
                    line,
                )
                return
            while p.peek().type in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                # TODO: Check if the value is not bigger than a byte
                self.pointer_advance(1 if directive == ".byte" else 2)
                p.advance()
                if p.peek().type == TokenType.COMMA:
                    p.advance()
                else:
                    break
            if p.current_token.type == TokenType.COMMA:
                self.add_error(
                    f"Unexpected token '{p.peek().value}' after {directive} directive",
                    p.peek().line,
                )
                p.advance()
            p.advance()
        elif directive in [".string", ".ascii"]:
            if p.peek().type == TokenType.STRING:
                p.advance()
                string_len = len(p.current_token.value)
                if directive == ".string":
                    string_len += 1  # Null terminator
                print(f"String length: {string_len}, String: {p.current_token.value}")
                self.pointer_advance(string_len)
                p.advance()
            else:
                self.add_error(f"Expected string after {directive}", line)
        elif directive == ".space":
            if p.peek().type == TokenType.IMMEDIATE:
                p.advance()
                space_size = int(p.current_token.value)
                self.pointer_advance(space_size)
                p.advance()
            else:
                self.add_error("Expected size after .space", line)
        else:
            self.add_error(f"Unknown directive '{directive}'", p.current_token.line)
            p.advance()

    def pass1(self):
        """First pass of the assembler."""
        p = self.parser

        # Fill the symbol tables with the constants using .equ and .set directives
        while p.current_token.type != TokenType.EOF:
            if p.current_token.type == TokenType.DIRECTIVE:
                if p.current_token.value in [".equ", ".set"]:
                    self.parse_constant()
            p.advance()

        p.reset()

        while p.current_token.type != TokenType.EOF:
            if p.current_token.type == TokenType.LABEL:
                self.parse_label()
            elif p.current_token.type == TokenType.IDENTIFIER:
                potential = p.current_token.value.lower()
                # TODO: For now, we can add instructions in any section
                if potential in TRUE_INSTRUCTIONS:
                    self.pointer_advance(2)
                elif potential in PSEUDO_INSTRUCTIONS:
                    self.pointer_advance(PSEUDO_INSTRUCTIONS[potential])

                # Keep advancing until we find a new line
                while p.peek().type not in [TokenType.NEWLINE, TokenType.EOF]:
                    p.advance()
                p.advance()

            elif p.current_token.type == TokenType.DIRECTIVE:
                self.parse_directive()

            if p.current_token.type not in [TokenType.NEWLINE, TokenType.EOF]:
                self.add_error(
                    f"Unexpected token '{p.current_token.value}'",
                    p.current_token.line,
                    p.current_token.column,
                )

            p.advance()

    def pass2(self):
        p = self.parser
        while p.peek().type != TokenType.EOF:
            p.advance()

    def calculate_memory_layout(self):
        self.memory_layout[".data"] = (
            self.section_pointers[".text"] + DEFAULT_SYMBOLS["CODE_START"]
        )
        self.memory_layout[".bss"] = (
            self.memory_layout[".data"] + self.section_pointers[".data"]
        )

    def assemble(self, source_code: str, filename: str) -> bool:
        """Assemble the given source code."""
        tokenizer = Tokenizer(source_code)
        try:
            tokens = tokenizer.tokenize()
        except Exception as e:
            self.add_error(f"Tokenization error: {e}", tokenizer.line, tokenizer.column)
            return False

        for token in tokens:
            if token.type == TokenType.NEWLINE:
                print(f"")
            else:
                print(
                    f"Token: {token.type} - {token.value} at line {token.line}, column {token.column}"
                )

        self.parser = ZX16Parser(tokens)

        self.pass1()
        self.calculate_memory_layout()

        self.parser.reset()  # Reset parser for second pass
        self.pass2()

        # If verbose, print the symbol table
        if self.verbose:
            print("Symbol Table:")
            for name, symbol in self.symbol_table.items():
                print(f"{name}: {symbol.value:#04x} (section: {symbol.section})")

        return True


def main():
    """Main entry point for the assembler."""
    parser = argparse.ArgumentParser(description="ZX16 Assembler")
    parser.add_argument("input", help="Input assembly file")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument(
        "-f",
        "--format",
        choices=["bin", "hex", "verilog", "mem"],
        default="bin",
        help="Output format",
    )
    parser.add_argument("-l", "--listing", help="Generate listing file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--verilog-module", default="program_memory", help="Verilog module name"
    )
    parser.add_argument(
        "--mem-sparse", action="store_true", help="Generate sparse memory file"
    )

    args = parser.parse_args()

    # Read input file
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Create assembler
    assembler = ZX16Assembler(verbose=args.verbose)

    # Assemble
    success = assembler.assemble(source_code, args.input)

    # Print errors/warnings
    assembler.print_errors()

    if not success:
        return 1

    # Generate output
    # if args.output:
    #     output_file = args.output
    # else:
    #     # Generate default output filename
    #     input_path = Path(args.input)
    #     if args.format == "bin":
    #         output_file = input_path.with_suffix(".bin")
    #     elif args.format == "hex":
    #         output_file = input_path.with_suffix(".hex")
    #     elif args.format == "verilog":
    #         output_file = input_path.with_suffix(".v")
    #     elif args.format == "mem":
    #         output_file = input_path.with_suffix(".mem")

    # try:
    #     if args.format == "bin":
    #         output_data = assembler.get_binary_output()
    #         with open(output_file, "wb") as f:
    #             f.write(output_data)

    #     elif args.format == "hex":
    #         output_data = assembler.get_intel_hex_output()
    #         with open(output_file, "w", encoding="utf-8") as f:
    #             f.write(output_data)

    #     elif args.format == "verilog":
    #         output_data = assembler.get_verilog_output(args.verilog_module)
    #         with open(output_file, "w", encoding="utf-8") as f:
    #             f.write(output_data)

    #     elif args.format == "mem":
    #         output_data = assembler.get_memory_file_output(args.mem_sparse)
    #         with open(output_file, "w", encoding="utf-8") as f:
    #             f.write(output_data)

    #     if args.verbose:
    #         print(f"Output written to {output_file}")

    #     # Generate listing file if requested
    #     if args.listing:
    #         listing_content = assembler.get_listing_output(source_lines)
    #         with open(args.listing, "w", encoding="utf-8") as f:
    #             f.write(listing_content)
    #         if args.verbose:
    #             print(f"Listing written to {args.listing}")

    # except IOError as e:
    #     print(f"Error writing output file: {e}", file=sys.stderr)
    #     return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
