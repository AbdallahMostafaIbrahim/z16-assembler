from typing import List
from definitions import Token, TokenType
from error_handler import Zx16Errors
from constants import char_tokens


# TODO ANY token error stop main
class Tokenizer:
    """Lexical analyzer for ZX16 assembly language."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.terminate = False
        self.tokens: List[Token] = []

    def current_char(self) -> str:
        """Get the current character."""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return ""

    def peek_char(self, offset: int = 1) -> str:
        """Peek at character with offset."""
        peek_pos = self.pos + offset
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return ""

    def advance(self) -> None:
        """Advance to the next character."""
        if self.pos < len(self.text) and self.text[self.pos] == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def skip_whitespace(self) -> None:
        """Skip whitespace except newlines."""
        while self.current_char() in " \t\r" and self.pos < len(self.text):
            self.advance()

    def read_string(self) -> str:
        """Read a string literal."""
        result = ""

        while (
            self.current_char()
            and self.current_char() != '"'
            and self.current_char() != "\n"
        ):
            if self.current_char() == "\\":
                self.advance()
                escape_char = self.current_char()
                escape_map = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}
                result += escape_map.get(escape_char, escape_char)
            else:
                result += self.current_char()
            self.advance()

        if self.current_char() == '"':
            self.advance()  # Skip closing quote
        else:
            Zx16Errors.add_error(
                "Tokenizer Error: Unterminated string literal", self.line, self.column
            )
            self.terminate = True

        return result

    def read_number(self) -> tuple[int, int]:
        """Read a numeric literal."""
        start_pos = self.pos
        counter = 0
        # Handle different number bases
        if self.current_char() == "0" and self.peek_char():
            self.advance()
            if self.current_char().lower() == "x":
                # Hexadecimal
                self.advance()
                while (
                    self.current_char().lower() in "0123456789abcdef"
                    and self.pos < len(self.text)
                ):
                    counter += 4
                    self.advance()
                return int(self.text[start_pos : self.pos], 16), counter
            elif self.current_char().lower() == "b":
                # Binary
                self.advance()
                while self.current_char() in "01" and self.pos < len(self.text):
                    counter += 1
                    self.advance()
                return int(self.text[start_pos : self.pos], 2), counter
            elif self.current_char().lower() == "o":
                # Octal
                self.advance()
                while self.current_char() in "01234567" and self.pos < len(self.text):
                    counter += 3
                    self.advance()
                return int(self.text[start_pos : self.pos], 8), counter
            else:
                # Decimal starting with 0
                self.pos = start_pos

        # Decimal number
        while self.current_char().isdigit():
            self.advance()

        return int(self.text[start_pos : self.pos]), counter

    def read_identifier(self) -> str:
        """Read an identifier."""
        start_pos = self.pos

        while (
            self.current_char().isalnum()
            or self.current_char() in "_"
            and self.pos < len(self.text)
        ):
            self.advance()

        return self.text[start_pos : self.pos]

    def get_register(self, identifier: str) -> str:
        """Check if identifier is a register name."""
        register_names = {
            "t0": "x0",
            "ra": "x1",
            "sp": "x2",
            "s0": "x3",
            "s1": "x4",
            "t1": "x5",
            "a0": "x6",
            "a1": "x7",
        }
        if identifier in register_names.values():
            return identifier
        if identifier in register_names:
            return register_names[identifier]
        return ""

    def tokenize(self) -> List[Token]:
        """Tokenize the input text."""
        while self.pos < len(self.text) and not self.terminate:
            self.skip_whitespace()

            # # Detect end of input
            # if not self.current_char():
            #     break

            line, column = self.line, self.column

            # Handle newlines
            if self.current_char() == "\n":
                self.tokens.append(Token(TokenType.NEWLINE, "\n", line, column))
                self.advance()
                continue

            # Handle comments
            if self.current_char() == "#":
                while self.current_char() and self.current_char() != "\n":
                    self.advance()
                # For simplicity, we ignore comments entirely
                continue

            # TODO TEST - Handle block comments
            # Handle block comments
            if self.current_char() == "/" and self.peek_char() == "*":
                self.advance()  # Skip '/'
                self.advance()  # Skip '*'
                while self.pos < len(self.text):
                    if self.current_char() == "*" and self.peek_char() == "/":
                        self.advance()  # Skip '*'
                        self.advance()  # Skip '/'
                        break
                    self.advance()
                # For simplicity, we ignore block comments entirely
                continue
            # Handle negative numbers
            if self.current_char() == "-" and self.peek_char().isdigit():
                self.advance()  # Skip '-'
                number_value, counter = self.read_number()
                number_value = -number_value
                self.tokens.append(
                    Token(TokenType.IMMEDIATE, str(number_value), line, column, counter)
                )
                continue
            # Handle numbers
            if self.current_char().isdigit():
                number_value, counter = self.read_number()
                self.tokens.append(
                    Token(TokenType.IMMEDIATE, str(number_value), line, column, counter)
                )
                continue

            # Handle single character tokens
            if self.current_char() in char_tokens:
                token_type = char_tokens[self.current_char()]
                self.tokens.append(Token(token_type, self.current_char(), line, column))
                self.advance()
                continue

            # Handle string literals
            if self.current_char() == '"':
                self.advance()  # Skip opening quote
                string_value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, string_value, line, column))
                continue

            # Handle character literals
            if self.current_char() == "'":
                self.advance()  # Skip opening quote
                if self.current_char() == "\\":
                    self.advance()
                    escape_char = self.current_char()
                    escape_map = {
                        "n": ord("\n"),
                        "t": ord("\t"),
                        "r": ord("\r"),
                        "\\": ord("\\"),
                        "'": ord("'"),
                    }
                    char_value = escape_map.get(escape_char, ord(escape_char))
                else:
                    char_value = ord(self.current_char())

                self.advance()

                if self.current_char() == "'":
                    self.advance()  # Skip closing quote
                else:
                    Zx16Errors.add_error(
                        "Tokenizer Error: Unterminated character literal", line, column
                    )
                    return

                self.tokens.append(
                    Token(TokenType.IMMEDIATE, str(char_value), line, column)
                )
                continue

            # Handle directives
            if self.current_char() == "." and (
                self.peek_char().isalpha() or self.peek_char() == "_"
            ):
                self.advance()  # Skip '.'
                identifier = self.read_identifier()
                self.skip_whitespace()
                if self.current_char() == ":":
                    self.advance()  # Skip ':'
                    self.tokens.append(
                        Token(TokenType.LABEL_DEF, identifier, line, column)
                    )
                    self.tokens.append(Token(TokenType.NEWLINE, "\n", line, column))
                else:
                    self.tokens.append(
                        Token(TokenType.DIRECTIVE, f".{identifier}", line, column)
                    )
                continue

            # Handle identifiers, labels, instructions, and registers
            if self.current_char().isalpha() or self.current_char() == "_":
                identifier = self.read_identifier()

                # Check if it's followed by a colon (label)
                self.skip_whitespace()
                if self.current_char() == ":":
                    self.advance()  # Consume the colon
                    self.tokens.append(
                        Token(TokenType.LABEL_DEF, identifier, line, column)
                    )
                    self.tokens.append(Token(TokenType.NEWLINE, "\n", line, column))
                    continue

                # Check if it's a register
                if self.get_register(identifier) != "":
                    self.tokens.append(
                        Token(
                            TokenType.REGISTER,
                            self.get_register(identifier),
                            line,
                            column,
                        )
                    )
                else:
                    # Assume it's an instruction or symbol (identifier)
                    self.tokens.append(
                        Token(TokenType.IDENTIFIER, identifier, line, column)
                    )
                continue

            # Unknown character - throw an error
            Zx16Errors.add_error(
                f"Tokenizer Error: Unknown character '{self.current_char()}'",
                line,
                column,
            )
            self.advance()
        self.tokens.append(Token(TokenType.EOF, "EOF", self.line, self.column))
        return self.tokens
