import sys
from typing import List
from dataclasses import dataclass


@dataclass
class AssemblerMessage:
    """Represents an assembly error or warning."""

    message: str
    line: int
    column: int


class Zx16Errors(object):
    """Class to manage errors and warnings in the ZX16 assembler."""

    errors: List[AssemblerMessage] = []
    warnings: List[AssemblerMessage] = []

    def __new__(cls):
        raise TypeError("Static classes cannot be instantiated")

    @staticmethod
    def has_errors() -> bool:
        """Check if there are any errors."""
        return len(Zx16Errors.errors) > 0

    @staticmethod
    def add_error(
        message: str,
        line: int,
        column: int = 0,
    ) -> None:
        """Add an error to the error list."""
        Zx16Errors.errors.append(AssemblerMessage(message, line, column))

    @staticmethod
    def clear_errors():
        Zx16Errors.errors.clear()

    @staticmethod
    def add_warning(
        message: str,
        line: int,
        column: int = 0,
    ) -> None:
        """Add a warning to the warning list."""
        Zx16Errors.warnings.append(AssemblerMessage(message, line, column))

    @staticmethod
    def clear_warnings():
        Zx16Errors.warnings.clear()

    @staticmethod
    def print_errors() -> None:
        """Print all errors and warnings."""
        for error in Zx16Errors.errors:
            print(f"Error at line {error.line}: {error.message}", file=sys.stderr)

        for warning in Zx16Errors.warnings:
            print(f"Warning at line {warning.line}: {warning.message}", file=sys.stderr)

        if Zx16Errors.errors:
            print(
                f"\nAssembly failed with {len(Zx16Errors.errors)} errors, {len(Zx16Errors.warnings)} warnings.",
                file=sys.stderr,
            )
        elif Zx16Errors.warnings:
            print(f"\nAssembly completed with {len(Zx16Errors.warnings)} warnings.")
        else:
            print("Assembly completed successfully.")
