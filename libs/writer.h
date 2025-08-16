#ifndef WRITER_H
#define WRITER_H

#include <string>
#include <vector>

namespace bar {

class Writer {
 public:
  Writer(std::string filename);

  void write(std::vector<std::string> lines);

 private:
  std::string filepath;
};

}  // namespace bar

#endif
