const vscode = require("vscode");

function activate(context) {
  console.log("Z16 Assembly extension is now active!");

  // Define instruction data
  const instructions = {
    // R-Type Instructions
    add: {
      description: "Add: add rd, rs2",
      detail: "rd ← rd + rs2",
      syntax: "add ${1:rd}, ${2:rs2}",
    },
    sub: {
      description: "Subtract: sub rd, rs2",
      detail: "rd ← rd - rs2",
      syntax: "sub ${1:rd}, ${2:rs2}",
    },
    slt: {
      description: "Set less than: slt rd, rs2",
      detail: "rd ← (rd < rs2) ? 1 : 0",
      syntax: "slt ${1:rd}, ${2:rs2}",
    },
    sltu: {
      description: "Set less than unsigned: sltu rd, rs2",
      detail: "rd ← (unsigned rd < unsigned rs2) ? 1 : 0",
      syntax: "sltu ${1:rd}, ${2:rs2}",
    },
    sll: {
      description: "Shift left logical: sll rd, rs2",
      detail: "rd ← rd << (rs2 & 0xF)",
      syntax: "sll ${1:rd}, ${2:rs2}",
    },
    srl: {
      description: "Shift right logical: srl rd, rs2",
      detail: "rd ← rd >> (rs2 & 0xF) (logical)",
      syntax: "srl ${1:rd}, ${2:rs2}",
    },
    sra: {
      description: "Shift right arithmetic: sra rd, rs2",
      detail: "rd ← rd >> (rs2 & 0xF) (arithmetic)",
      syntax: "sra ${1:rd}, ${2:rs2}",
    },
    or: {
      description: "Bitwise OR: or rd, rs2",
      detail: "rd ← rd | rs2",
      syntax: "or ${1:rd}, ${2:rs2}",
    },
    and: {
      description: "Bitwise AND: and rd, rs2",
      detail: "rd ← rd & rs2",
      syntax: "and ${1:rd}, ${2:rs2}",
    },
    xor: {
      description: "Bitwise XOR: xor rd, rs2",
      detail: "rd ← rd ^ rs2",
      syntax: "xor ${1:rd}, ${2:rs2}",
    },
    mv: {
      description: "Move: mv rd, rs2",
      detail: "rd ← rs2",
      syntax: "mv ${1:rd}, ${2:rs2}",
    },
    jr: {
      description: "Jump register: jr rd",
      detail: "PC ← rd",
      syntax: "jr ${1:rd}",
    },
    jalr: {
      description: "Jump and link register: jalr rd, rs2",
      detail: "rd ← PC + 2; PC ← rs2",
      syntax: "jalr ${1:rd}, ${2:rs2}",
    },

    // I-Type Instructions
    addi: {
      description: "Add immediate: addi rd, imm",
      detail: "rd ← rd + sext(imm7)",
      syntax: "addi ${1:rd}, ${2:imm}",
    },
    slti: {
      description: "Set less than immediate: slti rd, imm",
      detail: "rd ← (rd < sext(imm7)) ? 1 : 0",
      syntax: "slti ${1:rd}, ${2:imm}",
    },
    sltui: {
      description: "Set less than unsigned immediate: sltui rd, imm",
      detail: "rd ← (unsigned rd < unsigned sext(imm7)) ? 1 : 0",
      syntax: "sltui ${1:rd}, ${2:imm}",
    },
    slli: {
      description: "Shift left logical immediate: slli rd, imm",
      detail: "rd ← rd << imm[3:0]",
      syntax: "slli ${1:rd}, ${2:imm}",
    },
    srli: {
      description: "Shift right logical immediate: srli rd, imm",
      detail: "rd ← rd >> imm[3:0] (logical)",
      syntax: "srli ${1:rd}, ${2:imm}",
    },
    srai: {
      description: "Shift right arithmetic immediate: srai rd, imm",
      detail: "rd ← rd >> imm[3:0] (arithmetic)",
      syntax: "srai ${1:rd}, ${2:imm}",
    },
    ori: {
      description: "OR immediate: ori rd, imm",
      detail: "rd ← rd | sext(imm7)",
      syntax: "ori ${1:rd}, ${2:imm}",
    },
    andi: {
      description: "AND immediate: andi rd, imm",
      detail: "rd ← rd & sext(imm7)",
      syntax: "andi ${1:rd}, ${2:imm}",
    },
    xori: {
      description: "XOR immediate: xori rd, imm",
      detail: "rd ← rd ^ sext(imm7)",
      syntax: "xori ${1:rd}, ${2:imm}",
    },
    li: {
      description: "Load immediate: li rd, imm",
      detail: "rd ← sext(imm7)",
      syntax: "li ${1:rd}, ${2:imm}",
    },

    // B-Type Instructions
    beq: {
      description: "Branch if equal: beq rs1, rs2, label",
      detail: "if rs1 == rs2: PC ← PC + offset",
      syntax: "beq ${1:rs1}, ${2:rs2}, ${3:label}",
    },
    bne: {
      description: "Branch if not equal: bne rs1, rs2, label",
      detail: "if rs1 != rs2: PC ← PC + offset",
      syntax: "bne ${1:rs1}, ${2:rs2}, ${3:label}",
    },
    bz: {
      description: "Branch if zero: bz rs1, label",
      detail: "if rs1 == 0: PC ← PC + offset",
      syntax: "bz ${1:rs1}, ${2:label}",
    },
    bnz: {
      description: "Branch if not zero: bnz rs1, label",
      detail: "if rs1 != 0: PC ← PC + offset",
      syntax: "bnz ${1:rs1}, ${2:label}",
    },
    blt: {
      description: "Branch if less than: blt rs1, rs2, label",
      detail: "if rs1 < rs2: PC ← PC + offset (signed)",
      syntax: "blt ${1:rs1}, ${2:rs2}, ${3:label}",
    },
    bge: {
      description: "Branch if greater or equal: bge rs1, rs2, label",
      detail: "if rs1 >= rs2: PC ← PC + offset (signed)",
      syntax: "bge ${1:rs1}, ${2:rs2}, ${3:label}",
    },
    bltu: {
      description: "Branch if less than unsigned: bltu rs1, rs2, label",
      detail: "if rs1 < rs2: PC ← PC + offset (unsigned)",
      syntax: "bltu ${1:rs1}, ${2:rs2}, ${3:label}",
    },
    bgeu: {
      description: "Branch if greater or equal unsigned: bgeu rs1, rs2, label",
      detail: "if rs1 >= rs2: PC ← PC + offset (unsigned)",
      syntax: "bgeu ${1:rs1}, ${2:rs2}, ${3:label}",
    },

    // S-Type Instructions
    sb: {
      description: "Store byte: sb rs1, offset(rs2)",
      detail: "mem[rs1 + sext(imm)] ← rs2[7:0]",
      syntax: "sb ${1:rs1}, ${2:offset}(${3:rs2})",
    },
    sw: {
      description: "Store word: sw rs1, offset(rs2)",
      detail: "mem[rs1 + sext(imm)] ← rs2[15:0]",
      syntax: "sw ${1:rs1}, ${2:offset}(${3:rs2})",
    },

    // L-Type Instructions
    lb: {
      description: "Load byte: lb rd, offset(rs2)",
      detail: "rd ← sext(mem[rs2 + sext(imm)][7:0])",
      syntax: "lb ${1:rd}, ${2:offset}(${3:rs2})",
    },
    lw: {
      description: "Load word: lw rd, offset(rs2)",
      detail: "rd ← mem[rs2 + sext(imm)][15:0]",
      syntax: "lw ${1:rd}, ${2:offset}(${3:rs2})",
    },
    lbu: {
      description: "Load byte unsigned: lbu rd, offset(rs2)",
      detail: "rd ← zext(mem[rs2 + sext(imm)][7:0])",
      syntax: "lbu ${1:rd}, ${2:offset}(${3:rs2})",
    },

    // J-Type Instructions
    j: {
      description: "Jump: j label",
      detail: "PC ← PC + offset",
      syntax: "j ${1:label}",
    },
    jal: {
      description: "Jump and link: jal rd, function",
      detail: "rd ← PC + 2; PC ← PC + offset",
      syntax: "jal ${1:rd}, ${2:function}",
    },

    // U-Type Instructions
    lui: {
      description: "Load upper immediate: lui rd, imm",
      detail: "rd ← (imm[15:7] << 7)",
      syntax: "lui ${1:rd}, ${2:imm}",
    },
    auipc: {
      description: "Add upper immediate to PC: auipc rd, imm",
      detail: "rd ← PC + (imm[15:7] << 7)",
      syntax: "auipc ${1:rd}, ${2:imm}",
    },

    // SYS-Type Instructions
    ecall: {
      description: "Environment call: ecall service",
      detail: "trap to service number [15:6]",
      syntax: "ecall ${1:service}",
    },

    // Pseudo-Instructions
    li16: {
      description: "Load 16-bit immediate: li16 rd, imm",
      detail: "Expands to: LUI rd, imm[15:7]; ORI rd, imm[6:0]",
      syntax: "li16 ${1:rd}, ${2:imm}",
    },
    la: {
      description: "Load address: la rd, label",
      detail:
        "Expands to: AUIPC rd, ((label-PC)>>7); ADDI rd, ((label-PC)&0x7F)",
      syntax: "la ${1:rd}, ${2:label}",
    },
    push: {
      description: "Push register to stack: push rs",
      detail: "Expands to: ADDI sp, -2; SW rs, 0(sp)",
      syntax: "push ${1:rs}",
    },
    pop: {
      description: "Pop from stack to register: pop rd",
      detail: "Expands to: LW rd, 0(sp); ADDI sp, 2",
      syntax: "pop ${1:rd}",
    },
    call: {
      description: "Call function: call function",
      detail: "Expands to: JAL ra, offset",
      syntax: "call ${1:function}",
    },
    ret: {
      description: "Return from function: ret",
      detail: "Expands to: JR ra",
      syntax: "ret",
    },
    inc: {
      description: "Increment register: inc rd",
      detail: "Expands to: ADDI rd, 1",
      syntax: "inc ${1:rd}",
    },
    dec: {
      description: "Decrement register: dec rd",
      detail: "Expands to: ADDI rd, -1",
      syntax: "dec ${1:rd}",
    },
    neg: {
      description: "Negate register: neg rd",
      detail: "Expands to: XORI rd, -1; ADDI rd, 1",
      syntax: "neg ${1:rd}",
    },
    not: {
      description: "Bitwise NOT: not rd",
      detail: "Expands to: XORI rd, -1",
      syntax: "not ${1:rd}",
    },
    clr: {
      description: "Clear register: clr rd",
      detail: "Expands to: XOR rd, rd",
      syntax: "clr ${1:rd}",
    },
    nop: {
      description: "No operation: nop",
      detail: "Expands to: ADD x0, x0",
      syntax: "nop",
    },
  };

  // Define registers (Z16 specific)
  const registers = [
    // Register aliases (primary names)
    "t0", // x0
    "ra", // x1
    "sp", // x2
    "s0", // x3
    "s1", // x4
    "t1", // x5
    "a0", // x6
    "a1", // x7
    // Direct register names
    "x0", // same as t0
    "x1", // same as ra
    "x2", // same as sp
    "x3", // same as s0
    "x4", // same as s1
    "x5", // same as t1
    "x6", // same as a0
    "x7", // same as a1
  ];

  // Define directives
  const directives = [
    // Section directives
    { name: "text", description: "Text section directive", syntax: ".text" },
    { name: "data", description: "Data section directive", syntax: ".data" },
    {
      name: "inter",
      description: "Interrupt section directive",
      syntax: ".inter",
    },
    { name: "bss", description: "BSS section directive", syntax: ".bss" },
    {
      name: "mmio",
      description: "Memory-mapped I/O section directive",
      syntax: ".mmio",
    },

    // Data directives
    {
      name: "byte",
      description: "Byte directive: .byte value",
      syntax: ".byte ${1:value}",
    },
    {
      name: "word",
      description: "Word directive: .word value",
      syntax: ".word ${1:value}",
    },
    {
      name: "string",
      description: 'String directive: .string "text"',
      syntax: '.string "${1:text}"',
    },
    {
      name: "ascii",
      description: 'ASCII directive: .ascii "text"',
      syntax: '.ascii "${1:text}"',
    },
    {
      name: "space",
      description: "Space directive: .space size",
      syntax: ".space ${1:size}",
    },
    {
      name: "fill",
      description: "Fill directive: .fill count, size, value",
      syntax: ".fill ${1:count}, ${2:size}, ${3:value}",
    },

    // Other directives
    {
      name: "org",
      description: "Origin directive: .org address",
      syntax: ".org ${1:address}",
    },
    {
      name: "equ",
      description: "Equate directive: .equ symbol, value",
      syntax: ".equ ${1:symbol}, ${2:value}",
    },
    {
      name: "set",
      description: "Set directive: .set symbol, value",
      syntax: ".set ${1:symbol}, ${2:value}",
    },
  ];

  // Define default constants for Z16 assembler
  const defaultConstants = {
    __WORD_SIZE__: {
      value: "2",
      description: "Word size in bytes",
    },
    __DATA_SIZE__: {
      value: "16",
      description: "Data size in bits",
    },
    __ADDR_SIZE__: {
      value: "16",
      description: "Address size in bits",
    },
    RESET_VECTOR: {
      value: "0x0000",
      description: "Reset vector address",
    },
    INT_VECTORS: {
      value: "0x0000",
      description: "Interrupt vector table start",
    },
    CODE_START: {
      value: "0x0020",
      description: "Default code start address",
    },
    MMIO_BASE: {
      value: "0xF000",
      description: "Memory-mapped I/O base address",
    },
    MMIO_SIZE: {
      value: "0x1000",
      description: "MMIO region size",
    },
    STACK_TOP: {
      value: "0xEFFE",
      description: "Default stack top address",
    },
    MEM_SIZE: {
      value: "0x10000",
      description: "Total memory size (64KB)",
    },
  };

  // Function to extract symbols defined with .equ and .set directives
  function extractSymbols(document) {
    const text = document.getText();
    const symbols = new Map();

    // Match .equ and .set directives
    const symbolMatches = text.matchAll(
      /^\s*\.(?:equ|set)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*(.+)$/gim
    );

    for (const match of symbolMatches) {
      const symbolName = match[1];
      const symbolValue = match[2].trim();
      symbols.set(symbolName, {
        value: symbolValue,
        type: match[0].toLowerCase().includes(".equ") ? "equ" : "set",
      });
    }

    return symbols;
  }

  // Register completion provider
  const completionProvider = vscode.languages.registerCompletionItemProvider(
    "z16",
    {
      provideCompletionItems(document, position, token, context) {
        const completions = [];

        // Get the line text up to the cursor position
        const linePrefix = document
          .lineAt(position)
          .text.substring(0, position.character);
        const isAfterDot =
          linePrefix.endsWith(".") || /\.\w*$/.test(linePrefix);

        // Add instruction completions (only if not after a dot)
        if (!isAfterDot) {
          for (const [name, info] of Object.entries(instructions)) {
            const completion = new vscode.CompletionItem(
              name,
              vscode.CompletionItemKind.Function
            );
            completion.detail = info.detail;
            completion.documentation = new vscode.MarkdownString(
              info.description
            );
            completion.insertText = new vscode.SnippetString(info.syntax);
            completion.sortText = "1" + name; // Priority for instructions
            completions.push(completion);
          }
        }

        // Add register completions (only if not after a dot)
        if (!isAfterDot) {
          for (const reg of registers) {
            const completion = new vscode.CompletionItem(
              reg,
              vscode.CompletionItemKind.Variable
            );
            completion.detail = `Register ${reg}`;
            completion.documentation = new vscode.MarkdownString(
              `Z16 register: \`${reg}\``
            );
            completion.sortText = "2" + reg; // Lower priority than instructions
            completions.push(completion);
          }
        }

        // Add directive completions (only show when after a dot or when explicitly triggered)
        if (isAfterDot || context.triggerCharacter === ".") {
          for (const dir of directives) {
            const completion = new vscode.CompletionItem(
              dir.name,
              vscode.CompletionItemKind.Keyword
            );
            completion.detail = dir.description;
            // Remove the leading dot from the syntax for insertion
            const syntaxWithoutDot = dir.syntax.substring(1); // Remove the first character (.)
            completion.insertText = new vscode.SnippetString(syntaxWithoutDot);
            completion.filterText = dir.name; // What to match against
            completion.sortText = "0" + dir.name; // Highest priority for directives
            completions.push(completion);
          }
        }

        // Add label completions (only if not after a dot)
        if (!isAfterDot) {
          const text = document.getText();
          const labelMatches = text.matchAll(/^\s*([a-zA-Z_][a-zA-Z0-9_]*):/gm);
          for (const match of labelMatches) {
            const labelName = match[1];
            const completion = new vscode.CompletionItem(
              labelName,
              vscode.CompletionItemKind.Reference
            );
            completion.detail = "Label";
            completion.documentation = new vscode.MarkdownString(
              `Jump target: \`${labelName}\``
            );
            completion.sortText = "3" + labelName;
            completions.push(completion);
          }
        }

        // Add symbol completions (only if not after a dot)
        if (!isAfterDot) {
          const symbols = extractSymbols(document);
          for (const [symbolName, symbolInfo] of symbols) {
            const completion = new vscode.CompletionItem(
              symbolName,
              vscode.CompletionItemKind.Constant
            );
            completion.detail = `Symbol (${symbolInfo.type.toUpperCase()})`;
            completion.documentation = new vscode.MarkdownString(
              `Symbol defined with \`.${symbolInfo.type}\`\n\nValue: \`${symbolInfo.value}\``
            );
            completion.sortText = "4" + symbolName;
            completions.push(completion);
          }

          // Add default constants
          for (const [constantName, constantInfo] of Object.entries(
            defaultConstants
          )) {
            const completion = new vscode.CompletionItem(
              constantName,
              vscode.CompletionItemKind.Constant
            );
            completion.detail = `Default Constant`;
            completion.documentation = new vscode.MarkdownString(
              `**${constantInfo.description}**\n\nValue: \`${constantInfo.value}\``
            );
            completion.sortText = "4" + constantName;
            completions.push(completion);
          }
        }

        return completions;
      },
    },
    "." // Trigger completion when user types a dot
  );

  // Register hover provider for instruction documentation
  const hoverProvider = vscode.languages.registerHoverProvider("z16", {
    provideHover(document, position, token) {
      const range = document.getWordRangeAtPosition(position);
      if (!range) return;

      const word = document.getText(range).toLowerCase();

      if (instructions[word]) {
        const info = instructions[word];
        return new vscode.Hover(
          new vscode.MarkdownString(`**${info.description}**\n\n${info.detail}`)
        );
      }

      // Check if it's a register with alias information
      const registerAliases = {
        t0: "x0 (temporary register 0)",
        x0: "t0 (temporary register 0)",
        ra: "x1 (return address)",
        x1: "ra (return address)",
        sp: "x2 (stack pointer)",
        x2: "sp (stack pointer)",
        s0: "x3 (saved register 0)",
        x3: "s0 (saved register 0)",
        s1: "x4 (saved register 1)",
        x4: "s1 (saved register 1)",
        t1: "x5 (temporary register 1)",
        x5: "t1 (temporary register 1)",
        a0: "x6 (argument register 0)",
        x6: "a0 (argument register 0)",
        a1: "x7 (argument register 1)",
        x7: "a1 (argument register 1)",
      };

      if (registerAliases[word]) {
        return new vscode.Hover(
          new vscode.MarkdownString(
            `**Register:** \`${word}\`\n\nAlias: ${registerAliases[word]}`
          )
        );
      }

      // Check if it's a symbol defined with .equ or .set
      const symbols = extractSymbols(document);
      if (symbols.has(word)) {
        const symbolInfo = symbols.get(word);
        return new vscode.Hover(
          new vscode.MarkdownString(
            `**Symbol:** \`${word}\`\n\nDefined with: \`.${symbolInfo.type}\`\n\nValue: \`${symbolInfo.value}\``
          )
        );
      }

      // Check if it's a default constant
      if (defaultConstants[word]) {
        const constantInfo = defaultConstants[word];
        return new vscode.Hover(
          new vscode.MarkdownString(
            `**Default Constant:** \`${word}\`\n\n${constantInfo.description}\n\nValue: \`${constantInfo.value}\``
          )
        );
      }
    },
  });

  // Create diagnostic collection for errors
  const diagnosticCollection =
    vscode.languages.createDiagnosticCollection("z16");

  // Function to validate document and check for duplicate labels
  function validateDocument(document) {
    if (document.languageId !== "z16") {
      return;
    }

    const diagnostics = [];
    const labelMap = new Map(); // Map to track label names and their locations
    const text = document.getText();

    // Find all labels with their line numbers
    const lines = text.split("\n");
    for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
      const line = lines[lineIndex];
      const labelMatch = line.match(/^\s*([a-zA-Z_][a-zA-Z0-9_]*):/);

      if (labelMatch) {
        const labelName = labelMatch[1];
        const labelStart = line.indexOf(labelName);

        if (labelMap.has(labelName)) {
          // Duplicate label found!
          const firstOccurrence = labelMap.get(labelName);

          // Create error for current (duplicate) label
          const range = new vscode.Range(
            lineIndex,
            labelStart,
            lineIndex,
            labelStart + labelName.length
          );

          const diagnostic = new vscode.Diagnostic(
            range,
            `Duplicate label '${labelName}'. First defined at line ${
              firstOccurrence.line + 1
            }.`,
            vscode.DiagnosticSeverity.Error
          );
          diagnostic.code = "duplicate-label";
          diagnostic.source = "z16-assembly";
          diagnostics.push(diagnostic);

          // Also mark the first occurrence as an error
          const firstRange = new vscode.Range(
            firstOccurrence.line,
            firstOccurrence.start,
            firstOccurrence.line,
            firstOccurrence.start + labelName.length
          );

          const firstDiagnostic = new vscode.Diagnostic(
            firstRange,
            `Duplicate label '${labelName}'. Also defined at line ${
              lineIndex + 1
            }.`,
            vscode.DiagnosticSeverity.Error
          );
          firstDiagnostic.code = "duplicate-label";
          firstDiagnostic.source = "z16-assembly";
          diagnostics.push(firstDiagnostic);
        } else {
          // First occurrence of this label
          labelMap.set(labelName, {
            line: lineIndex,
            start: labelStart,
          });
        }
      }
    }

    // Set diagnostics for this document
    diagnosticCollection.set(document.uri, diagnostics);
  }

  // Validate document on open and save
  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument(validateDocument),
    vscode.workspace.onDidSaveTextDocument(validateDocument),
    vscode.workspace.onDidChangeTextDocument((event) => {
      // Validate on content changes with a slight delay to avoid too frequent updates
      setTimeout(() => validateDocument(event.document), 500);
    })
  );

  // Validate all currently open documents
  vscode.workspace.textDocuments.forEach(validateDocument);

  // Register definition provider for "Go to Definition" on labels
  const definitionProvider = vscode.languages.registerDefinitionProvider(
    "z16",
    {
      provideDefinition(document, position, token) {
        const range = document.getWordRangeAtPosition(
          position,
          /[a-zA-Z_][a-zA-Z0-9_]*/
        );
        if (!range) {
          return;
        }

        const word = document.getText(range);
        const text = document.getText();
        const lines = text.split("\n");

        // Look for the label definition (word followed by colon)
        for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
          const line = lines[lineIndex];
          const labelMatch = line.match(new RegExp(`^\\s*(${word}):`));

          if (labelMatch) {
            const labelStart = line.indexOf(word);
            const labelPosition = new vscode.Position(lineIndex, labelStart);
            const labelRange = new vscode.Range(
              labelPosition,
              new vscode.Position(lineIndex, labelStart + word.length)
            );

            return new vscode.Location(document.uri, labelRange);
          }
        }

        // Look for symbol definition with .equ or .set
        for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
          const line = lines[lineIndex];
          const symbolMatch = line.match(
            new RegExp(`^\\s*\\.(?:equ|set)\\s+(${word})\\s*,`, "i")
          );

          if (symbolMatch) {
            const symbolStart = line.indexOf(word);
            const symbolPosition = new vscode.Position(lineIndex, symbolStart);
            const symbolRange = new vscode.Range(
              symbolPosition,
              new vscode.Position(lineIndex, symbolStart + word.length)
            );

            return new vscode.Location(document.uri, symbolRange);
          }
        }

        // If no definition found, return undefined
        return undefined;
      },
    }
  );

  // Register reference provider for "Find All References" on labels
  const referenceProvider = vscode.languages.registerReferenceProvider("z16", {
    provideReferences(document, position, context, token) {
      const range = document.getWordRangeAtPosition(
        position,
        /[a-zA-Z_][a-zA-Z0-9_]*/
      );
      if (!range) {
        return [];
      }

      const word = document.getText(range);
      const text = document.getText();
      const lines = text.split("\n");
      const references = [];

      // Find all references to this label
      for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
        const line = lines[lineIndex];

        // Check for label definition (if context.includeDeclaration is true)
        if (context.includeDeclaration) {
          const labelDefMatch = line.match(new RegExp(`^\\s*(${word}):`));
          if (labelDefMatch) {
            const labelStart = line.indexOf(word);
            const refRange = new vscode.Range(
              lineIndex,
              labelStart,
              lineIndex,
              labelStart + word.length
            );
            references.push(new vscode.Location(document.uri, refRange));
          }

          // Check for symbol definition with .equ or .set
          const symbolDefMatch = line.match(
            new RegExp(`^\\s*\\.(?:equ|set)\\s+(${word})\\s*,`, "i")
          );
          if (symbolDefMatch) {
            const symbolStart = line.indexOf(word);
            const refRange = new vscode.Range(
              lineIndex,
              symbolStart,
              lineIndex,
              symbolStart + word.length
            );
            references.push(new vscode.Location(document.uri, refRange));
          }
        }

        // Check for label references in instructions (like j, beq, call, etc.)
        const instructionMatch = line.match(
          new RegExp(
            `\\b(j|jal|beq|bne|bz|bnz|blt|bge|bltu|bgeu|call)\\s+(?:[^,]+,\\s*)*\\b(${word})\\b`
          )
        );
        if (instructionMatch) {
          const refStart = line.lastIndexOf(word);
          const refRange = new vscode.Range(
            lineIndex,
            refStart,
            lineIndex,
            refStart + word.length
          );
          references.push(new vscode.Location(document.uri, refRange));
        }

        // Check for label references in la (load address) instructions
        const laMatch = line.match(
          new RegExp(`\\bla\\s+\\w+,\\s*(${word})\\b`)
        );
        if (laMatch) {
          const refStart = line.lastIndexOf(word);
          const refRange = new vscode.Range(
            lineIndex,
            refStart,
            lineIndex,
            refStart + word.length
          );
          references.push(new vscode.Location(document.uri, refRange));
        }

        // Check for symbol references in immediate operands (like li, addi, etc.)
        const immediateMatch = line.match(
          new RegExp(
            `\\b(?:li|addi|slti|sltui|ori|andi|xori|slli|srli|srai)\\s+\\w+,\\s*(${word})\\b`
          )
        );
        if (immediateMatch) {
          const refStart = line.lastIndexOf(word);
          const refRange = new vscode.Range(
            lineIndex,
            refStart,
            lineIndex,
            refStart + word.length
          );
          references.push(new vscode.Location(document.uri, refRange));
        }

        // Check for symbol references in other contexts (general symbol usage)
        const generalMatch = line.match(new RegExp(`\\b(${word})\\b`));
        if (
          generalMatch &&
          !line.match(/^\s*\.(?:equ|set)/) &&
          !line.match(/^\s*[a-zA-Z_][a-zA-Z0-9_]*:/)
        ) {
          // Only add if it's not already captured by other patterns
          const allMatches = [
            ...line.matchAll(new RegExp(`\\b(${word})\\b`, "g")),
          ];
          for (const match of allMatches) {
            const refStart = match.index;
            const refRange = new vscode.Range(
              lineIndex,
              refStart,
              lineIndex,
              refStart + word.length
            );
            // Check if this reference is not already added
            const isDuplicate = references.some(
              (ref) =>
                ref.range.start.line === lineIndex &&
                ref.range.start.character === refStart
            );
            if (!isDuplicate) {
              references.push(new vscode.Location(document.uri, refRange));
            }
          }
        }
      }

      // For default constants, we only look for references (no definitions to include)
      if (defaultConstants[word]) {
        for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
          const line = lines[lineIndex];

          // Check for constant references in immediate operands
          const immediateMatch = line.match(
            new RegExp(
              `\\b(?:li|addi|slti|sltui|ori|andi|xori|slli|srli|srai)\\s+\\w+,\\s*(${word})\\b`
            )
          );
          if (immediateMatch) {
            const refStart = line.lastIndexOf(word);
            const refRange = new vscode.Range(
              lineIndex,
              refStart,
              lineIndex,
              refStart + word.length
            );
            references.push(new vscode.Location(document.uri, refRange));
          }

          // Check for general constant usage
          const generalMatch = line.match(new RegExp(`\\b(${word})\\b`));
          if (
            generalMatch &&
            !line.match(/^\s*\.(?:equ|set)/) &&
            !line.match(/^\s*[a-zA-Z_][a-zA-Z0-9_]*:/)
          ) {
            const allMatches = [
              ...line.matchAll(new RegExp(`\\b(${word})\\b`, "g")),
            ];
            for (const match of allMatches) {
              const refStart = match.index;
              const refRange = new vscode.Range(
                lineIndex,
                refStart,
                lineIndex,
                refStart + word.length
              );
              // Check if this reference is not already added
              const isDuplicate = references.some(
                (ref) =>
                  ref.range.start.line === lineIndex &&
                  ref.range.start.character === refStart
              );
              if (!isDuplicate) {
                references.push(new vscode.Location(document.uri, refRange));
              }
            }
          }
        }
      }

      return references;
    },
  });

  context.subscriptions.push(
    completionProvider,
    hoverProvider,
    diagnosticCollection,
    definitionProvider,
    referenceProvider
  );
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
