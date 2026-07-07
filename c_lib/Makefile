# Makefile — C 模块编译
# 将所有数据结构的 .c 编译并链接为单一可执行文件 campus_lib
#
# 使用:
#   make              — 编译所有模块
#   make clean        — 清理编译产物
#   make test-queue   — 测试队列模块

CC       = gcc
CFLAGS   = -Wall -Wextra -O2 -std=c99
LDFLAGS  =

# 当前可编译的源文件（queue 模块已完成，其余模块后续补充）
SOURCES  = queue.c \
           main.c
#          linked_list.c \
#          binary_search.c \
#          stack.c \
#          kmp.c \
#          hash_table.c \

OBJECTS  = $(SOURCES:.c=.o)
TARGET   = campus_lib

# 默认目标
all: $(TARGET)

# 链接
$(TARGET): $(OBJECTS)
	$(CC) $(LDFLAGS) -o $@ $^
	@echo "[OK] 编译完成: $(TARGET)"

# 编译规则
%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

# main.c 没有对应的 .h 文件
main.o: main.c
	$(CC) $(CFLAGS) -c -o $@ $<

# 清理
clean:
	rm -f $(OBJECTS) $(TARGET) queue_data.json
	@echo "[OK] 清理完成"

# 单独测试队列模块（编译为独立测试程序）
test-queue: queue.c queue.h
	$(CC) $(CFLAGS) -DQUEUE_STANDALONE_TEST -o test_queue queue.c
	@echo "[OK] 队列测试程序编译完成: ./test_queue"
	@echo "  测试入队: echo '{\"command\":\"enqueue\",\"data\":\"hello\"}' | ./test_queue"
	@echo "  测试出队: echo '{\"command\":\"dequeue\"}' | ./test_queue"
	@echo "  测试大小: echo '{\"command\":\"size\"}' | ./test_queue"

.PHONY: all clean test-queue
