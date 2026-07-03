/* ================================================================
 * campus_lib —— 校园达人 CampusAI 数据结构 C 模块统一入口
 *
 * 协议：stdin 读取一行 JSON 命令 → 路由到对应模块 → stdout 输出 JSON
 *
 * 输入格式：
 *   {"module":"<模块名>","action":"<操作>","data":{...}}
 *
 * 输出格式：
 *   {"status":"ok","result":<模块返回值>}
 *   或 {"status":"error","error":"<错误消息>"}
 *
 * 支持的模块：
 *   linked_list    - 双向链表（AI 对话历史）
 *   queue          - 队列（AI 请求排队）
 *   stack          - 栈（撤销/重做）
 *   kmp            - KMP 字符串匹配（关键词搜索）
 *   hash_table     - 哈希表（快速检索）
 *   binary_search  - 二分查找（时间排序记录）
 *
 * 编译：gcc -Wall -O2 -o campus_lib main.c linked_list.c queue.c
 *           stack.c kmp.c hash_table.c binary_search.c
 * ================================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- 模块头文件 ---- */
#include "linked_list.h"
#include "queue.h"
#include "binary_search.h"

/* 前向声明（其他组的模块，编译时需链接对应的 .c 文件）*/
extern char* stack_handle(const char *action, const char *data_json);
extern char* kmp_handle(const char *action, const char *data_json);
extern char* hash_table_handle(const char *action, const char *data_json);

/* ========== JSON 辅助函数 ========== */

/* 从 JSON 中提取字符串值 */
static char* json_extract_string(const char *json, const char *key) {
    if (!json || !key) return NULL;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return NULL;
    pos += strlen(search);
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    if (*pos != '"') return NULL;
    pos++;
    const char *end = pos;
    while (*end && *end != '"') {
        if (*end == '\\' && *(end + 1)) end++;
        end++;
    }
    if (*end != '"') return NULL;
    size_t len = end - pos;
    char *result = (char*) malloc(len + 1);
    if (!result) return NULL;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        if (pos[i] == '\\' && i + 1 < len) {
            i++;
            switch (pos[i]) {
                case 'n':  result[j++] = '\n'; break;
                case 't':  result[j++] = '\t'; break;
                case 'r':  result[j++] = '\r'; break;
                case '"':  result[j++] = '"';  break;
                case '\\': result[j++] = '\\'; break;
                default:   result[j++] = pos[i]; break;
            }
        } else {
            result[j++] = pos[i];
        }
    }
    result[j] = '\0';
    return result;
}

/* 提取嵌套的 data 对象（{ ... }）的字符串 */
static char* json_extract_data_object(const char *json) {
    if (!json) return NULL;
    const char *pos = strstr(json, "\"data\"");
    if (!pos) {
        /* 没有 data 包装，整个输入可能就是 data */
        return strdup(json);
    }
    pos = strchr(pos, '{');
    if (!pos) return NULL;
    const char *start = pos;
    int depth = 0;
    while (*pos) {
        if (*pos == '{') depth++;
        else if (*pos == '}') {
            depth--;
            if (depth == 0) {
                size_t len = pos - start + 1;
                char *result = (char*) malloc(len + 1);
                if (!result) return NULL;
                memcpy(result, start, len);
                result[len] = '\0';
                return result;
            }
        } else if (*pos == '"') {
            pos++;
            while (*pos && *pos != '"') {
                if (*pos == '\\') pos++;
                if (*pos) pos++;
            }
        }
        pos++;
    }
    return strdup(json); /* fallback: 返回整个输入 */
}

/* ========== 主函数 ========== */

int main(void) {
    /* 设置 stdout 无缓冲，确保 JSON 输出完整 */
    setvbuf(stdout, NULL, _IONBF, 0);

    /* 读取 stdin 直到 EOF */
    char buffer[65536];
    size_t total = 0;
    int c;
    while ((c = getchar()) != EOF && total < sizeof(buffer) - 1) {
        buffer[total++] = (char) c;
    }
    buffer[total] = '\0';

    if (total == 0) {
        printf("{\"status\":\"error\",\"error\":\"empty input\"}\n");
        return 1;
    }

    /* 解析 module 和 action */
    char *module = json_extract_string(buffer, "module");
    char *action = json_extract_string(buffer, "action");
    char *data   = json_extract_data_object(buffer);

    if (!module) {
        printf("{\"status\":\"error\",\"error\":\"missing 'module' field\"}\n");
        free(action);
        free(data);
        return 1;
    }
    if (!action) {
        printf("{\"status\":\"error\",\"error\":\"missing 'action' field\"}\n");
        free(module);
        free(data);
        return 1;
    }

    /* 路由到对应模块 */
    char *result = NULL;

    if (strcmp(module, "linked_list") == 0) {
        result = linked_list_handle(action, data);
    } else if (strcmp(module, "queue") == 0) {
        result = queue_handle(action, data);
    } else if (strcmp(module, "binary_search") == 0) {
        result = binary_search_handle(action, data);
    } else if (strcmp(module, "stack") == 0) {
        /* 交棒：李恩琪+余欣泽 填充 */
        result = stack_handle ? stack_handle(action, data)
                 : strdup("{\"error\":\"stack module not yet implemented\"}");
    } else if (strcmp(module, "kmp") == 0) {
        result = kmp_handle ? kmp_handle(action, data)
                 : strdup("{\"error\":\"kmp module not yet implemented\"}");
    } else if (strcmp(module, "hash_table") == 0) {
        result = hash_table_handle ? hash_table_handle(action, data)
                 : strdup("{\"error\":\"hash_table module not yet implemented\"}");
    } else {
        size_t len = strlen(module) + 128;
        result = (char*) malloc(len);
        snprintf(result, len, "{\"error\":\"unknown module: %s\"}", module);
    }

    /* 输出最终 JSON */
    if (result) {
        printf("{\"status\":\"ok\",\"result\":%s}\n", result);
        free(result);
    } else {
        printf("{\"status\":\"error\",\"error\":\"module returned null\"}\n");
    }

    free(module);
    free(action);
    free(data);
    return 0;
}
