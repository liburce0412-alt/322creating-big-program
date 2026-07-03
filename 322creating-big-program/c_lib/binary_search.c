/**
 * 二分查找模块 — 谢佳杨
 * TODO: 实现二分查找算法
 */
#include <stdio.h>
#include <string.h>
#include "binary_search.h"

void binary_search_handler(const char *action, const char *json_data, char *output) {
    if (strcmp(action, "search") == 0) {
        /* TODO: 从 json_data 中解析数组和目标值，执行二分查找 */
        snprintf(output, 8192,
                 "{\"success\":true,\"index\":-1,\"note\":\"TODO: 谢佳杨 实现二分查找\"}");
    } else {
        snprintf(output, 8192,
                 "{\"success\":false,\"error\":\"Unknown action: %s\"}", action);
    }
}
