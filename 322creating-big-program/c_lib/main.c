/**
 * C 模块统一入口 — stdin JSON → 路由到各模块 → stdout JSON
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 模块声明 */
extern void linked_list_handler(const char *action, const char *json_data, char *output);
extern void stack_handler(const char *action, const char *json_data, char *output);
extern void queue_handler(const char *action, const char *json_data, char *output);
extern void kmp_handler(const char *action, const char *json_data, char *output);
extern void hash_table_handler(const char *action, const char *json_data, char *output);
extern void binary_search_handler(const char *action, const char *json_data, char *output);

int main() {
    char input[8192] = {0};
    char output[8192] = {0};

    /* 读取 stdin JSON */
    if (!fgets(input, sizeof(input), stdin)) {
        printf("{\"success\":false,\"error\":\"No input\"}\n");
        return 1;
    }

    /* 简单解析 module 和 action（不引入 JSON 库，使用字符串查找） */
    char module[64] = {0};
    char action[64] = {0};
    char data_start[4096] = {0};

    /* 提取 "module":"xxx" */
    char *p = strstr(input, "\"module\"");
    if (p) {
        p = strchr(p, ':');
        if (p) {
            p = strchr(p, '"');
            if (p) {
                p++;
                int i = 0;
                while (*p && *p != '"' && i < 63) module[i++] = *p++;
            }
        }
    }

    /* 提取 "action":"xxx" */
    p = strstr(input, "\"action\"");
    if (p) {
        p = strchr(p, ':');
        if (p) {
            p = strchr(p, '"');
            if (p) {
                p++;
                int i = 0;
                while (*p && *p != '"' && i < 63) action[i++] = *p++;
            }
        }
    }

    /* 提取 "data":{...} */
    p = strstr(input, "\"data\"");
    if (p) {
        p = strchr(p, '{');
        if (p) {
            strncpy(data_start, p, 4095);
        }
    }

    /* 路由到对应模块 */
    if (strcmp(module, "linked_list") == 0) {
        linked_list_handler(action, data_start, output);
    } else if (strcmp(module, "stack") == 0) {
        stack_handler(action, data_start, output);
    } else if (strcmp(module, "queue") == 0) {
        queue_handler(action, data_start, output);
    } else if (strcmp(module, "kmp") == 0) {
        kmp_handler(action, data_start, output);
    } else if (strcmp(module, "hash_table") == 0) {
        hash_table_handler(action, data_start, output);
    } else if (strcmp(module, "binary_search") == 0) {
        binary_search_handler(action, data_start, output);
    } else {
        snprintf(output, sizeof(output),
                 "{\"success\":false,\"error\":\"Unknown module: %s\"}", module);
    }

    printf("%s\n", output);
    return 0;
}
