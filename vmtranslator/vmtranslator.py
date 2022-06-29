import typing
import re
import sys
import os

class LexerError(Exception):
    def __init__(self, message, line, pos):
        super().__init__(f"{message}. {line}:{pos}")

class SyntaxError(LexerError):
    def __init__(self, message, line, pos):
        super().__init__(f"syntax error, {message}", line, pos)

# Constants for Command, Token
C_ARITHMETIC = 1
C_PUSH = 2
C_POP = 3
C_LABEL = 4
C_GOTO = 5
C_IF = 6
C_FUNCTION = 7
C_RETURN = 8
C_CALL = 9

TOK_ERROR = 1
TOK_CMD = 2
TOK_ARG = 3

EOF = None

class Token:
    def __init__(self, type: int, value: str, pos: int, line: int):
        self.type = type
        self.value = value
        self.pos = pos
        self.line = line

class Command:
    def __init__(self, type: int, tokens: typing.List[Token], line: int):
        self.type = type
        self.tokens = tokens
        self.line = line

    def __repr__(self) -> str:
        return f"{self.line}: {' '.join([tok.value for tok in self.tokens])}"

class Lexer:
    def __init__(self, input: str, lex_start):
        self.input = input
        self.input_len = len(input)
        self.lex_start = lex_start
        self._reset()

    def _reset(self):
        self.start = 0
        self.pos = 0
        self.line = 1
        self.tokens = []
        self.cmds = []

    def peek(self):
        if self.pos >= self.input_len:
            return EOF

        ch = self.input[self.pos]

        return ch

    # next char, increase pos
    def next(self):
        ch = self.peek()

        self.pos += 1
        if ch == '\n':
            self.line += 1

        return ch

    def back(self):
        self.pos -= 1
        ch = self.peek()

        if ch == '\n':
            self.line -= 1

    # consumes next char if its in valid set
    def accept(self, valid: str):
        ch = self.next()
        ret = False
        while ch and ch in valid:
            ch = self.next()
            ret = True
        self.back()

        return ret

    # consumes next char if its match regex
    def accept_r(self, regex):
        ch = self.next()
        ret = False
        while ch and re.match(regex, ch):
            ch = self.next()
            ret = True
        self.back()

        return ret

    def next_match(self, str: str):
        end = self.pos + len(str)
        if end > self.input_len:
            return False
        if str == self.input[self.pos:end]:
            self.pos = end
            return True
        return False

    def next_matchs(self, strs: typing.List[str]):
        for str in strs:
            if self.next_match(str):
                return True
        return False

    # skip current line
    def skip_line(self):
        self.pos += self.input[self.pos:].index('\n') + 1
        self.start = self.pos
        self.line += 1

    def ignore(self, inc_line = False):
        if inc_line:
            self.line += self.input[self.start:self.pos].count('\n')
        self.start = self.pos

    def _pop_tok(self):
        if len(self.tokens) > 0:
            return self.tokens.pop(0)

    def _push_tok(self, type):
        token = Token(type, self.input[self.start:self.pos], self.start, self.line)
        self.tokens.append(token)
        self.start = self.pos

        return token

    def _flush_tok(self):
        self.tokens = []

    def _push_cmd(self, type):
        self.cmds.append(Command(type, self.tokens, self.tokens[0].line))
        self._flush_tok()

    def _pop_cmd(self):
        if len(self.cmds) > 0:
            return self.cmds.pop(0)

    def run(self):
        self._reset()

        lex_fn = self.lex_start
        while lex_fn != None:
            lex_fn = lex_fn(self)

def lex_line(l: Lexer):
    # print(f"tokens[] = {l.tokens}")
    l._flush_tok()
    l.accept(" \t\n")
    l.ignore()
    ch = l.peek()

    if ch == EOF:
        return None

    if ch == '/':
        if l.next() != '/':
            raise SyntaxError("unknown one '/' character", l.line, l.pos)
        # reach comment -> ignore current line
        # print('reach comment, ignore line.')
        l.skip_line()
        return lex_line

    print(f"start with '{ch}' at {l.line}:{l.pos}")

    # arithmetic / logical
    if l.next_matchs(["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]):
        return lex_arithmetic

    # memory access
    if l.next_matchs(["push", "pop"]):
        return lex_memory_access

    # branching
    if l.next_matchs(["label", "goto", "if-goto"]):
        pass

    # function
    if l.next_matchs(["function", "call", "return"]):
        pass

    raise SyntaxError("unknown command", l.line, l.pos)

def ignore_blank(l: Lexer):
    l.accept(" \t")
    l.ignore()

def lex_end_line(l: Lexer):
    l.accept(" \t")
    ch = l.next()
    if ch == '/' and l.next() == '/':
        l.skip_line()
    elif ch != '\n':
        raise SyntaxError(f"unexpected end of line '{ch}'", l.line, l.pos)

    return lex_line

def lex_arithmetic(l: Lexer):
    print("-> arithmetic")

    l._push_tok(TOK_CMD)
    l._push_cmd(C_ARITHMETIC)
    return lex_end_line

def lex_memory_access(l: Lexer):
    print("-> memory access")

    cmd_tok = l._push_tok(TOK_CMD)
    ignore_blank(l)

    # get the segment
    l.accept_r(r"\w")
    l._push_tok(TOK_ARG)
    ignore_blank(l)

    # get the value
    l.accept_r(r"\d")
    l._push_tok(l)

    if cmd_tok.value == "push":
        l._push_cmd(C_PUSH)
    else:
        l._push_cmd(C_POP)

    return lex_end_line

R_COPY_VAL = "R13"
R_COPY_POINTER = "R14"

class AsmTempl:
    def __init__(self):
        pass
    
    @staticmethod
    def load_constant_to_d(constant):
        return f"""\
@{constant}
D=A
"""
    
    # this function will compute and set "to" register to (mem value from base + offset)
    # "to" = *base + offset
    @staticmethod
    def load_address(base, offset, to="A"):
        offset = int(offset)

        # load base
        __c = f"""\
@{base}
"""
        if offset == 0:
            return f"""\
{__c}\
{to}=M
"""

        offset_sign = "+"
        offset_val = offset
        if offset < 0:
            offset_sign = "-"
            offset_val = -offset 

        if offset_val == 1:
            return f"""\
{__c}\
{to}=M{offset_sign}{offset_val}
"""
        
        return f"""\
{__c}\
D=M
@{offset_val}
{to}=D{offset_sign}A
"""

    # increase sp pointer
    @staticmethod
    def dec_sp():
        return f"""\
@SP
M=M-1
A=M
"""
    
    # decrese sp pointer 
    @staticmethod
    def inc_sp():
        return f"""\
@SP
M=M+1
A=M
"""

    @staticmethod
    def pop_sp_to_d():
        return f"""\
{AsmTempl.dec_sp()}\
D=M
"""

    @staticmethod
    def push_d_to_sp():
        return f"""\
{AsmTempl.load_address("SP", "0")}\
M=D
{AsmTempl.inc_sp()}\
"""

    @staticmethod
    def stack_unary_op(op: str):
        # first load top of stack into D,
        # do arithmetic on D and write it back to top of stack.
        # we do this without modified stack pointer (SP) for optimization 
        asm_code = f"""\
{AsmTempl.load_address("SP", "-1")}\
D=M
D={op}D
M=D
"""

        return asm_code

    @staticmethod
    def stack_binary_op(op: str):
        # pop top of stack into D
        asm_code = AsmTempl.pop_sp_to_d()

        # load current top stack pointer and do arithmetic on M and D register
        asm_code += f"""\
{AsmTempl.load_address("SP", "-1")}\
D=M{op}D
M=D
"""

        return asm_code

    @staticmethod
    def stack_compare_op(op: str, label: str):
        op = op.upper()
        end_label = f"{op}_END.{label}"

        return f"""\
{AsmTempl.pop_sp_to_d()}\
{AsmTempl.load_address("SP", "-1")}\
D=M-D
M=-1
@{end_label}
D;J{op.upper()}
{AsmTempl.load_address("SP", "-1")}\
M=0
({end_label})
"""

    @staticmethod
    def read_register_to_d(r):
        return f"""\
@{r}
D=M
"""

    @staticmethod
    def write_d_to_register(r):
        return f"""\
@{r}
M=D
"""

    @staticmethod
    def pop_sp_to_register(r):
        return f"""\
{AsmTempl.pop_sp_to_d()}\
{AsmTempl.write_d_to_register(r)}\
"""

    @staticmethod
    def read_segment_to_d(base, offset):
        return f"""\
{AsmTempl.load_address(base, offset)}\
D=M
"""

    @staticmethod
    def write_d_to_segment(base, offset):
        return f"""\
{AsmTempl.write_d_to_register(R_COPY_VAL)}\
{AsmTempl.load_address(base, offset, "D")}\
{AsmTempl.write_d_to_register(R_COPY_POINTER)}\
{AsmTempl.read_register_to_d(R_COPY_VAL)}\
{AsmTempl.load_address(R_COPY_POINTER, "0")}\
M=D
"""

    @staticmethod
    def pop_sp_to_segment(base, offset):
        return f"""\
{AsmTempl.load_address(base, offset, "D")}\
{AsmTempl.write_d_to_register(R_COPY_POINTER)}\
{AsmTempl.pop_sp_to_d()}\
{AsmTempl.load_address(R_COPY_POINTER, "0")}\
M=D
"""


class Generator:
    def __init__(self, file_name, cmds):
        self.file_name = file_name.replace(".vm", "")
        self.cmds = cmds

    def get_label(self, prefix: str, cmd):
        return f"{prefix or 'GENERATOR'}__{cmd.line}"

    def get_static_name(self, symbol: str):
        return f"{self.file_name}.{symbol}"

    def dec_arithmetic(self, cmd):
        op = cmd.tokens[0].value

        asm_code = f"//{cmd}\n"

        if op == "neg":
            asm_code += AsmTempl.stack_unary_op("-")
        elif op == "not":
            asm_code += AsmTempl.stack_unary_op("!")
        elif op == "add":
            asm_code += AsmTempl.stack_binary_op("+")
        elif op == "sub":
            asm_code += AsmTempl.stack_binary_op("-")
        elif op == "and":
            asm_code += AsmTempl.stack_binary_op("&")
        elif op == "or":
            asm_code += AsmTempl.stack_binary_op("|")
        elif op == "eq":
            asm_code += AsmTempl.stack_compare_op(op, self.get_label("CMP", cmd))
        elif op == "gt":
            asm_code += AsmTempl.stack_compare_op(op, self.get_label("CMP", cmd))
        elif op == "lt":
            asm_code += AsmTempl.stack_compare_op(op, self.get_label("CMP", cmd))
        else:
            raise Exception(f"generator error. unknown arithmetic operation '{op}'")

        return asm_code
    
    def dec_push(self, cmd):
        # push segment i
        segment = cmd.tokens[1].value
        i = cmd.tokens[2].value

        asm_code = f"//{cmd}\n"

        if segment == "constant":
            asm_code += AsmTempl.load_constant_to_d(i)
        elif segment == "local":
            asm_code += AsmTempl.read_segment_to_d("LCL", i)
        elif segment == "argument":
            asm_code += AsmTempl.read_segment_to_d("ARG", i)
        elif segment == "this":
            asm_code += AsmTempl.read_segment_to_d("THIS", i)
        elif segment == "that":
            asm_code += AsmTempl.read_segment_to_d("THAT", i)
        elif segment == "static":
            asm_code += AsmTempl.read_register_to_d(self.get_static_name(i))
        elif segment == "pointer":
            asm_code += AsmTempl.read_register_to_d("THIS" if i == "0" else "THAT")
        elif segment == "temp":
            asm_code += AsmTempl.read_register_to_d(f"R{int(i)+5}")
        else:
            raise Exception(f"generator error. unknown memory access segment '{segment}'")

        asm_code += AsmTempl.push_d_to_sp()

        return asm_code

    def dec_pop(self, cmd):
        # push segment i
        segment = cmd.tokens[1].value
        i = cmd.tokens[2].value

        asm_code = f"//{cmd}\n"

        if segment == "local":
            asm_code += AsmTempl.pop_sp_to_segment("LCL", i)
        elif segment == "argument":
            asm_code += AsmTempl.pop_sp_to_segment("ARG", i)
        elif segment == "this":
            asm_code += AsmTempl.pop_sp_to_segment("THIS", i)
        elif segment == "that":
            asm_code += AsmTempl.pop_sp_to_segment("THAT", i)
        elif segment == "static":
            asm_code += AsmTempl.pop_sp_to_register(self.get_static_name(i))
        elif segment == "pointer":
            asm_code += AsmTempl.pop_sp_to_register("THIS" if i == "0" else "THAT")
        elif segment == "temp":
            asm_code += AsmTempl.pop_sp_to_register(f"R{int(i)+5}")
        else:
            raise Exception(f"generator error. unknown memory segment '{segment}'")

        return asm_code

    def decode_cmd(self, pos):
        cmd = self.cmds[pos]
        if cmd == None:
            raise Exception("generator error. null command")
        
        if cmd.type == C_ARITHMETIC:
            return self.dec_arithmetic(cmd)

        if cmd.type == C_PUSH:
            return self.dec_push(cmd)

        if cmd.type == C_POP:
            return self.dec_pop(cmd)

        raise Exception("generator error. unknown command")


    def run(self, outf):
        i = 0
        while i < len(self.cmds):
            asm_code = self.decode_cmd(i)
            outf.write(asm_code + "\n")
            i+=1


def main():
    vm_file = sys.argv[1]

    asm_file = vm_file.replace(".vm", ".asm") if vm_file.endswith(".vm") else (vm_file + ".asm")
    if len(sys.argv) > 2:
        asm_file = sys.argv[3]

    inf = open(vm_file, 'r')
    input = inf.read()
    inf.close()
    l = Lexer(input, lex_line)
    l.run()

    outf = open(asm_file, 'w')
    g = Generator(os.path.basename(vm_file), l.cmds)
    g.run(outf)
    outf.close()

if __name__ == "__main__":
    main()

