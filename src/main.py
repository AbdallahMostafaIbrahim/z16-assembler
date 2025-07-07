import argparse
import sys
from typing import List
from error_handler import Zx16Errors
from tokenizer import Tokenizer
from pathlib import Path
from first_pass import FirstPass
from second_pass import SecondPass
from definitions import FirstPassResult


class ZX16Assembler:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.binary_output = bytearray(65536)

    def assemble(self, source_code: str):
        tokenizer = Tokenizer(source_code)

        tokens = tokenizer.tokenize()

        if Zx16Errors.has_errors():
            return

        pass1 = FirstPass(tokens, self.verbose)
        result = pass1.execute()

        if Zx16Errors.has_errors():
            return

        if self.verbose:
            self.print_symbol_table(result)

        pass2 = SecondPass(result.tokens, result.memory_layout, self.verbose)
        self.binary_output = pass2.execute()

    def print_symbol_table(self, result: FirstPassResult):
        print("Constants:")
        constants = [
            (name, sym)
            for name, sym in result.symbol_table.items()
            if sym.section is None
        ]
        for name, sym in sorted(constants, key=lambda item: item[1].value):
            print(f"{name:<30} 0x{sym.value:04X}")

        print("Symbol Table:")
        others = [
            (name, sym)
            for name, sym in result.symbol_table.items()
            if sym.section is not None
        ]
        for name, sym in sorted(others, key=lambda item: item[1].value):
            print(f"{name:<30} 0x{sym.value:04X}  {sym.section}")

    def get_binary_output(self) -> bytes:
        """Get binary output."""
        return bytes(self.binary_output)

    def get_intel_hex_output(self) -> str:
        pass

    def get_verilog_output(self, module_name: str = "program_memory") -> str:
        pass

    def get_memory_file_output(self, sparse: bool = False) -> str:
        pass

    def get_listing_output(self, source_lines: List[str]) -> str:
        pass

    def print_errors(self) -> List[str]:
        """Get a list of errors."""
        return Zx16Errors.print_errors()


def main():
    """Main entry point for the assembler."""
    parser = argparse.ArgumentParser(description="ZX16 Assembler")
    parser.add_argument("input", help="Input assembly file")
    # TODO - Add support for multiple input files
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument(
        "-f",
        "--format",
        choices=["bin", "hex", "verilog", "mem"],
        default="bin",
        help="Output format",
    )
    # TODO - Add listing
    parser.add_argument("-l", "--listing", help="Generate listing file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    # TODO make those
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
        print(f"Error: reading Input file: {e}", file=sys.stderr)
        return 1

    assembler = ZX16Assembler(args.verbose)
    assembler.assemble(source_code)
    assembler.print_errors()

    # Generate output
    if args.output:
        output_file = args.output
    else:
        # Generate default output filename
        input_path = Path(args.input)
        if args.format == "bin":
            output_file = input_path.with_suffix(".bin")
        elif args.format == "hex":
            output_file = input_path.with_suffix(".hex")
        elif args.format == "verilog":
            output_file = input_path.with_suffix(".v")
        elif args.format == "mem":
            output_file = input_path.with_suffix(".mem")

    try:
        if args.format == "bin":
            output_data = assembler.get_binary_output()
            with open(output_file, "wb") as f:
                f.write(output_data)
        # elif args.format == "hex":
        #     output_data = assembler.get_intel_hex_output()
        #     with open(output_file, "w", encoding="utf-8") as f:
        #         f.write(output_data)

        # elif args.format == "verilog":
        #     output_data = assembler.get_verilog_output(args.verilog_module)
        #     with open(output_file, "w", encoding="utf-8") as f:
        #         f.write(output_data)

        # elif args.format == "mem":
        #     output_data = assembler.get_memory_file_output(args.mem_sparse)
        #     with open(output_file, "w", encoding="utf-8") as f:
        #         f.write(output_data)

        # if args.verbose:
        #     print(f"Output written to {output_file}")
        # # Generate listing file if requested
        # if args.listing:
        #     listing_content = assembler.get_listing_output(source_lines)
        #     with open(args.listing, "w", encoding="utf-8") as f:
        #         f.write(listing_content)
        #     if args.verbose:
        #         print(f"Listing written to {args.listing}")

    except IOError as e:
        print(f"Error: writing output file {e} was not successful", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
