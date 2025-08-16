import re
import sys

# INSTRUCTION
INS_A = 1
INS_C = 2
INS_L = 3

# TOKEN
TOK_ERROR = 1
TOK_NUMBER = 2
TOK_SYMBOL = 3
TOK_ATSIGN = 4
TOK_LEFTPAREN = 5
TOK_RIGHPAREN = 6
TOK_LABEL = 7
TOK_OPERATOR = 8
TOK_ASSIGN = 9
TOK_SEMICOLON = 10
TOK_KEYWORD = 11
TOK_REGISTER = 12
TOK_DEST = 13
TOK_COMP = 14
TOK_JMP = 15

EOF = None


class LexerError(Exception):
    def __init__(self, message, line, pos):
        super().__init__(f"{message}. {line}:{pos}")


class SyntaxError(LexerError):
    def __init__(self, message, line, pos):
        super().__init__(f"syntax error, {message}", line, pos)


class SymbolTable:
    def __init__(self):
        self._symbols = {
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4,
            "R0": 0,
            "R1": 1,
            "R2": 2,
            "R3": 3,
            "R4": 4,
            "R5": 5,
            "R6": 6,
            "R7": 7,
            "R8": 8,
            "R9": 9,
            "R10": 10,
            "R11": 11,
            "R12": 12,
            "R13": 13,
            "R14": 14,
            "R15": 15,
            "SCREEN": 0x4000,
            "KBD": 0x6000,
        }
        self.register_count = 16

    def put(self, symbol, value):
        if value == None:
            if self.has(symbol):
                return

        self._symbols[symbol] = value

    def get(self, symbol):
        return self._symbols[symbol]

    def has(self, symbol):
        return symbol in self._symbols

    def relocate(self, symbol):
        if not self.has(symbol):
            raise Exception(f"symbol {symbol} notfound")

        if self.get(symbol) == None:
            # increase register number for variable by one
            self._symbols[symbol] = self.register_count
            self.register_count += 1

        return self.get(symbol)


class Instruction:
    def __init__(self, line, tokens=[]):
        self.line = line
        self.tokens = tokens

    def relocate(self, symbol_table: SymbolTable) -> None:
        raise Exception("not implemented")

    def to_bin(self) -> str:
        raise Exception("not implemented")

    def __repr__(self) -> str:
        return "NULL: (0)"


_dest_codes = ["", "M", "D", "MD", "A", "AM", "AD", "AMD"]
_comp_codes = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "!D": "0001101",
    "!A": "0110001",
    "-D": "0001111",
    "-A": "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    "M": "1110000",
    "!M": "1110001",
    "-M": "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}
_jump_codes = ["", "JGT", "JEQ", "JGE", "JLT", "JNE", "JLE", "JMP"]


def bits(num):
    return bin(int(num))[2:]


class InstructionA(Instruction):
    def __init__(self, line, tokens, symbol, address):
        super().__init__(line, tokens)
        self.symbol = symbol
        self.address = address

    def relocate(self, symbol_table: SymbolTable):
        if self.address == None:
            if not symbol_table.has(self.symbol):
                raise LexerError(
                    f"relocate error. cannot find address of symbol {self.symbol}",
                    self.line,
                    self.tokens[1].pos,
                )

            self.address = symbol_table.relocate(self.symbol)

    def to_bin(self):
        addr_bin = bits(int(self.address))
        if len(addr_bin) > 15:
            raise LexerError(
                f"address out of range [0 : 2^16-1] {self.address}",
                self.line,
                self.tokens[1].pos,
            )
        return "0" + addr_bin.zfill(15)

    def __repr__(self):
        return f"@{self.address}: {self.to_bin()}"


class InstructionC(Instruction):
    def __init__(self, line, tokens, dest, comp, jump):
        super().__init__(line, tokens)
        self.dest = dest
        self.comp = comp
        self.jump = jump

    def relocate(self, symbol_table: SymbolTable):
        pass

    def to_bin(self):
        b_ins = "111"

        if self.comp == None or _comp_codes[self.comp] == None:
            raise LexerError(f"unexpected comp '{self.comp}'", self.line, -1)
        b_ins += _comp_codes[self.comp]

        if self.dest != None:
            b_ins += bits(_dest_codes.index(self.dest)).zfill(3)
        else:
            b_ins += "".zfill(3)

        if self.jump != None:
            b_ins += bits(_jump_codes.index(self.jump)).zfill(3)
        else:
            b_ins += "".zfill(3)

        return b_ins

    def __repr__(self):
        return f"{self.dest}={self.comp};{self.jump}: {self.to_bin()}"


class Token:
    def __init__(self, type, value: str, pos, line):
        self.type = type
        self.pos = pos
        self.line = line
        self.value = value


class Lexer:
    def __init__(self, input: str, lex_start, symbol_table: SymbolTable):
        self.input = input
        self.input_len = len(input)
        self.start = 0
        self.pos = 0
        self.line = 1
        self.tokens = []
        self.lex_start = lex_start
        self.ins = []
        self.symbol_table = symbol_table

    def peek(self):
        if self.pos >= self.input_len:
            return EOF

        ch = self.input[self.pos]

        return ch

    # next char, increase pos
    def next(self):
        ch = self.peek()

        self.pos += 1
        if ch == "\n":
            self.line += 1

        return ch

    def back(self):
        self.pos -= 1
        ch = self.peek()

        if ch == "\n":
            self.line -= 1

    # consumes next char if its in valid set
    def accept(self, valid):
        ch = self.next()
        while ch and ch in valid:
            ch = self.next()
            pass
        self.back()

    # consumes next char if its match regex
    def accept_r(self, regex):
        ch = self.next()
        while ch and re.match(regex, ch):
            ch = self.next()
            pass
        self.back()

    # skip current line
    def skip_line(self):
        self.pos += self.input[self.pos :].index("\n") + 1
        self.start = self.pos
        self.line += 1

    def ignore(self, inc_line=False):
        if inc_line:
            self.line += self.input[self.start : self.pos].count("\n")
        self.start = self.pos

    def _pop_tok(self):
        if len(self.tokens) > 0:
            return self.tokens.pop(0)

    def _push_tok(self, type):
        token = Token(type, self.input[self.start : self.pos], self.start, self.line)
        self.tokens.append(token)
        self.start = self.pos

        return token

    def _flush_tok(self):
        self.tokens = []

    def run(self):
        lex_fn = self.lex_start
        while lex_fn != None:
            lex_fn = lex_fn(self)

    def assemble(self, outf):
        for ins in self.ins:
            ins.relocate(self.symbol_table)
            print(ins)
            outf.write(ins.to_bin() + "\n")


def is_alphanumeric(ch):
    return re.match(r"^\w+$", ch)


def lex_line(l: Lexer):
    # print(f"tokens[] = {l.tokens}")
    l._flush_tok()
    l.accept(" \t\n")
    l.ignore()
    ch = l.next()

    if ch == EOF:
        return None

    if ch == "/":
        if l.next() != "/":
            raise SyntaxError("unknown one '/' character", l.line, l.pos)
        # reach comment -> ignore current line
        # print('reach comment, ignore line.')
        l.skip_line()
        return lex_line

    print(f"start with '{ch}' at {l.line}:{l.pos}")

    if ch == "(":
        # TODO lex_label
        l.ignore()
        return lex_label

    if ch == "@":
        # TODO lex_a_ins
        return lex_a_ins

    # TODO lex_c_ins
    l.back()
    return lex_c_ins


def lex_end_line(l: Lexer):
    l.accept(" \t")
    ch = l.next()
    if ch == "/" and l.next() == "/":
        l.skip_line()
    elif ch != "\n":
        raise SyntaxError(f"unexpected end of line '{ch}'", l.line, l.pos)

    return lex_line


def lex_label(l: Lexer):
    ch = l.next()
    # label must only starting with alphabetic or underscore
    if not ch == None and not re.match(r"[A-Za-z_]", ch):
        raise SyntaxError(
            f"label must only start with alphabetic or underscore, but got '{ch}'",
            l.line,
            l.pos,
        )

    l.accept_r(r"[\w_.$:]")
    # ch = l.next()
    # while is_alphanumeric(ch):
    #     ch = l.next()

    # l.back()
    token = l._push_tok(TOK_LABEL)
    label = token.value
    ch = l.next()

    if ch != ")":
        raise SyntaxError(f"unexpected label character '{ch}'", l.line, l.pos)

    if l.symbol_table.has(label) and l.symbol_table.get(label) != None:
        raise SyntaxError(f"duplicate label '{label}'", l.line, l.pos)

    l.symbol_table.put(label, len(l.ins))
    print(f"(LABEL) {label}")

    return lex_end_line


def lex_a_ins(l: Lexer):
    l._push_tok(TOK_ATSIGN)

    ch = l.next()

    if ch == None:
        raise SyntaxError(
            f"A-instruction: unexpected format, must be '@symbol|number' but got '{ch}'",
            l.line,
            l.pos,
        )

    # number
    if "0" <= ch and ch <= "9":
        l.accept_r(r"\d")
        token = l._push_tok(TOK_NUMBER)
        l.ins.append(InstructionA(token.line, l.tokens, token.value, token.value))

        # trail and check end line
        # l.accept(" \t")
        # if l.next() != '\n':
        #     raise SyntaxError(f"A-instruction: unexpected number '{l.input[l.start:l.pos]}'", l.line, l.pos)
        print(f"(A) @{token.value}")
        return lex_end_line

    # symbol
    if re.match(r"[A-Za-z_]", ch):
        l.accept_r(r"[\w_.$:]")
        # l.accept_r(r"\w")
        token = l._push_tok(TOK_SYMBOL)
        l.ins.append(InstructionA(token.line, l.tokens, token.value, None))
        l.symbol_table.put(token.value, None)

        # trail and check end line
        # l.accept(" \t")
        # if l.next() != '\n':
        #     raise SyntaxError(f"A-instruction: unexpected symbol '{l.input[l.start:l.pos]}'", l.line, l.pos)
        print(f"(A) @{token.value}")
        return lex_end_line

    raise SyntaxError(
        f"A-instruction: unexpected format, must be '@symbol|number' but got '{ch}'",
        l.line,
        l.pos,
    )


def lex_c_ins(l: Lexer):
    dest = None
    comp = None
    jump = None

    l.accept_r(r"[AMD]")
    # dest part
    if l.peek() == "=":
        token = l._push_tok(TOK_DEST)
        dest = token.value
        l.next()
        l._push_tok(TOK_ASSIGN)

    l.accept_r(r"[AMD+\-&|!01]")
    # comp part
    if l.pos == l.start:
        # check if comp part is missing
        raise SyntaxError(
            f"C-instruction: unexpected format, must be 'dest=comp;jump' but got '{l.input[l.start:l.pos]}'",
            l.line,
            l.pos,
        )
    token = l._push_tok(TOK_COMP)
    comp = token.value

    # check if has jmp part
    if l.peek() == ";":
        l.next()
        l._push_tok(TOK_SEMICOLON)
        l.accept(r"[JGEQLTNMP]")
        token = l._push_tok(TOK_JMP)
        jump = token.value

    l.ins.append(InstructionC(l.line, l.tokens, dest, comp, jump))

    # trail and check end line
    # l.accept(" \t")
    # if l.next() != '\n':
    #     raise SyntaxError(f"C-instruction: unexpected format '{l.input[l.start:l.pos]}'", l.line, l.pos)
    print(f"(C) {dest}={comp};{jump}")

    return lex_end_line


def main():
    asm_file = sys.argv[1]

    hack_file = (
        asm_file.replace(".asm", ".hack")
        if asm_file.endswith(".asm")
        else (asm_file + ".hack")
    )
    if len(sys.argv) > 2:
        hack_file = sys.argv[3]

    inf = open(asm_file, "r")
    input = inf.read()
    inf.close()
    symbol_table = SymbolTable()
    l = Lexer(input, lex_line, symbol_table)
    l.run()
    print(symbol_table._symbols)
    outf = open(hack_file, "w")
    l.assemble(outf)
    outf.close()


if __name__ == "__main__":
    main()
