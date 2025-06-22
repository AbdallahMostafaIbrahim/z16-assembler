import argparse
import re
import sys
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Union, Any, Literal
from pathlib import Path
from utils import AssemblerMessage, Symbol
from tokenizer import Tokenizer, TokenType
from parser import ZX16Parser

ADDRESSES = {".text": 0x0020, ".data": 0x8000, ".bss": 0x9000}


class ZX16Assembler:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[AssemblerMessage] = []
        self.warnings: List[AssemblerMessage] = []
        self.parser: ZX16Parser = None
        self.symbol_table: Dict[str, Symbol] = {}
        self.current_address: int = 0x0000  # Starting address for the ZX16
        self.data = bytearray()  # Data to be assembled

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

    def define_symbol(
        self, name: str, value: int, line: int = 0, is_global: bool = False
    ) -> None:
        """Define a symbol."""
        if name in self.symbol_table:
            if self.symbol_table[name].defined:
                self.add_error(f"Symbol '{name}' already defined", line)
                return

        self.symbol_table[name] = Symbol(
            name, value, defined=True, global_symbol=is_global, line=line
        )

    def pass1(self):
        """First pass of the assembler."""
        p = self.parser
        self.current_address = 0x0000  # Starting address for the ZX16
        while p.peek().type != TokenType.EOF:

            if p.current_token.type == TokenType.LABEL:
                label_name = p.current_token.value
                self.define_symbol(
                    label_name, self.current_address, p.current_token.line
                )
                p.advance()
                continue

            if p.current_token.type == TokenType.DIRECTIVE:
                directive = p.current_token.value
                line = p.current_token.line
                if directive == ".text":
                    self.current_address = ADDRESSES[".text"]
                    p.advance()
                elif directive == ".data":
                    self.current_address = ADDRESSES[".data"]
                    p.advance()
                elif directive == ".bss":
                    self.current_address = ADDRESSES[".bss"]
                    p.advance()
                elif directive == ".org":
                    if p.peek().type == TokenType.IMMEDIATE:
                        self.current_address = int(p.peek().value, 0)
                        p.advance()
                    else:
                        self.add_error(
                            "Expected immediate value after .org directive",
                            p.current_token.line,
                        )
                        continue
                elif directive in [".equ", ".set"]:
                    if p.peek().type == TokenType.INSTRUCTION:
                        p.advance()
                        symbol_name = p.current_token.value
                        if p.peek().type == TokenType.COMMA:
                            p.advance()
                        else:
                            self.add_error(f"Expected comma after {symbol_name}", line)
                            continue

                        if p.peek().type == TokenType.IMMEDIATE:
                            value = int(p.peek().value)
                            self.define_symbol(symbol_name, value, line)
                            p.advance()
                        else:
                            self.add_error(
                                "Expected immediate value after symbol name", line
                            )
                    else:
                        self.add_error(f"Expected symbol name after {directive}", line)
                elif directive == ".global":
                    # We will take a look at this in the next pass, probably
                    p.advance()
                elif directive == ".byte":
                    while p.peek().type in [TokenType.IMMEDIATE, TokenType.CHARACTER]:
                        self.current_address += 1
                        p.advance()
                        if p.peek().type == TokenType.COMMA:
                            p.advance()
                        else:
                            break
                elif directive == ".word":
                    while p.peek().type == TokenType.IMMEDIATE:
                        self.current_address += 2
                        p.advance()
                        if p.peek().type == TokenType.COMMA:
                            p.advance()
                        else:
                            break
                elif directive in [".string", ".ascii"]:
                    if p.peek().type == TokenType.STRING:
                        string_len = len(p.current_token.value)
                        if directive == ".string":
                            string_len += 1  # Null terminator
                        self.current_address += string_len
                        p.advance()
                    else:
                        self.add_error(f"Expected string after {directive}", line)
                elif directive == ".space":
                    if p.peek().type == TokenType.IMMEDIATE:
                        space_size = int(p.current_token.value)
                        self.current_address += space_size
                        p.advance()
                    else:
                        self.add_error("Expected size after .space", line)
                else:
                    self.add_error(
                        f"Unknown directive '{directive}'", p.current_token.line
                    )
                    p.advance()
                continue

            if p.current_token.type == TokenType.INSTRUCTION:
                self.current_address += 2  # Each instruction is 2 bytes
                p.advance()
                continue

            p.advance()

    def pass2(self):
        p = self.parser
        self.current_address = 0x0000  # Starting address for the ZX16
        while p.peek().type != TokenType.EOF:
            p.advance()

    def assemble(self, source_code: str, filename: str) -> bool:
        """Assemble the given source code."""
        tokenizer = Tokenizer(source_code)
        tokens = tokenizer.tokenize()

        self.parser = ZX16Parser(tokens)

        self.pass1()
        self.parser.reset()  # Reset parser for second pass
        self.pass2()

        # If verbose, print the symbol table
        if self.verbose:
            print("Symbol Table:")
            for name, symbol in self.symbol_table.items():
                print(f"{name}: {symbol.value:#04x} (defined: {symbol.defined})")

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
            source_lines = source_code.splitlines()
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
