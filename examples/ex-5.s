.text
.org 0x0000
j main
.org 0x0020
main:
  la t0, hello_world
  lb t1, 0(t0)
  lb t1, 1(t0)
  lb t1, 2(t0)
  lb t1, 3(t0)
  ecall 10
data:


hello_world:
.byte 5, 6, 7, 8

