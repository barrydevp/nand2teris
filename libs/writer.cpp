#include "writer.h"

#include <fstream>

namespace bar {

Writer::Writer(std::string filename) : filepath(std::move(filename)) {}

void Writer::write(std::vector<std::string> lines) {
  std::ofstream file(filepath);
  if (!file) {
    throw std::runtime_error("Could not open file for writing");
  }

  for (const auto& line : lines) {
    file << line << '\n';
  }

  file.close();
  if (!file) {
    throw std::runtime_error("Error writing to file");
  }
}

}  // namespace bar
