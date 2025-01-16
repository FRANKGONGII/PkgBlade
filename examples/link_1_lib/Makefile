# 编译器和编译选项
CC = gcc
CFLAGS = -Wall -Wextra -g

# 目标文件
TARGET = example

# 共享库相关
SHARED_LIB_DIR = ../library       # 已有共享库所在目录
SHARED_LIB_NAME = libmylib.so          # 共享库名称

# 源文件
MAIN_SRC = example.c

# 包含目录和库路径
INCLUDE_DIRS = -I.
LIB_DIRS = -L$(SHARED_LIB_DIR)

# 链接的共享库
LIBS = -lmylib

# 默认目标
all: $(TARGET)

# 编译主程序并链接已有共享库
$(TARGET): $(MAIN_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(LIB_DIRS) $(LIBS)

# 清理目标文件
clean:
	rm -f $(TARGET)

# 伪目标，避免文件名冲突
.PHONY: all clean
