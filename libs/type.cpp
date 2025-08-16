#include "type.h"

#include <cctype>

bool isidentnonalnum(char c) { return c == '_' || c == ':' || c == '$' || c == '.'; }

bool isidentstart(char c) { return std::isalpha(c) || isidentnonalnum(c); }

bool isident(char c) { return std::isalnum(c) || isidentnonalnum(c); }

bool isaddoperator(char c) { return c == '+' || c == '-'; }
bool ismuloperator(char c) { return c == '*' || c == '/'; }
bool ismodoperator(char c) { return c == '%'; }
bool islogicoperator(char c) { return c == '&' || c == '|' || c == '!'; }

bool isoperator(char c) {
  return c == '*' || c == '/' || c == '+' || c == '-' || c == '&' || c == '|' || c == '!' ||
         c == '%';
}
