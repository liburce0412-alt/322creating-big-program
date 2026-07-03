# Makefile —— campus_lib C 数据结构模块
# 编译生成独立的可执行文件，Python 通过 subprocess 调用

CC       = gcc
CFLAGS   = -Wall -Wextra -O2 -std=c99
LDFLAGS  = -lm

# 所有 .c 源文件（两组各自添加）
SOURCES  = main.c           \
           linked_list.c    \
           queue.c          \
           binary_search.c  \
           stack.c          \
           kmp.c            \
           hash_table.c

OBJECTS  = $(SOURCES:.c=.o)
TARGET   = campus_lib

# 默认目标
.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "✅ Build success: ./$(TARGET)"

%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

# main.c 依赖所有模块头文件
main.o: main.c linked_list.h queue.h binary_search.h stack.h kmp.h hash_table.h
	$(CC) $(CFLAGS) -c -o $@ $<

# 如果某个组的 .c 还没写，创建空桩以便编译通过
stack.o: stack.c stack.h
	$(CC) $(CFLAGS) -c -o $@ $< 2>/dev/null || true

kmp.o: kmp.c kmp.h
	$(CC) $(CFLAGS) -c -o $@ $< 2>/dev/null || true

hash_table.o: hash_table.c hash_table.h
	$(CC) $(CFLAGS) -c -o $@ $< 2>/dev/null || true

# 仅编译已完成的模块（谢佳杨负责的 3 个 + main.c）
partial: main.c linked_list.c linked_list.h queue.c queue.h binary_search.c binary_search.h
	$(CC) $(CFLAGS) -o $(TARGET) main.c linked_list.c queue.c binary_search.c $(LDFLAGS) \
		-Wl,--allow-multiple-definition
	@echo "✅ Partial build (3 modules): ./$(TARGET)"

# 测试
test: $(TARGET)
	@echo "=== 测试 linked_list ==="
	@echo '{"module":"linked_list","action":"append","data":{"role":"user","content":"你好"}}' | ./$(TARGET)
	@echo ""
	@echo '{"module":"linked_list","action":"append","data":{"role":"assistant","content":"你好！有什么可以帮助你的？"}}' | ./$(TARGET)
	@echo ""
	@echo '{"module":"linked_list","action":"to_array"}' | ./$(TARGET)
	@echo ""
	@echo "=== 测试 queue ==="
	@echo '{"module":"queue","action":"enqueue","data":{"request_id":"r1","model":"deepseek","prompt_hash":"abc","priority":0}}' | ./$(TARGET)
	@echo ""
	@echo '{"module":"queue","action":"size"}' | ./$(TARGET)
	@echo ""
	@echo '{"module":"queue","action":"dequeue"}' | ./$(TARGET)
	@echo ""
	@echo "=== 测试 binary_search ==="
	@echo '{"module":"binary_search","action":"search_by_time","data":{"target":1700000000,"records":[{"id":1,"timestamp":1600000000},{"id":2,"timestamp":1700000000},{"id":3,"timestamp":1800000000}]}}' | ./$(TARGET)
	@echo ""
	@echo '{"module":"binary_search","action":"range_search","data":{"start":1600000000,"end":1750000000,"records":[{"id":1,"timestamp":1600000000},{"id":2,"timestamp":1700000000},{"id":3,"timestamp":1800000000}]}}' | ./$(TARGET)
	@echo ""

clean:
	rm -f $(OBJECTS) $(TARGET)
	@echo "🧹 Cleaned"
