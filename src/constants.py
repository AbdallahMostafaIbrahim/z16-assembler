TRUE_INSTRUCTIONS = {
    # R-Type
    "add",
    "sub",
    "slt",
    "sltu",
    "sll",
    "srl",
    "sra",
    "or",
    "and",
    "xor",
    "mv",
    "jr",
    "jalr",
    # I-Type
    "addi",
    "slti",
    "sltui",
    "slli",
    "srli",
    "srai",
    "ori",
    "andi",
    "xori",
    "li",
    # B-Type
    "beq",
    "bne",
    "bz",
    "bnz",
    "blt",
    "bge",
    "bltu",
    "bgeu",
    # S-Type
    "sb",
    "sw",
    # L-Type
    "lb",
    "lw",
    "lbu",
    # J-Type
    "j",
    "jal",
    # U-Type
    "lui",
    "auipc",
    # SYS-Type
    "ecall",
}

# Pseudo-instructions sizes in bytes
PSEUDO_INSTRUCTIONS = {
    "li16": 4,
    "la": 4,
    "push": 4,
    "pop": 4,
    "call": 2,
    "ret": 2,
    "inc": 2,
    "dec": 2,
    "neg": 4,
    "not": 2,
    "clr": 2,
    "nop": 2,
}
DEFAULT_SYMBOLS = {
    "RESET_VECTOR": 0x0000,
    "INT_VECTORS": 0x0000,  # Interrupt vector table start
    "CODE_START": 0x0020,  # Default code start
    "MMIO_BASE": 0xF000,  # Memory-mapped I/O base
    "MMIO_SIZE": 0x1000,  # MMIO region size
    "STACK_TOP": 0xEFFE,  # Default stack top
    "MEM_SIZE": 0x10000,  # Total memory size (64KB)
}
