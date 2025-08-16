#include "lexer.h"

#include <iostream>

namespace bar {

std::ostream& operator<<(std::ostream& os, const Token& t) { return os << t.str(); }

}  // namespace bar
