.equ STACK_TOP, 0xEFFE
.equ TILE_MAP_BUFFER_ADDR, 0xF000
.equ TILE_DEFINITIONS_ADDR, 0xF200
.equ COLOR_PALLETE_ADDR, 0xFA00

.text
.org 0x0000
j main
.org 0x0020
main:
    li16 sp, STACK_TOP # Initialize stack pointer
    
    la a0, palette_data # Load address of palette_data
    li a1, 16          # Set size to 16 bytes
    li16 s1, COLOR_PALLETE_ADDR

    ecall 9 # Memory dump syscall
    call load_data # Load color palette data

    li16 a0, COLOR_PALLETE_ADDR # Load address of color palette
    li a1, 16          # Set size to 16 bytes
    ecall 9 # Memory dump syscall

    li16 a0, tile0_data # Load address of tile0_data
    li16 a1, 128          # Set size to 128 bytes
    li16 s1, TILE_DEFINITIONS_ADDR
    ecall 9 # Memory dump syscall
    call load_data # Load tile definitions data

    li16 a0, TILE_DEFINITIONS_ADDR # Load address of tile definitions
    li16 a1, 128          # Set size to 128 bytes
    ecall 9 # Memory dump syscall

    
    # Exit with success code
    CLR a0             # Exit code 0
    ECALL 10       # Exit program syscall

load_data:
  # First: save return address and s1
  addi   sp, -8       # make room on stack
  sw     ra, 4(sp)        # save ra (x1)
  sw     s1, 0(sp)        # save s1 (x4), which holds dest ptr

  li     t0, 0            # counter = 0

  loop:
      beq    t0, a1, end     # if counter == size, done
      lbu    t1, 0(a0)        # load byte from [a0]
      sb     t1, 0(s1)        # store byte to [s1]
      addi   a0, 1        # a0++  (source ptr++)
      addi   s1, 1        # s1++  (dest ptr++)
      addi   t0, 1        # counter++
      j      loop

  end:
      # End: restore s1 and ra
      lw     s1, 0(sp)
      lw     ra, 4(sp)
      addi   sp, 8
      ret

.data
hello_msg: .string "Hello, enter a number:"
hi_msg: .string "You entered: "

input_string: .space 32


palette_data:
    .byte 0xFF,     0xDA,      0xDA,      0xB6,      0xB6,      0x92,      0x91,      0x6D
    .byte 0x6D,     0x49,      0x49,      0x24,      0x24,      0x00,      0x00,      0x00

tile0_data:
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123
    .word 0xCDEF,      0x89AB,      0x4567,      0x0123,      0xCDEF,      0x89AB,      0x4567,      0x0123