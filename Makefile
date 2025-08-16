# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++14 -Wall -I.

# Directories
BUILD_DIR = build
ASSEMBLY_DIR = assembly
LIBS_DIR = libs
VM_DIR = vmtranslator

VPATH = $(ASSEMBLY_DIR) $(LIBS_DIR) $(VM_DIR)

# --- Library sources and objects ---
LIB_SRCS = $(notdir $(wildcard $(LIBS_DIR)/*.cpp))
LIB_OBJS = $(addprefix $(BUILD_DIR)/, $(LIB_SRCS:.cpp=.o))

# --- Assembler sources and objects ---
ASSEMBLER_SRC = assembler.cpp
ASSEMBLER_OBJ = $(addprefix $(BUILD_DIR)/, $(ASSEMBLER_SRC:.cpp=.o))
ASSEMBLER_TARGET = $(addprefix $(ASSEMBLY_DIR)/, assembler)

# --- VM Translator sources and objects ---
VM_SRC = vmtranslator.cpp
VM_OBJ = $(addprefix $(BUILD_DIR)/, $(VM_SRC:.cpp=.o))
VM_TARGET = $(addprefix $(VM_DIR)/, vmtranslator)

.PHONY: all clean assembler vmtranslator

all: assembler vmtranslator

assembler: $(ASSEMBLER_TARGET)

vmtranslator: $(VM_TARGET)

test:
	@echo $(LIB_SRCS)
	@echo $(LIB_OBJS)

# --- Linker rules ---
$(ASSEMBLER_TARGET): $(ASSEMBLER_OBJ) $(LIB_OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(VM_TARGET): $(VM_OBJ) $(LIB_OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^

# --- Compilation rule ---
$(BUILD_DIR)/%.o: %.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -rf $(BUILD_DIR) $(ASSEMBLER_TARGET) $(VM_TARGET)
