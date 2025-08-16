#include "reader.h"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace bar {

Reader::Reader(std::string _filepath) : filepath(std::move(_filepath)) {
  std::ifstream file(filepath, std::ios::binary);
  if (!file) {
    throw std::runtime_error("Could not open file");
  }

  // Go to the end to get file size
  file.seekg(0, std::ios::end);
  std::streamsize size = file.tellg();
  file.seekg(0, std::ios::beg);

  // Allocate vector with file size
  buffer = std::vector<char>(size);

  // Read all bytes into the vector
  if (!file.read(buffer.data(), size)) {
    throw std::runtime_error("Could not read file");
  }

  reset();
}

std::vector<char>& Reader::getbuf() { return buffer; }

int Reader::getrow() const { return row; }
int Reader::getcol() const { return col; }

void Reader::reset() {
  ptr = 0;
  col = buffer.empty() ? 0 : 1;
  row = buffer.empty() ? 0 : 1;
}

char Reader::curch() {
  if (ptr >= buffer.size()) {
    return EOF;
  }

  return buffer[ptr];
}

char Reader::nextch() {
  if (ptr >= buffer.size() - 1) {
    if (ptr == buffer.size() - 1) {
      ++ptr;
    }
    return EOF;
  }

  col++;
  if (buffer[ptr] == '\n') {
    col = 1;
    row++;
  }

  return buffer[++ptr];
}

char Reader::seekch() {
  if (ptr >= buffer.size() - 1) {
    return EOF;
  }
  return buffer[ptr + 1];
}

// char Parser::backch() {
//   if (cur >= buffer.size()) {
//     return EOF;
//   }
//   return buffer[--cur];
// }

}  // namespace bar
