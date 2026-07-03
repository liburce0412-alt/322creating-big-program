/**
 * 队列模块 — 谢佳杨
 * TODO: 实现队列的基本操作（enqueue、dequeue 等）
 */
#include <stdio.h>
#include <string.h>
#include "queue.h"

void queue_handler(const char *action, const char *json_data, char *output) {
    if (strcmp(action, "enqueue") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 谢佳杨 实现队列enqueue\"}");
    } else if (strcmp(action, "dequeue") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 谢佳杨 实现队列dequeue\"}");
    } else {
        snprintf(output, 8192,
                 "{\"success\":false,\"error\":\"Unknown action: %s\"}", action);
    }
}
