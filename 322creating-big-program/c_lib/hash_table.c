/**
 * 哈希表模块 — 李恩琪 + 余欣泽
 * TODO: 实现哈希表的插入、查找、删除等操作
 */
#include <stdio.h>
#include <string.h>
#include "hash_table.h"

void hash_table_handler(const char *action, const char *json_data, char *output) {
    if (strcmp(action, "insert") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 李恩琪+余欣泽 实现哈希表insert\"}");
    } else if (strcmp(action, "search") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 李恩琪+余欣泽 实现哈希表search\"}");
    } else if (strcmp(action, "delete") == 0) {
        snprintf(output, 8192,
                 "{\"success\":true,\"note\":\"TODO: 李恩琪+余欣泽 实现哈希表delete\"}");
    } else {
        snprintf(output, 8192,
                 "{\"success\":false,\"error\":\"Unknown action: %s\"}", action);
    }
}
