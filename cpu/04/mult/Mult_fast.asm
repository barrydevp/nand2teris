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

    // init loop
    @l
    M=D // set l = n1
    @i
    M=1

(LOOP_ADD)
    // if (i >= n0) goto END
    @n0
    D=M
    @i
    D=M-D
    @END
    D;JGT

    // loop content
    // if current bit cursor in n0 is 1 => add l to sum, else jump to POST_LOOP
    @n0
    D=M
    @i
    D=D&M
    @POST_LOOP
    D;JEQ
    // current bit in n0 is 1, so add last to sum(R2)
    @l
    D=M
    @R2
    M=M+D

(POST_LOOP)
    // post loop
    // calulate last = last + last
    @l
    D=M
    M=D+M
    // (i*=2) and jump to continue loop
    @i
    D=M
    M=D+M
    @LOOP_ADD
    0;JEQ

(END)
    @END
    0;JEQ

