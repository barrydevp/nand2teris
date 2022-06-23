// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// Put your code here.

(MAIN)
    // reset R2
    @R2
    M=0
    
    // declare variables
    // and check if (R1 == 0 || R2 == 0) goto END
    @R0
    D=M;
    @END
    D;JEQ
    @n0
    M=D
    @R1
    D=M
    @END
    D;JEQ
    @n1
    M=D
    // set min, max (n0 = min, n1 = max)
    // if (n0 >= n1)
    @n0
    D=M-D;
    @N1_GTE_N2
    D;JGE
    // else (n0 < n1)
    @R1
    D=M
    @n0
    M=D
    @R0
    D=M
    @n1
    M=D
(N1_GTE_N2)

    // for(i = 0; i < n0; i++) { R2 = R2 + n1 }
    // init loop (i = 0)
    @i
    M=0

(LOOP_ADD)
    // if (i >= n0) goto END
    @n0
    D=M
    @i
    D=M-D
    @END
    D;JGE

    // loop content
    // R2 = R2 + n1
    @n1
    D=M
    @R2
    M=M+D

    // post loop (i++) and jump
    @i
    M=M+1
    @LOOP_ADD
    0;JEQ

(END)
    @END
    0;JEQ

