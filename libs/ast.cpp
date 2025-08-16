#include "ast.h"

namespace bar {

AST::AST(std::vector<std::shared_ptr<Token>>&& toks) : toks(std::move(toks)) {}

std::string AST::toksstr() const {
  std::string result = "[ ";
  for (const auto& tok : toks) {
    if (tok) {
      result += "\"" + tok->value + "\" ";
    } else {
      result += "\"\" ";
    }
  }
  result += "]";
  return result;
}

ExprAST::ExprAST(std::vector<std::shared_ptr<Token>>&& toks) : AST(std::move(toks)) {}

}  // namespace bar
