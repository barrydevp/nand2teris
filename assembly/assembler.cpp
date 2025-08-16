#include <cctype>
#include <cstddef>
#include <iostream>
#include <map>
#include <memory>
#include <string>

#include "../libs/ast.h"
#include "../libs/context.h"
#include "../libs/lexer.h"
#include "../libs/reader.h"
#include "../libs/type.h"
#include "../libs/writer.h"

namespace {
using namespace bar;

const std::map<std::string, int> presymbols_to_addr = {
    {"SP", 0},   {"LCL", 1},  {"ARG", 2},  {"THIS", 3},       {"THAT", 4},   {"R0", 0},
    {"R1", 1},   {"R2", 2},   {"R3", 3},   {"R4", 4},         {"R5", 5},     {"R6", 6},
    {"R7", 7},   {"R8", 8},   {"R9", 9},   {"R10", 10},       {"R11", 11},   {"R12", 12},
    {"R13", 13}, {"R14", 14}, {"R15", 15}, {"SCREEN", 16384}, {"KBD", 24576}};

const std::string regsymbols[] = {"A", "D", "M"};

const std::string kwsymbols[] = {"JMP", "JEQ", "JGT", "JLT", "JNE", "JGE", "JLE"};

// comp to binary code map
const std::map<std::string, std::string> comp_to_bincode = {
    {"0", "0101010"},   {"1", "0111111"},   {"-1", "0111010"},  {"D", "0001100"},
    {"A", "0110000"},   {"!D", "0001101"},  {"!A", "0110001"},  {"-D", "0001111"},
    {"-A", "0110011"},  {"D+1", "0011111"}, {"A+1", "0110111"}, {"D-1", "0001110"},
    {"A-1", "0110010"}, {"D+A", "0000010"}, {"D-A", "0010011"}, {"A-D", "0000111"},
    {"D&A", "0000000"}, {"D|A", "0010101"}, {"M", "1110000"},   {"!M", "1110001"},
    {"-M", "1110011"},  {"M+1", "1110111"}, {"M-1", "1110010"}, {"D+M", "1000010"},
    {"D-M", "1010011"}, {"M-D", "1000111"}, {"D&M", "1000000"}, {"D|M", "1010101"},
};

const std::map<std::string, std::string> dest_to_bincode = {
    {"", "000"},  {"M", "001"},  {"D", "010"},  {"MD", "011"},
    {"A", "100"}, {"AM", "101"}, {"AD", "110"}, {"AMD", "111"},
};

const std::map<std::string, std::string> jmp_to_bincode = {
    {"", "000"},    {"JGT", "001"}, {"JEQ", "010"}, {"JGE", "011"},
    {"JLT", "100"}, {"JNE", "101"}, {"JLE", "110"}, {"JMP", "111"},
};

bool isregister(const std::string& s) { return s == "A" || s == "D" || s == "M"; }
bool isregister(const char& c) { return c == 'A' || c == 'D' || c == 'M'; }

class SymbolTable {
 private:
  std::map<std::string, int> tbl;
  int freeaddr;

 public:
  SymbolTable() { clear(); }

  void clear() {
    tbl = presymbols_to_addr;
    freeaddr = 16;
  }

  void put(const std::string& name) {
    if (tbl.find(name) != tbl.end()) {
      return;
    }
    tbl[name] = -1;
  }
  void putwaddr(const std::string& name, const int& addr) { tbl[name] = addr; }
  void putwinc(const std::string& name) {
    if (tbl.find(name) != tbl.end()) {
      return;
    }
    tbl[name] = freeaddr++;
  }
  const int get(const std::string& name) const {
    auto it = tbl.find(name);
    if (it == tbl.end()) {
      throw std::runtime_error("Symbol not found: " + name);
    }
    return it->second;
  }
  void relocate() {}
};

class AsmContext : public Context {
 public:
  SymbolTable symtbl;

  AsmContext() {}

 private:
};

class AsmAST : public AST {
 public:
  AsmAST() = default;
  AsmAST(std::vector<std::shared_ptr<Token>>&& toks) : AST(std::move(toks)) {}
  virtual std::string codegen(AsmContext*) = 0;
};

class AsmExprAST : public ExprAST {
 public:
  AsmExprAST() = default;
  AsmExprAST(std::vector<std::shared_ptr<Token>>&& toks) : ExprAST(std::move(toks)) {}
  virtual std::string codegen(AsmContext*) = 0;
};

class ConstantExprAST : public AsmExprAST {
 public:
  ConstantExprAST(int value, std::vector<std::shared_ptr<Token>>&& toks)
      : AsmExprAST(std::move(toks)) {
    if (value < 0 || value > 24576) {
      throw std::runtime_error("Constant value out of range[0-24576]: " + std::to_string(value));
    }
    this->value = value;
  }

  int getValue() const { return value; }

  std::string codegen(AsmContext*) override { return std::to_string(value); }

 private:
  int value;
};

class SymbolExprAST : public AsmExprAST {
 public:
  SymbolExprAST(const std::string& name, std::vector<std::shared_ptr<Token>>&& toks)
      : AsmExprAST(std::move(toks)), name(name) {}

  const std::string& getName() const { return name; }

  std::string codegen(AsmContext*) override {
    // For simplicity, we just return the symbol name
    return name;
  }

 private:
  std::string name;
};

class CompAST : public AsmExprAST {
 public:
  CompAST(const bool& isM, const std::string& raw, const std::string& op,
          std::unique_ptr<AsmExprAST>&& LHS, std::unique_ptr<AsmExprAST>&& RHS,
          std::vector<std::shared_ptr<Token>>&& toks)
      : AsmExprAST(std::move(toks)),
        isM(isM),
        raw(raw),
        op(op),
        LHS(std::move(LHS)),
        RHS(std::move(RHS)) {}

  std::string codegen(AsmContext* ctx) override {
    // Generate code for comp
    // return LHS->codegen(ctx) + " " + op + " " + RHS->codegen(ctx);

    return comp_to_bincode.at(raw);
  }

 private:
  bool isM;  // is M register (a=1)
  std::string raw;
  std::string op;
  std::unique_ptr<AsmExprAST> LHS, RHS;
};

class DestAST : public AsmAST {
 public:
  DestAST(std::unique_ptr<SymbolExprAST>&& dest, std::vector<std::shared_ptr<Token>>&& toks)
      : AsmAST(std::move(toks)), dest(std::move(dest)) {}

  static bool isdest(const std::string& s) {
    return s == "M" || s == "D" || s == "MD" || s == "A" || s == "AM" || s == "AD" || s == "AMD";
  }

  std::string codegen(AsmContext* ctx) override {
    // Generate code for dest
    return dest_to_bincode.at(dest->getName());
  }

 private:
  std::unique_ptr<SymbolExprAST> dest;
};

class JmpAST : public AsmAST {
 public:
  JmpAST(const std::string& jmp, std::vector<std::shared_ptr<Token>>&& toks)
      : AsmAST(std::move(toks)), jmp(jmp) {}

  const std::string& getJmp() const { return jmp; }

  static bool isjmp(const std::string& s) {
    return s == "JMP" || s == "JEQ" || s == "JGT" || s == "JLT" || s == "JNE" || s == "JGE" ||
           s == "JLE";
  }

  std::string codegen(AsmContext* ctx) override {
    // Generate code for jump
    return jmp_to_bincode.at(jmp);
  }

 private:
  std::string jmp;
};

class CommentAST : public AsmAST {
 public:
  CommentAST(const std::string& comment, std::vector<std::shared_ptr<Token>>&& toks)
      : AsmAST(std::move(toks)), comment(comment) {}

  const std::string& getComment() const { return comment; }

 private:
  std::string comment;
};

class InstrAST : public AsmAST {
 public:
  InstrAST(std::vector<std::shared_ptr<Token>>&& toks) : AsmAST(std::move(toks)) {}
};

class AInstrAST : public InstrAST {
 public:
  AInstrAST(std::unique_ptr<AsmExprAST>&& expr, std::vector<std::shared_ptr<Token>>&& toks)
      : InstrAST(std::move(toks)), expr(std::move(expr)) {}

  AsmExprAST* getExpr() const { return expr.get(); }

  SymbolExprAST* castToSymbol() const { return dynamic_cast<SymbolExprAST*>(expr.get()); }
  ConstantExprAST* castToConstant() const { return dynamic_cast<ConstantExprAST*>(expr.get()); }

  std::string codegen(AsmContext* ctx) override {
    // Generate code for A-instruction
    if (auto symexpr = castToSymbol()) {
      int addr = ctx->symtbl.get(symexpr->getName());
      std::cout << "Symbol address: " << addr << std::endl;
      return "0" + std::bitset<15>(addr).to_string();
    }

    if (auto conexpr = castToConstant()) {
      int val = conexpr->getValue();
      std::cout << "Constant value: " << val << std::endl;
      return "0" + std::bitset<15>(val).to_string();
    }

    throw std::runtime_error("Invalid expression in A-instruction");
  }

 private:
  std::unique_ptr<AsmExprAST> expr;
};

class CInstrAST : public InstrAST {
 public:
  CInstrAST(std::unique_ptr<DestAST>&& dest, std::unique_ptr<CompAST>&& comp,
            std::unique_ptr<JmpAST>&& jump, std::vector<std::shared_ptr<Token>>&& toks)
      : InstrAST(std::move(toks)),
        dest(std::move(dest)),
        comp(std::move(comp)),
        jump(std::move(jump)) {}

  std::string codegen(AsmContext* ctx) override {
    // Generate code for C-instruction
    return "111" + comp->codegen(ctx) + (dest ? dest->codegen(ctx) : "000") +
           (jump ? jump->codegen(ctx) : "000");
  }

 private:
  std::unique_ptr<DestAST> dest;
  std::unique_ptr<CompAST> comp;
  std::unique_ptr<JmpAST> jump;
};

class LabelAST : public AsmAST {
 public:
  LabelAST(std::unique_ptr<SymbolExprAST>&& label, const int location,
           std::vector<std::shared_ptr<Token>>&& toks)
      : AsmAST(std::move(toks)), label(std::move(label)), location(location) {}

  std::string getLabel() const { return label->getName(); }
  const int getLocation() const { return location; }

  std::string codegen(AsmContext* ctx) override {
    // Generate code for label instruction
    // return "(" + label->codegen(ctx) + ")";
    throw std::runtime_error("LabelAST cannot generate code");
  }

 private:
  std::unique_ptr<SymbolExprAST> label;
  int location;
};

class Lexer {
 public:
  Lexer(std::shared_ptr<Reader> reader) : reader(reader) { reset(); }

  void reset() {
    reader->reset();
    // std::cout << "Lexer reset with reader: " << reader << std::endl;
  }

  std::shared_ptr<Token> nexttok() {
    // std::cout << "Next token..." << std::endl;
    // std::cout << reader << std::endl;
    char c = reader->curch();
    // std::cout << "CUR: " << c << " (" << reader->getcol() << ":" << reader->getrow() << ")"
    //           << std::endl;

    // eat whitespace
    while (isspace(c) && c != EOL) {
      c = reader->nextch();
    }

    int col = reader->getcol();
    int row = reader->getrow();
    TokenType tok_type = TOK_ANY;
    std::string tok_value{c};

    // identifier [a-zA-Z_][a-zA-Z0-9_]*
    if (isidentstart(c)) {
      while (isident(c = reader->nextch())) {
        tok_value += c;
      }
      tok_type = TOK_IDENTIFIER;
      goto RET;
    }

    // number
    if (isdigit(c)) {
      while (isdigit(c = reader->nextch())) {
        tok_value += c;
      }

      tok_type = TOK_NUMBER;
      goto RET;
    }

    // comment
    if (c == '/') {
      if ((c = reader->nextch()) != '/') {
        throw std::runtime_error("Expected '//' for comment");
      }

      tok_value += c;
      while ((c = reader->nextch()) != EOF && c != EOL) {
        tok_value += c;
      }
      tok_type = TOK_COMMENT;
      goto RET;
    }

    // EOF
    if (c == EOF) {
      tok_type = TOK_EOF;
      goto RET;
    }

    if (isaddoperator(c)) {
      tok_type = TOK_OPERATOR;
    }

    if (c == '=') {
      tok_type = TOK_EQUAL;
    }

    if (c == ';') {
      tok_type = TOK_SEMICOLONS;
    }

    // EOL
    if (c == EOL) {
      tok_type = TOK_EOL;
    }

    reader->nextch();  // consume current character
    // std::cout << "EOL" << (c == parser.curch()) << std::endl;
  RET:
    // std::cout << "EXIT: " << tok_value << " " << tok_type << std::endl;
    return std::make_shared<Token>(tok_type, tok_value, col, row);
  }

 public:
  std::shared_ptr<Reader> reader;
};

class Assembler {
 private:
  std::shared_ptr<Token> cur_tok;
  std::shared_ptr<Lexer> lexer;

 public:
  std::vector<std::shared_ptr<InstrAST>> ins;
  std::vector<std::shared_ptr<LabelAST>> labels;

  Assembler(std::shared_ptr<Lexer> lexer) : lexer(lexer) { reset(); }

  void reset() {
    ins.clear();
    labels.clear();
    cur_tok = nullptr;
    lexer->reset();
  }

  void parse() {
    reset();

    cur_tok = lexer->nexttok();
    while (cur_tok->type != TOK_EOF) {
      // std::cout << "HELLO" << std::endl;
      std::cout << *cur_tok << std::endl;

      switch (cur_tok->type) {
        case TOK_COMMENT: {
          // auto comment = std::make_shared<CommentAST>(token->value,
          //                                             std::vector<std::shared_ptr<Token>>{token});
          // ins.push_back(comment);
          // cur_tok = lexer->nexttok();
          break;
        }
        case TOK_EOL:
          skipEOL();
          continue;
        default:
          // label instruction
          if (cur_tok->value == "(") {
            labels.push_back(parseLabelInstr());
          } else if (cur_tok->value == "@") {
            ins.push_back(parseAInstr());
          } else {
            ins.push_back(parseCInstr());
          }
          expectEOInstr();  // Expect end of instruction, should be EOL or Comment
      }
      cur_tok = lexer->nexttok();
    }
  }

  void skipEOL() {
    while (cur_tok->type == TOK_EOL) {
      cur_tok = lexer->nexttok();
    }
  }

  void expectEOInstr() {
    if (cur_tok->type != TOK_EOL && cur_tok->type != TOK_COMMENT) {
      throw std::runtime_error("Expected EOL or Comment, got: " + cur_tok->str());
    }
  }

  std::shared_ptr<AInstrAST> parseAInstr() {
    // cur_tok = '@'
    std::vector<std::shared_ptr<Token>> tokens{cur_tok, nullptr};
    cur_tok = lexer->nexttok();
    tokens[1] = cur_tok;
    std::unique_ptr<AsmExprAST> expr;
    switch (cur_tok->type) {
      case TOK_IDENTIFIER: {
        tokens[1] = cur_tok;
        expr = std::make_unique<SymbolExprAST>(cur_tok->value,
                                               std::vector<std::shared_ptr<Token>>{cur_tok});
        break;
      }
      case TOK_NUMBER: {
        tokens[1] = cur_tok;
        expr = std::make_unique<ConstantExprAST>(std::stoi(cur_tok->value),
                                                 std::vector<std::shared_ptr<Token>>{cur_tok});
        break;
      }
      default:
        throw std::runtime_error("Expected identifier or number after '@' in A-Instruction");
    }

    cur_tok = lexer->nexttok();  // next token
    return std::make_shared<AInstrAST>(std::move(expr), std::move(tokens));
  }

  std::unique_ptr<AsmExprAST> parseCompOperand(std::shared_ptr<Token> tok) {
    if (!tok) {
      return nullptr;
    }

    if (tok->type == TOK_IDENTIFIER) {
      if (!isregister(tok->value)) {
        throw std::runtime_error("Invalid C-instruction's comp register: " + tok->str());
      }

      return std::make_unique<SymbolExprAST>(tok->value, std::vector<std::shared_ptr<Token>>{tok});
    }

    if (tok->type == TOK_NUMBER) {
      return std::make_unique<ConstantExprAST>(std::stoi(tok->value),
                                               std::vector<std::shared_ptr<Token>>{tok});
    }

    throw std::runtime_error("Invalid C-instruction's comp operand: " + tok->str());
  }

  std::shared_ptr<CInstrAST> parseCInstr() {
    // cur_tok := constants(0,1) | symbol(A,D,M) | operator(+,-) | ';'

    std::vector<std::shared_ptr<Token>> tokens{};
    std::unique_ptr<DestAST> dest;
    std::unique_ptr<CompAST> comp;
    std::unique_ptr<JmpAST> jump;

    // remember we alway maitain two tokens: cur_tok and tok
    std::shared_ptr<Token> tok = cur_tok;
    // std::cout << tok->value << " is tok before dest parsing" << std::endl;
    // std::cout << cur_tok->value << " is cur_tok before dest parsing" << std::endl;

    // parse dest
    if (tok->type == TOK_IDENTIFIER) {
      cur_tok = lexer->nexttok();

      // std::cout << cur_tok->value << " is cur_tok" << std::endl;
      if (cur_tok->type == TOK_EQUAL) {
        tokens.push_back(tok);
        // should be dest=comp
        if (!DestAST::isdest(tok->value)) {
          throw std::runtime_error("Invalid C-instruction's dest: " + tok->str());
        }

        dest = std::make_unique<DestAST>(
            std::make_unique<SymbolExprAST>(tok->value, std::vector<std::shared_ptr<Token>>{tok}),
            std::vector<std::shared_ptr<Token>>{tok, cur_tok});

        tokens.push_back(cur_tok);
        tok = lexer->nexttok();      // eat "="
        cur_tok = lexer->nexttok();  // next token
      }
    }
    // std::cout << tok->value << " is tok after dest parsing" << std::endl;
    // std::cout << cur_tok->value << " is cur_tok after dest parsing" << std::endl;

    // parse comp => notice that comp is mandatory
    int operandidx = 0;
    bool isM = false;
    std::string raw_comp = "";
    std::vector<std::shared_ptr<Token>> comp_toks(3);

    while (operandidx < 3) {
      if (tok->type == TOK_OPERATOR) {
        operandidx = 2;
        comp_toks[1] = tok;
        raw_comp += tok->value;
        tokens.push_back(tok);
        tok = (cur_tok = (tok == cur_tok ? lexer->nexttok() : cur_tok));
      }

      if (tok->type != TOK_IDENTIFIER && tok->type != TOK_NUMBER) {
        break;
      }

      if (operandidx == 1) {
        throw std::runtime_error(
            "Invalid C-instruction's comp, expect operator after first operand");
      }
      comp_toks[operandidx++] = tok;
      raw_comp += tok->value;
      tokens.push_back(tok);
      tok = (cur_tok = (tok == cur_tok ? lexer->nexttok() : cur_tok));
    }

    // std::cout << operandidx << " operands found in comp: " << std::endl;
    // for (int i = 0; i < 3; i++) {
    //   if (comp_toks[i]) {
    //     std::cout << "  " << i << ": " << *comp_toks[i] << std::endl;
    //   } else {
    //     std::cout << "  " << i << ": null" << std::endl;
    //   }
    // }
    // check if valid comp
    if (comp_toks[0] == nullptr && comp_toks[2] == nullptr) {
      throw std::runtime_error("Invalid C-instruction's comp, no operands found");
    }

    if (comp_toks[0] != nullptr && comp_toks[1] != nullptr && comp_toks[2] == nullptr) {
      throw std::runtime_error("Invalid C-instruction's comp, missing the second operand");
    }

    if (comp_toks[0] != nullptr && comp_toks[2] != nullptr) {
      // cannot have two number operands
      if (comp_toks[0]->type == TOK_NUMBER && comp_toks[2]->type == TOK_NUMBER) {
        throw std::runtime_error("Invalid C-instruction's comp, two constant operands");
      }
      // if two operands are identifiers
      if (comp_toks[0]->type == TOK_IDENTIFIER && comp_toks[2]->type == TOK_IDENTIFIER) {
        // cannot have same identifier
        if (comp_toks[0]->value == comp_toks[2]->value) {
          throw std::runtime_error("Invalid C-instruction's comp, two same identifiers " +
                                   comp_toks[0]->value);
        }

        // if two operands are identifiers, A and M cannot be used together
        if ((comp_toks[0]->value == "M")) {
          isM = true;
          if (comp_toks[2]->value == "A") {
            throw std::runtime_error("Invalid C-instruction's comp, cannot use M and A together");
          }
        }
        if ((comp_toks[0]->value == "A" && comp_toks[2]->value == "M")) {
          throw std::runtime_error("Invalid C-instruction's comp, cannot use A and M together");
        }
      }
    }

    if (comp_toks[0] != nullptr && comp_toks[1] == nullptr) {
      // swap to RHS if only one operand is found
      comp_toks[2] = comp_toks[0];
      comp_toks[0] = nullptr;
    }

    comp = std::make_unique<CompAST>(isM, raw_comp, comp_toks[1] ? comp_toks[1]->value : "",
                                     parseCompOperand(comp_toks[0]), parseCompOperand(comp_toks[2]),
                                     std::move(comp_toks));

    // parse jump
    if (cur_tok->type == TOK_SEMICOLONS) {
      tokens.push_back(cur_tok);
      cur_tok = lexer->nexttok();  // eat ";"

      if (cur_tok->type != TOK_IDENTIFIER || !JmpAST::isjmp(cur_tok->value)) {
        throw std::runtime_error(
            "Invalid C-instruction's jump, expected jump's keywords after ';' got: " +
            cur_tok->str());
      }

      tokens.push_back(cur_tok);
      jump = std::make_unique<JmpAST>(cur_tok->value, std::vector<std::shared_ptr<Token>>{cur_tok});
      cur_tok = lexer->nexttok();  // next token
    }

    // std::cout << "cur_tok: " << (cur_tok ? cur_tok->str() : "null") << std::endl;
    // std::cout << "C-instruction parsed: " << (dest ? dest->toksstr() : "null") << std::endl;
    // std::cout << "Comp: " << (comp ? comp->toksstr() : "null") << std::endl;
    // std::cout << "Jump: " << (jump ? jump->toksstr() : "null") << std::endl;
    // std::cout << "cur_tok: " << (cur_tok ? cur_tok->str() : "null") << std::endl;

    return std::make_shared<CInstrAST>(std::move(dest), std::move(comp), std::move(jump),
                                       std::move(tokens));
  }

  std::shared_ptr<LabelAST> parseLabelInstr() {
    // cur_tok = '('
    std::vector<std::shared_ptr<Token>> tokens{cur_tok, nullptr, nullptr};
    cur_tok = lexer->nexttok();
    tokens[1] = cur_tok;

    if (cur_tok->type != TOK_IDENTIFIER) {
      throw std::runtime_error("Expected identifier after '(', got: " + cur_tok->str());
    }

    if (presymbols_to_addr.find(cur_tok->value) != presymbols_to_addr.end()) {
      throw std::runtime_error("Label cannot be a predefined symbol: " + cur_tok->str());
    }

    auto label = std::make_unique<SymbolExprAST>(cur_tok->value,
                                                 std::vector<std::shared_ptr<Token>>{cur_tok});

    cur_tok = lexer->nexttok();  // next token, should be ')'
    if (cur_tok->value != ")") {
      throw std::runtime_error("Expected ')' after label, got: " + cur_tok->str());
    }
    tokens[2] = cur_tok;

    cur_tok = lexer->nexttok();  // next token

    return std::make_shared<LabelAST>(std::move(label), ins.size(), std::move(tokens));
  }

  std::vector<std::string> link(AsmContext* ctx) {
    // put labels into symbol table
    for (auto label : labels) {
      ctx->symtbl.putwaddr(label->getLabel(), label->getLocation());
    }

    // put all A-instruction symbols into symbol table
    for (auto in : ins) {
      if (auto ain = std::dynamic_pointer_cast<AInstrAST>(in)) {
        if (auto sym_expr = ain->castToSymbol()) {
          ctx->symtbl.putwinc(sym_expr->getName());
        }
      }
    }

    // generate binary codes
    std::vector<std::string> bincodes;

    for (auto in : ins) {
      bincodes.push_back(in->codegen(ctx));
    }

    return bincodes;
  }
};

}  // namespace

int main(int argc, char* argv[]) {
  if (argc < 2) {
    std::cerr << "Usage: " << argv[0] << " <filename>\n";
    return 1;
  }

  const std::string ifilename = argv[1];
  std::string ofilename = ifilename;
  ofilename.replace(ofilename.find_last_of('.') + 1, std::string::npos, "hack");

  auto context = std::make_shared<AsmContext>();
  auto reader = std::make_shared<Reader>(ifilename);
  auto writer = std::make_shared<Writer>(ofilename);
  auto lexer = std::make_shared<Lexer>(reader);
  auto assembler = std::make_shared<Assembler>(lexer);

  assembler->parse();

  std::cout << "Parsed Instructions:" << std::endl;
  for (auto in : assembler->ins) {
    std::cout << in->toksstr() << std::endl;
  }

  std::cout << "Parsed Labels:" << std::endl;
  for (auto label : assembler->labels) {
    std::cout << label->toksstr() << std::endl;
  }

  std::cout << "Generated Binary Codes:" << std::endl;
  auto bincodes = assembler->link(context.get());
  for (auto code : bincodes) {
    std::cout << code << std::endl;
  }

  writer->write(bincodes);

  // std::cout << std::string(tokenizer.getbuf().begin(), tokenizer.getbuf().end()) << std::endl;
  // char c = parser.curch();
  // // std::cout << parser.curch() << std::endl;
  // while ((c) != EOF) {
  //   // Process each character as needed
  //   if (c != EOF) {
  //     std::cout << c << "(" << parser.getcol() << ":" << parser.getrow() << ")" << std::endl;
  //     ;  // Output the character
  //   }
  //   c = parser.nextch();
  // }

  // Lexer lexer(reader);
  //
  // std::shared_ptr<Token> token;
  //
  // while ((token = lexer->nexttok())->type != TOK_EOF) {
  //   // Process tokens as needed
  //   // std::cout << token << std::endl;
  //   std::cout << *token << std::endl;
  // }
}
