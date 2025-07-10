.text
.org 0x0000
j main
.org 0x0020
main:
    li16 a0, 'w'
   loop:
    ecall 7
    j loop
    ECALL 10       # Exit program syscall

