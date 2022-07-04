import typing
import re
import sys
import os
import glob

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
        return lex_branching

    # function
    if l.next_matchs(["function", "call"]):
        return lex_function
    
    # function return
    if l.next_match("return"):
        return lex_function_return

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

    # "segment"
    l.accept_r(r"\w")
    l._push_tok(TOK_ARG)
    ignore_blank(l)

    # "i"
    l.accept_r(r"\d")
    l._push_tok(l)

    if cmd_tok.value == "push":
        l._push_cmd(C_PUSH)
    else:
        l._push_cmd(C_POP)

    return lex_end_line

def lex_branching(l: Lexer):
    print("-> branching")

    cmd_str = l._push_tok(TOK_CMD).value
    cmd_type = C_LABEL
    if cmd_str == "goto":
        cmd_type = C_GOTO
    elif cmd_str == "if-goto":
        cmd_type = C_IF

    ignore_blank(l)

    # "label"
    l.accept_r(r"[\w_.$:]")
    l._push_tok(TOK_ARG)

    l._push_cmd(cmd_type)

    return lex_end_line

def lex_function(l: Lexer):
    print("-> function")

    cmd_str = l._push_tok(TOK_CMD).value
    cmd_type = C_FUNCTION
    if cmd_str == "call":
        cmd_type = C_CALL

    ignore_blank(l)

    # "functionName"
    l.accept_r(r"[\w_.$:]")
    l._push_tok(TOK_ARG)
    ignore_blank(l)
    
    # "nArgs"
    l.accept_r(r"\d")
    l._push_tok(TOK_ARG)

    l._push_cmd(cmd_type)

    return lex_end_line

def lex_function_return(l: Lexer):
    print("-> function return")

    l._push_tok(TOK_CMD)
    l._push_cmd(C_RETURN)
    return lex_end_line

R_COPY_VAL = "R13"
R_COPY_POINTER = "R14"
R_RET_ADDRESS = "R15"

class AsmTempl:
    def __init__(self):
        pass

    @staticmethod
    def repeat(func, times=1):
        times = int(times)
        __c = ""
        while times > 0:
            __c += func()
            times -= 1

        return __c

    @staticmethod
    def c__vm_begin_bootstrap():
        return f"""\
// ---- VM Translator for Hack platform ----
// Author: barrydevp
// -----------------------

// === VM Initialize code _ BEGIN ===
"""

    @staticmethod
    def c__sys_bootstrap():
        return f"""// Bootstrap code
{AsmTempl.load_constant("256", "D")}\
{AsmTempl.write_to_register("SP", "D")}\
{AsmTempl.call_function("Sys.init", 0, 0)}\
"""
    
    @staticmethod
    def c__vm_end_bootstrap():
        return f"""\
// === VM Initialize code _ END   ===
    """

    @staticmethod
    def define_label(label):
        return f"""\
({label})
"""
    
    @staticmethod
    def goto_label(label):
        return f"""\
@{label}
0;JMP
"""

    @staticmethod
    def if_goto_label(label):
        return f"""\
{AsmTempl.pop_sp_to_d()}\
@{label}
D;JNE
"""

    @staticmethod
    def jump_from_register(reg):
        return f"""\
@{reg}
A=M
0;JMP
"""

    # {dst} = {comp_bef}constant{comp_aft}
    @staticmethod
    def load_constant(constant, dst="D", comp_bef="", comp_aft=""):
        return f"""\
@{constant}
{dst}={comp_bef}A{comp_aft}
"""
    
    # this function will compute and set "to" register to (mem value from base) + offset
    # "to" = M[base] + offset
    @staticmethod
    def load_address(base, offset, dst="A"):
        offset = int(offset)

        # load base
        __c = f"""\
@{base}
"""
        if offset == 0:
            return f"""\
{__c}\
{dst}=M
"""

        offset_sign = "+"
        offset_val = offset
        if offset < 0:
            offset_sign = "-"
            offset_val = -offset 

        if offset_val == 1:
            return f"""\
{__c}\
{dst}=M{offset_sign}{offset_val}
"""
        
        return f"""\
{__c}\
D=M
@{offset_val}
{dst}=D{offset_sign}A
"""

    @staticmethod
    def read_address(base, offset, dst="D"):
        return f"""\
{AsmTempl.load_address(base, offset)}\
{dst}=M
"""

    # decrease pointer
    @staticmethod
    def dec_address(base):
        return f"""\
@{base}
M=M-1
A=M
"""

    # decrease sp pointer
    @staticmethod
    def dec_sp():
        return AsmTempl.dec_address("SP")    

    # increase pointer 
    @staticmethod
    def inc_address(base):
        return f"""\
@{base}
M=M+1
A=M
"""

    # increase sp pointer 
    @staticmethod
    def inc_sp():
        return AsmTempl.inc_address("SP")

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

    # *SP = constant; SP++
    @staticmethod
    def push_constant_to_sp(constant):
        return f"""\
{AsmTempl.load_constant(constant, "D")}\
{AsmTempl.push_d_to_sp()}\
"""

    @staticmethod
    def push_register_to_sp(reg):
        return f"""\
{AsmTempl.read_register(reg, "D")}\
{AsmTempl.push_d_to_sp()}\
"""

    @staticmethod
    def stack_unary_op(op: str):
        # first load top of stack into D,
        # do arithmetic on D and write it back to top of stack.
        # we do this without modified stack pointer (SP) for optimization 
        asm_code = f"""\
{AsmTempl.load_address("SP", "-1")}\
M={op}M
"""

        return asm_code

    @staticmethod
    def stack_binary_op(op: str):
        # pop top of stack into D
        asm_code = AsmTempl.pop_sp_to_d()

        # load current top stack pointer and do arithmetic on M and D register
        asm_code += f"""\
{AsmTempl.load_address("SP", "-1")}\
M=M{op}D
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
{AsmTempl.define_label(end_label)}
"""

    # {dst} = R
    # {dst} = {comp_bef}R{comp_aft} -> eg: {dst} = R + 1
    @staticmethod
    def read_register(reg, dst="D", comp_bef="", comp_aft=""):
        return f"""\
@{reg}
{dst}={comp_bef}M{comp_aft}
"""

    # R = D
    @staticmethod
    def write_to_register(reg, src="D"):
        return f"""\
@{reg}
M={src}
"""

    @staticmethod
    def pop_sp_to_register(reg):
        return f"""\
{AsmTempl.pop_sp_to_d()}\
{AsmTempl.write_to_register(reg)}\
"""

    @staticmethod
    def pop_address_to_register(base, reg):
        return f"""\
{AsmTempl.dec_address(base)}\
D=M
{AsmTempl.write_to_register(reg, "D")}\
"""

    # {dst} = *(base + offset)
    @staticmethod
    def read_segment(base, offset, dst="D"):
        return f"""\
{AsmTempl.load_address(base, offset)}\
{dst}=M
"""
    
    # *(base + offset) = {src}
    @staticmethod
    def write_to_segment(base, offset, src="D"):
        return f"""\
{AsmTempl.write_to_register(R_COPY_VAL, src)}\
{AsmTempl.load_address(base, offset, "D")}\
{AsmTempl.write_to_register(R_COPY_POINTER, "D")}\
{AsmTempl.read_register(R_COPY_VAL, "D")}\
{AsmTempl.load_address(R_COPY_POINTER, "0")}\
M=D
"""

    # *(base + offset) = pop()
    @staticmethod
    def pop_sp_to_segment(base, offset):
        return f"""\
{AsmTempl.load_address(base, offset, "D")}\
{AsmTempl.write_to_register(R_COPY_POINTER, "D")}\
{AsmTempl.pop_sp_to_d()}\
{AsmTempl.load_address(R_COPY_POINTER, "0")}\
M=D
"""

    @staticmethod
    def g__restore_function_frame():
        return f"""\
{AsmTempl.read_register("LCL", "D")}\
{AsmTempl.write_to_register(R_COPY_VAL, "D")}\
{AsmTempl.read_address(R_COPY_VAL, "-5", "D")}\
{AsmTempl.write_to_register(R_RET_ADDRESS, "D")}\
{AsmTempl.pop_sp_to_segment("ARG", "0")}\
{AsmTempl.load_address("ARG", "1", "D")}\
{AsmTempl.write_to_register("SP", "D")}\
{AsmTempl.pop_address_to_register(R_COPY_VAL, "THAT")}\
{AsmTempl.pop_address_to_register(R_COPY_VAL, "THIS")}\
{AsmTempl.pop_address_to_register(R_COPY_VAL, "ARG")}\
{AsmTempl.pop_address_to_register(R_COPY_VAL, "LCL")}\
{AsmTempl.jump_from_register(R_RET_ADDRESS)}\
"""

    @staticmethod
    def define_function(func_name, n_lcl):
        return f"""\
{AsmTempl.define_label(func_name)}\
{AsmTempl.load_constant("0", "D")}\
{AsmTempl.repeat(
    lambda : AsmTempl.push_d_to_sp(), n_lcl
)}\
"""

    @staticmethod
    def call_function(func_name, n_args, at_line):
        ret_label = f"{func_name}$ret.{at_line}"

        return f"""\
{AsmTempl.push_constant_to_sp(ret_label)}\
{AsmTempl.push_register_to_sp("LCL")}\
{AsmTempl.push_register_to_sp("ARG")}\
{AsmTempl.push_register_to_sp("THIS")}\
{AsmTempl.push_register_to_sp("THAT")}\
{AsmTempl.read_register("SP", "D")}\
{AsmTempl.write_to_register("LCL", "D")}\
{AsmTempl.load_constant(5 + int(n_args), "D", "D-")}\
{AsmTempl.write_to_register("ARG", "D")}\
{AsmTempl.goto_label(func_name)}
{AsmTempl.define_label(ret_label)}\
"""

    @staticmethod
    def return_function():
        return f"""\
{AsmTempl.g__restore_function_frame()}\
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

        asm_code = ""

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

        asm_code = ""

        if segment == "constant":
            asm_code += AsmTempl.load_constant(i)
        elif segment == "local":
            asm_code += AsmTempl.read_segment("LCL", i)
        elif segment == "argument":
            asm_code += AsmTempl.read_segment("ARG", i)
        elif segment == "this":
            asm_code += AsmTempl.read_segment("THIS", i)
        elif segment == "that":
            asm_code += AsmTempl.read_segment("THAT", i)
        elif segment == "static":
            asm_code += AsmTempl.read_register(self.get_static_name(i))
        elif segment == "pointer":
            asm_code += AsmTempl.read_register("THIS" if i == "0" else "THAT")
        elif segment == "temp":
            asm_code += AsmTempl.read_register(f"R{int(i)+5}")
        else:
            raise Exception(f"generator error. unknown memory access segment '{segment}'")

        asm_code += AsmTempl.push_d_to_sp()

        return asm_code

    def dec_pop(self, cmd):
        # pop segment i
        segment = cmd.tokens[1].value
        i = cmd.tokens[2].value

        asm_code = ""

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

    def dec_label(self, cmd):
        # label label
        label = cmd.tokens[1].value

        return AsmTempl.define_label(label)

    def dec_goto(self, cmd):
        # goto label
        label = cmd.tokens[1].value

        return AsmTempl.goto_label(label)

    def dec_if_goto(self, cmd):
        # if-goto label
        label = cmd.tokens[1].value

        return AsmTempl.if_goto_label(label)

    def dec_function(self, cmd):
        # function functionName nArgs
        func_name = cmd.tokens[1].value
        # nArgs = number of local variables (LCL)
        n_lcl = cmd.tokens[2].value

        return AsmTempl.define_function(func_name, n_lcl)

    def dec_call(self, cmd):
        # called at
        at_line = cmd.line
        # function functionName nArgs
        func_name = cmd.tokens[1].value
        # nArgs = number of argument (ARG)
        n_args = cmd.tokens[2].value

        return AsmTempl.call_function(func_name, n_args, at_line)

    def dec_return(self, cmd):

        return AsmTempl.return_function()

    def decode_cmd(self, pos):
        cmd = self.cmds[pos]
        if cmd == None:
            raise Exception("generator error. null command")

        asm_code = f"//{cmd}\n"
        
        if cmd.type == C_ARITHMETIC:
            pass
            asm_code += self.dec_arithmetic(cmd)
        elif cmd.type == C_PUSH:
            pass
            asm_code += self.dec_push(cmd)
        elif cmd.type == C_POP:
            pass
            asm_code += self.dec_pop(cmd)
        elif cmd.type == C_LABEL:
            pass
            asm_code += self.dec_label(cmd)
        elif cmd.type == C_GOTO:
            pass
            asm_code += self.dec_goto(cmd)
        elif cmd.type == C_IF:
            pass
            asm_code += self.dec_if_goto(cmd)
        elif cmd.type == C_FUNCTION:
            pass
            asm_code += self.dec_function(cmd)
        elif cmd.type == C_CALL:
            pass
            asm_code += self.dec_call(cmd)
        elif cmd.type == C_RETURN:
            pass
            asm_code += self.dec_return(cmd)
        else:
            raise Exception("generator error. unknown command")

        return asm_code

    def run(self, outf):
        i = 0
        while i < len(self.cmds):
            asm_code = self.decode_cmd(i)
            outf.write(asm_code + "\n")
            i+=1

def translate(vm_file, writer):
    print(f"=> Start translating {vm_file}")
    inf = open(vm_file, 'r')
    input = inf.read()
    inf.close()
    l = Lexer(input, lex_line)
    l.run()
    # for cmd in l.cmds:
    #     print(cmd)
    g = Generator(os.path.basename(vm_file), l.cmds)
    g.run(writer)

def main():
    input_name = sys.argv[1]
    vm_source = [input_name]

    asm_file = input_name.replace(".vm", ".asm")
    if not input_name.endswith(".vm"):
        asm_file = input_name + ".asm"
        vm_source = glob.glob(f"{input_name}/*.vm")

    if len(sys.argv) > 2:
        asm_file = sys.argv[3]

    outf = open(asm_file, 'w')

    # writing vm bootstrap begin section
    outf.write(AsmTempl.c__vm_begin_bootstrap() + '\n')
    # check exists Sys.vm file and write bootstrap code
    if "Sys.vm" in [file_path.split("/")[-1] for file_path in vm_source]:
        print("Writing bootstrap code")
        outf.write(AsmTempl.c__sys_bootstrap() + '\n')

    # writing vm bootstrap end section
    outf.write(AsmTempl.c__vm_end_bootstrap() + '\n')

    # translating file by file
    for vm_file in vm_source:
        translate(vm_file, outf)
    outf.close()

if __name__ == "__main__":
    main()

