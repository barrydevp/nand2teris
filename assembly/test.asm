// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.

(MAIN)
@cur
M=-1
(MAIN_LOOP)
@KBD
D=M

@IF_KBD_EQ
D;JEQ
@cur
M=1
@END_IF_KBD_EQ
0;JMP
(IF_KBD_EQ)
@cur
M=0
(END_IF_KBD_EQ)
@cur
D=M
@last
D=D-M
@MAIN_LOOP
D;JEQ

@CLEAR
D;JLT

(FILL)
@last
M=1
@draw_val
M=-1
@FILL_RET
D=A
@ret
M=D
@DRAW
0;JMP
(FILL_RET)
@MAIN_LOOP
0;JMP

(CLEAR)
@last
M=0
@draw_val
M=0
@CLEAR_RET
D=A
@ret
M=D
@DRAW
0;JMP
(CLEAR_RET)
@MAIN_LOOP
0;JMP

// DRAW function
(DRAW)
@SCREEN
D=A
@i
M=D
(DRAW_LOOP)
@24576
D=A
@i
D=M-D
@DRAW_LOOP_END
D;JGE

@draw_val
D=M
@i
A=M
M=D

@i
M=M+1
@DRAW_LOOP
0;JMP
(DRAW_LOOP_END)
@ret
A=M
0;JMP

