#ifndef AST_H
#define AST_H

#include <memory>
#include <vector>

#include "lexer.h"

namespace bar {

class AST {
 public:
  AST() = default;
  AST(std::vector<std::shared_ptr<Token>>&&);
  virtual ~AST() = default;

  std::string toksstr() const;

 protected:
  std::vector<std::shared_ptr<Token>> toks;
};

class ExprAST : public AST {
 public:
  ExprAST() = default;
  ExprAST(std::vector<std::shared_ptr<Token>>&&);
  virtual ~ExprAST() = default;
};

}  // namespace bar

#endif
