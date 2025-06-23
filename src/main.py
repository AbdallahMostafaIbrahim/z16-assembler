import argparse
import sys
from typing import Dict, List
from utils import AssemblerMessage, Symbol, Token
from tokenizer import Tokenizer, TokenType
from parser import ZX16Parser
from constants import TRUE_INSTRUCTIONS, PSEUDO_INSTRUCTIONS

  

class ZX16Assembler:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[AssemblerMessage] = []
        self.warnings: List[AssemblerMessage] = []
        self.symbol_table: Dict[str, Symbol] = {}
        self.parser: ZX16Parser = None
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

    def pass1(self):
        """First pass of the assembler."""
        p = self.parser

        # Fill the symbol tables with the constants using .equ and .set directives
        while p.current_token.type != TokenType.EOF:
            if p.current_token.type == TokenType.DIRECTIVE:
                if p.current_token.value in [".equ", ".set"]:
                    p.parse_constant()
            p.advance()
         # adding constants to the symbol table
        self.symbol_table= p.symbol_table
         # TODO: Handle ifs
        # Another Loop
        p.reset()
        while p.current_token.type != TokenType.EOF:
            if p.current_token.type == TokenType.LABEL:
                p.parse_label()
            elif p.current_token.type == TokenType.IDENTIFIER:
                potential = p.current_token.value.lower()
                # TODO: For now, we can add instructions in any section
                if potential in TRUE_INSTRUCTIONS:
                    p.pointer_advance(2)
                elif potential in PSEUDO_INSTRUCTIONS:
                    p.pointer_advance(PSEUDO_INSTRUCTIONS[potential])

                # Keep advancing until we find a new line
                while p.peek().type not in [TokenType.NEWLINE, TokenType.EOF]:
                    p.advance()
                p.advance()

            elif p.current_token.type == TokenType.DIRECTIVE:
                p.parse_directive()
            
            #Syntax errors
            if p.current_token.type not in [TokenType.NEWLINE, TokenType.EOF]:
                self.add_error(
                    f"Unexpected token '{p.current_token.value}'",
                    p.current_token.line,
                    p.current_token.column,
                )

            p.advance()

    def pass2(self):
        for line in self.parser.lines:
            if line[0] == TokenType.EOF:
                break
            if line[0] == TokenType.DIRECTIVE:
                pass
            elif line[0] == TokenType.IDENTIFIER:
                pass

    
    def assemble(self, source_code: str, filename: str) -> bool:
        """Assemble the given source code."""
        tokenizer = Tokenizer(source_code)
        try:
            tokens = tokenizer.tokenize()
        except Exception as e:
            self.add_error(f"Tokenization error: {e}", tokenizer.line, tokenizer.column)
            return False

        self.parser = ZX16Parser(tokens)

        self.pass1()

        # for token in tokens:
        #     if token.type == TokenType.NEWLINE:
        #         print(f"")
        #     else:
        #         print(
        #             f"Token: {token.type} - {token.value} at line {token.line}, column {token.column}"
                # )
        self.parser.calculate_memory_layout()
        self.parser.lionize()
        # Print parsed lines for debugging
        
        # self.parser.reset()  # Reset parser for second pass
        # self.pass2()

        # If verbose, print the symbol table
        if self.verbose:
            for line_number, line in enumerate(self.parser.lines, start=1):
                if line[0] == TokenType.EOF:
                    break
                print(f"Line {line_number}: {[token.value for token in line]}")
            print("Symbol Table:")
            for name, symbol in self.symbol_table.items():
                print(f"{name}: {symbol.value} (section: {symbol.section})")

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
