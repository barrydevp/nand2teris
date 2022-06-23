// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(MAIN_LOOP)
    // main loop check if KBD = 0 (no key pressed)
    @pixel
    M=0
    @KBD
    D=M
    @END_IF_KBD_PRESSED
    D;JEQ 
    // if (KBD != 0)
    @pixel
    M=-1
(END_IF_KBD_PRESSED)

    // render to screen
    @8191
    D=A
    @SCREEN
    D=D+A
    @addr
    M=D

(RENDER) // render pixel variable to screen
    @pixel
    D=M
    @addr
    A=M
    M=D

    // while(addr >= screen) continue loop
    @SCREEN
    D=A
    @addr
    M=M-1
    D=M-D
    @RENDER
    D;JGE

    // back to main loop
    @MAIN_LOOP
    0;JEQ

// unreachable code
(END)
    @END
    0;JEQ

