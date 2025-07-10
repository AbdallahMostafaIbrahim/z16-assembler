# Z16 Assembly Language Support

> **NOTE:** This extension is completely vibe coded with claude

A meh Visual Studio Code extension providing full language support for Z16 Assembly programming, including syntax highlighting, intelligent code completion, error detection, and advanced navigation features.

---

## 🚀 Features

### 🎨 Syntax Highlighting

- **Complete instruction set** highlighting with color-coded instruction types
- **Register highlighting** for all Z16 registers (x0-x7, t0-t1, ra, sp, s0-s1, a0-a1)
- **Label highlighting** for jump targets and function definitions
- **Directive highlighting** for assembler directives (.text, .data, .inter, .bss, .mmio)
- **Comment highlighting** for line comments starting with `#`
- **Number highlighting** for decimal, hexadecimal, and character literals
- **String highlighting** for quoted strings with escape sequence support

### 💡 Intelligent Code Completion

- **51 Z16 instructions** with detailed syntax templates and tab navigation
- **8 Z16 registers** with alias information (e.g., t0 ↔ x0)
- **Assembly directives** with proper syntax (.byte, .word, .string, .ascii, .space, etc.)
- **Label autocomplete** - automatically detects and suggests all labels in the current file
- **Context-aware suggestions** - directives only appear after typing `.`
- **Snippet support** with placeholder navigation using Tab key

### 📚 Rich Documentation

- **Hover documentation** for all instructions with operation details
- **Register alias information** - hover over any register to see its alternate name
- **Instruction categories** clearly explained (R-type, I-type, B-type, etc.)
- **Pseudo-instruction expansion** details showing what they compile to

### 🔍 Code Navigation

- **Go to Definition** (Ctrl+Click or F12) - jump from label references to definitions
- **Find All References** (Shift+F12) - see all usages of a label
- **Symbol navigation** through the VS Code outline panel
- **Breadcrumb navigation** for easy file structure understanding

### ⚠️ Error Detection

- **Duplicate label detection** with red squiggles and error messages
- **Cross-reference validation** showing line numbers of conflicts
- **Real-time error checking** as you type
- **Problems panel integration** for easy error navigation

### 🔧 Smart Indentation

- **Automatic indentation** for labels and instructions
- **Configurable indentation rules** that understand assembly structure
- **Smart line continuation** that doesn't interfere with jump instructions

## 📖 Supported Z16 Instruction Set

### R-Type Instructions (13 total)

```assembly
ADD x1, x2
SUB x1, x2
SLT x1, x2
SLTU x1, x2
SLL x1, x2
SRL x1, x2
SRA x1, x2
OR x1, x2
AND x1, x2
XOR x1, x2
MV x1, x2
JR x1
JALR x1, x2
```

### I-Type Instructions (10 total)

```assembly
ADDI x1, -42
SLTI x1, 10
SLTUI x1, 10
SLLI x1, 3
SRLI x1, 3
SRAI x1, 3
ORI x1, 0x0F
ANDI x1, 0x0F
XORI x1, 0x0F
LI x1, 42
```

### B-Type Instructions (8 total)

```assembly
BEQ x1, x2, label
BNE x1, x2, label
BZ x1, label
BNZ x1, label
BLT x1, x2, label
BGE x1, x2, label
BLTU x1, x2, label
BGEU x1, x2, label
```

### Memory Instructions (5 total)

```assembly
# Load Instructions
LB x1, 4(x2)
LW x1, -2(x2)
LBU x1, 4(x2)

# Store Instructions
SB x1, 4(x2)
SW x1, -2(x2)
```

### Jump Instructions (2 total)

```assembly
J label             # PC ← PC + offset
JAL x1, function    # rd ← PC + 2; PC ← PC + offset
```

### Upper Immediate Instructions (2 total)

```assembly
LUI x1, 0x1000      # rd ← (imm[15:7] << 7)
AUIPC x1, 0x1000    # rd ← PC + (imm[15:7] << 7)
```

### System Instructions (1 total)

```assembly
ECALL 0x002         # trap to service number [15:6]
```

### Pseudo-Instructions (12 total)

```assembly
LI16 x1, 0x1234     # Load 16-bit immediate
LA x1, data_label   # Load address
PUSH x1             # Push register to stack
POP x1              # Pop from stack to register
CALL function       # Call function
RET                 # Return from function
INC x1              # Increment register
DEC x1              # Decrement register
NEG x1              # Negate register (two's complement)
NOT x1              # Bitwise NOT
CLR x1              # Clear register to zero
NOP                 # No operation
```

## 🎯 Z16 Register Set

The extension supports all 8 Z16 registers with their aliases:

| Register | Alias | Purpose              |
| -------- | ----- | -------------------- |
| x0       | t0    | Temporary register 0 |
| x1       | ra    | Return address       |
| x2       | sp    | Stack pointer        |
| x3       | s0    | Saved register 0     |
| x4       | s1    | Saved register 1     |
| x5       | t1    | Temporary register 1 |
| x6       | a0    | Argument register 0  |
| x7       | a1    | Argument register 1  |

## 📁 File Extensions

The extension automatically activates for files with these extensions:

- `.z16` - Z16 assembly files
- `.s` - Generic assembly files
- `.asm` - Assembly files

## 🎯 Usage Examples

### Basic Program Structure

```assembly
.equ BUFFER_ADDR, 0xF000

.text
.org 0x0000
j main

.org 0x0020
main:
    li x1, 42               # Load immediate value
    call process_data       # Call subroutine
    j end                   # Jump to end

process_data:
    push x1                 # Save register
    addi x1, 10             # Add 10 to x1
    pop x1                  # Restore register
    ret                     # Return

end:
    ecall 10                # Exit program

.data
buffer: .space 64
message: .string "Hello, Z16!"
```

### Autocomplete Examples

- Type `ad` → suggests `ADD`, `ADDI`
- Type `x` → suggests all registers (`x0`, `x1`, etc.)
- Type `.` → suggests all directives (`.text`, `.data`, etc.)
- Type `main` → suggests existing labels

## ⚙️ Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Z16 Assembly"
4. Click Install

### Manual Installation

1. Download the `.vsix` file from releases
2. Run: `code --install-extension z16-assembly-x.x.x.vsix`
3. Reload VS Code
4. Create a `.z16` file and start coding!

## 🛠️ Development

### Building from Source

```bash
# Install dependencies
npm install -g @vscode/vsce

# Clone repository
git clone <repository>
cd z16-extension

# Package extension
vsce package

# Install locally
code --install-extension z16-assembly-x.x.x.vsix
```

### Testing

- Press `F5` to launch Extension Development Host
- Create test `.z16` files to verify functionality
- Use `Developer: Reload Window` to test changes

## 🔧 Configuration

The extension works out of the box with sensible defaults. Language configuration includes:

- **Line comments**: `#`
- **Auto-closing pairs**: `()`, `""`, `''`
- **Bracket matching**: `()`
- **Smart indentation** for labels and instructions

### Custom Settings

You can customize the extension behavior in VS Code settings:

```json
{
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "editor.wordWrap": "off",
  "editor.rulers": [80],
  "files.associations": {
    "*.z16": "z16"
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**Extension not activating:**

- Ensure file has `.z16`, `.s`, or `.asm` extension
- Check VS Code output panel for errors
- Try reloading the window (Ctrl+Shift+P → "Developer: Reload Window")

**Autocomplete not working:**

- Trigger manually with `Ctrl+Space`
- Check if the file is recognized as Z16 assembly (bottom right corner)
- Ensure cursor is in valid position (not in comments)

**Go to Definition not working:**

- Ensure label is defined in the same file
- Check that label name matches exactly (case-sensitive)
- Try Find All References (Shift+F12) as alternative

### Performance

- The extension is optimized for files up to 10,000 lines
- Label detection runs on document change with 500ms debounce
- Syntax highlighting is handled by VS Code's TextMate engine

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=abdallahmostafa.z16-assembly)
- [Repo](https://github.com/AbdallahMostafaIbrahim/z16-assembler/tree/main/extension)
- [Z16 Architecture Documentation](https://github.com/shalan/z16)

## 🙏 Acknowledgments

- Thank you claude, you are awesome!
