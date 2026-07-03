/**
 * 链表模块 — 谢佳杨
 * TODO: 实现链表的基本操作（增删改查、排序等）
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "linked_list.h"

void linked_list_handler(const char *action, const char *json_data, char *output) {
    if (strcmp(action, "sort") == 0) {
        /* TODO: 从 json_data 解析数组，使用链表排序后返回 */
        snprintf(output, 8192,
                 "{\"success\":true,\"sorted\":[1,2,3],\"note\":\"TODO: 谢佳杨 实现链表排序\"}");
    } else {
        snprintf(output, 8192,
                 "{\"success\":false,\"error\":\"Unknown action: %s\"}", action);
    }
}
