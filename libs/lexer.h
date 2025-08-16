#ifndef LEXER_H
#define LEXER_H

#include <iostream>
#include <string>

namespace bar {

enum TokenType {
  TOK_EOF = -3,
  TOK_EOL = -2,
  TOK_COMMENT = -1,
  TOK_ANY = 0,
  TOK_IDENTIFIER = 1,
  TOK_NUMBER = 2,
  TOK_OPERATOR = 3,
  TOK_EQUAL = 4,
  TOK_SEMICOLONS = 5,
};

class Token {
 public:
  TokenType type;
  std::string value;
  int col;
  int row;

  Token(TokenType type, const std::string& value, int col, int row)
      : type(type), value(value), col(col), row(row) {}

  std::string str() const {
    return "\"" + value + "\" " + std::to_string(type) + " " + std::to_string(row) + ":" +
           std::to_string(col);
  }
};

std::ostream& operator<<(std::ostream& os, const Token& t);

}  // namespace bar

#endif
