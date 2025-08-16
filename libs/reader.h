#ifndef READER_H
#define READER_H

#include <string>
#include <vector>

namespace bar {

class Reader {
 public:
  Reader(std::string filename);
  std::vector<char>& getbuf();
  int getrow() const;
  int getcol() const;

  void reset();
  char curch();
  char nextch();
  char seekch();
  // char backch();

 private:
  std::vector<char> buffer;
  int ptr;
  int row;
  int col;
  std::string filepath;
};

}  // namespace bar

#endif
