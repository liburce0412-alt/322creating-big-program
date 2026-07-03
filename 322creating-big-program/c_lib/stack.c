/**
 * 栈模块 — 李恩琪 + 余欣泽
 * TODO: 实现栈的基本操作（push、pop、peek 等）
 */
#include <stdio.h>
#include <string.h>
#include "stack.h"

void stack_handler(const char *action, const char *json_data, char *output) {
    if (strcmp(action, "push") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 李恩琪+余欣泽 实现栈push\"}");
    } else if (strcmp(action, "pop") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 李恩琪+余欣泽 实现栈pop\"}");
    } else if (strcmp(action, "peek") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 李恩琪+余欣泽 实现栈peek\"}");
    } else {
        snprintf(output, 8192,
                 "{\"success\":false,\"error\":\"Unknown action: %s\"}", action);
    }
}
