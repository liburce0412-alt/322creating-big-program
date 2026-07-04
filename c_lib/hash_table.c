/*
 * hash_table.c —— 哈希表快速检索
 * 👤 李恩琪+余欣泽
 *
 * 采用链地址法（拉链法）处理冲突，djb2 哈希算法。
 * 支持 insert/search/delete/size/clear/keys/bulk_insert。
 *
 * 通信协议：hash_table_handle(action, data_json) -> strdup'd JSON string
 *   调用者负责 free() 返回值。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "hash_table.h"

/* ======================== 常量 ======================== */
#define INITIAL_CAPACITY 128
#define MAX_KEY_LEN      256
#define MAX_VALUE_LEN    4096

/* ======================== 内部数据结构 ======================== */

/* 哈希表节点（链表） */
typedef struct HTNode {
    char *key;                /* 键（strdup） */
    char *value;              /* 值 JSON 字符串（strdup） */
    struct HTNode *next;      /* 拉链指针 */
} HTNode;

/* 哈希表主体 */
typedef struct {
    HTNode **buckets;         /* 桶数组 */
    size_t capacity;          /* 桶数量 */
    size_t count;             /* 当前元素数 */
} HashTable;

static HashTable table = { NULL, 0, 0 }; /* 全局哈希表 */

/* ======================== 哈希函数 ======================== */

static size_t hash_djb2(const char *str) {
    unsigned long hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + (unsigned char)c; /* hash * 33 + c */
    }
    return (size_t)hash;
}

/* ======================== 内部操作 ======================== */

static void ht_init(void) {
    if (table.buckets != NULL) return;
    table.capacity = INITIAL_CAPACITY;
    table.count = 0;
    table.buckets = (HTNode**)calloc(table.capacity, sizeof(HTNode*));
}

static void ht_destroy(void) {
    if (!table.buckets) return;
    for (size_t i = 0; i < table.capacity; i++) {
        HTNode *node = table.buckets[i];
        while (node) {
            HTNode *next = node->next;
            free(node->key);
            free(node->value);
            free(node);
            node = next;
        }
    }
    free(table.buckets);
    table.buckets = NULL;
    table.capacity = 0;
    table.count = 0;
}

static HTNode* ht_find(const char *key) {
    if (!table.buckets || !key) return NULL;
    size_t idx = hash_djb2(key) % table.capacity;
    HTNode *node = table.buckets[idx];
    while (node) {
        if (strcmp(node->key, key) == 0) return node;
        node = node->next;
    }
    return NULL;
}

static int ht_insert(const char *key, const char *value) {
    if (!key || !table.buckets) return -1;
    ht_init();

    HTNode *existing = ht_find(key);
    if (existing) {
        /* 更新已有值 */
        free(existing->value);
        existing->value = strdup(value ? value : "null");
        return 0; /* 已更新 */
    }

    size_t idx = hash_djb2(key) % table.capacity;
    HTNode *new_node = (HTNode*)malloc(sizeof(HTNode));
    if (!new_node) return -1;
    new_node->key = strdup(key);
    new_node->value = strdup(value ? value : "null");
    new_node->next = table.buckets[idx];
    table.buckets[idx] = new_node;
    table.count++;
    return 1; /* 新增 */
}

static int ht_delete(const char *key) {
    if (!table.buckets || !key) return 0;
    size_t idx = hash_djb2(key) % table.capacity;
    HTNode *node = table.buckets[idx];
    HTNode *prev = NULL;

    while (node) {
        if (strcmp(node->key, key) == 0) {
            if (prev) {
                prev->next = node->next;
            } else {
                table.buckets[idx] = node->next;
            }
            free(node->key);
            free(node->value);
            free(node);
            table.count--;
            return 1;
        }
        prev = node;
        node = node->next;
    }
    return 0;
}

/* ======================== JSON 辅助 ======================== */

/* 从 JSON 字符串中提取指定 key 的字符串值（双引号内内容）
 * 返回 strdup 的字符串或 NULL */
static char* json_extract_string(const char *json, const char *key) {
    if (!json || !key) return NULL;
    char search[512];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return NULL;
    pos += strlen(search);
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t' || *pos == '\n' || *pos == '\r')) pos++;
    if (*pos != '"') return NULL;
    pos++;
    const char *end = pos;
    while (*end && *end != '"') {
        if (*end == '\\' && *(end+1)) end++;
        end++;
    }
    size_t len = end - pos;
    char *result = (char*)malloc(len + 1);
    if (!result) return NULL;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        if (pos[i] == '\\' && i + 1 < len) {
            i++;
            switch (pos[i]) {
                case 'n': result[j++] = '\n'; break;
                case 't': result[j++] = '\t'; break;
                case 'r': result[j++] = '\r'; break;
                case '"': result[j++] = '"';  break;
                case '\\': result[j++] = '\\'; break;
                default: result[j++] = pos[i]; break;
            }
        } else {
            result[j++] = pos[i];
        }
    }
    result[j] = '\0';
    return result;
}

/* 从 JSON 中提取整个 value 字段的 JSON 对象/数组字符串 */
static char* json_extract_value_json(const char *json) {
    if (!json) return NULL;
    /* 查找 "value": 后面的 { 或 [ */
    const char *pos = strstr(json, "\"value\"");
    if (!pos) return NULL;
    pos = strchr(pos, ':');
    if (!pos) return NULL;
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    if (*pos == '{' || *pos == '[') {
        char open = *pos;
        char close = (open == '{') ? '}' : ']';
        const char *start = pos;
        int depth = 0;
        while (*pos) {
            if (*pos == open) depth++;
            else if (*pos == close) {
                depth--;
                if (depth == 0) {
                    size_t len = pos - start + 1;
                    char *result = (char*)malloc(len + 1);
                    if (result) {
                        memcpy(result, start, len);
                        result[len] = '\0';
                    }
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
    }
    return NULL;
}

/* ======================== 对外接口 ======================== */

char* hash_table_handle(const char *action, const char *data_json) {
    if (!action) return strdup("{\"error\":\"missing action\"}");

    ht_init();

    /* --- insert --- */
    if (strcmp(action, "insert") == 0) {
        char *key = json_extract_string(data_json, "key");
        if (!key) return strdup("{\"error\":\"missing key\"}");
        char *value = json_extract_value_json(data_json);
        if (!value) {
            value = json_extract_string(data_json, "value");
        }
        int ret = ht_insert(key, value ? value : "null");
        free(key);
        free(value);

        char buf[256];
        if (ret == 1) {
            snprintf(buf, sizeof(buf),
                "{\"inserted\":true,\"updated\":false,\"size\":%zu}", table.count);
        } else if (ret == 0) {
            snprintf(buf, sizeof(buf),
                "{\"inserted\":false,\"updated\":true,\"size\":%zu}", table.count);
        } else {
            return strdup("{\"error\":\"insert failed\"}");
        }
        return strdup(buf);
    }

    /* --- search --- */
    if (strcmp(action, "search") == 0) {
        char *key = json_extract_string(data_json, "key");
        if (!key) return strdup("{\"error\":\"missing key\"}");

        HTNode *node = ht_find(key);
        free(key);

        if (node) {
            char buf[4096];
            snprintf(buf, sizeof(buf),
                "{\"found\":true,\"key\":\"%s\",\"value\":%s}",
                node->key, node->value);
            return strdup(buf);
        }
        return strdup("{\"found\":false}");
    }

    /* --- delete --- */
    if (strcmp(action, "delete") == 0) {
        char *key = json_extract_string(data_json, "key");
        if (!key) return strdup("{\"error\":\"missing key\"}");

        int deleted = ht_delete(key);
        free(key);

        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"deleted\":%s,\"size\":%zu}",
            deleted ? "true" : "false", table.count);
        return strdup(buf);
    }

    /* --- size --- */
    if (strcmp(action, "size") == 0) {
        char buf[64];
        snprintf(buf, sizeof(buf), "{\"size\":%zu}", table.count);
        return strdup(buf);
    }

    /* --- clear --- */
    if (strcmp(action, "clear") == 0) {
        size_t old_count = table.count;
        ht_destroy();
        ht_init();
        char buf[64];
        snprintf(buf, sizeof(buf), "{\"cleared\":true,\"previous_size\":%zu}", old_count);
        return strdup(buf);
    }

    /* --- keys --- */
    if (strcmp(action, "keys") == 0) {
        if (table.count == 0) {
            return strdup("{\"keys\":[]}");
        }
        /* 先计算总长度 */
        size_t total_len = 20; /* {"keys":[,]} */
        for (size_t i = 0; i < table.capacity; i++) {
            HTNode *node = table.buckets[i];
            while (node) {
                total_len += strlen(node->key) + 6; /* "key", */
                node = node->next;
            }
        }
        char *result = (char*)malloc(total_len + 10);
        if (!result) return strdup("{\"error\":\"memory error\"}");
        strcpy(result, "{\"keys\":[");
        int first = 1;
        for (size_t i = 0; i < table.capacity; i++) {
            HTNode *node = table.buckets[i];
            while (node) {
                if (!first) strcat(result, ",");
                strcat(result, "\"");
                strcat(result, node->key);
                strcat(result, "\"");
                first = 0;
                node = node->next;
            }
        }
        strcat(result, "]}");
        return result;
    }

    /* --- bulk_insert --- */
    if (strcmp(action, "bulk_insert") == 0) {
        if (!data_json) return strdup("{\"error\":\"no data\"}");
        /* 简化实现：只插入单个 insert 的数据
         * 更复杂的实现需要解析 JSON 数组 */
        char *key = json_extract_string(data_json, "key");
        char *value = json_extract_value_json(data_json);
        int count = 0;

        if (key) {
            int ret = ht_insert(key, value ? value : "null");
            if (ret > 0 || ret == 0) count = 1;
            free(key);
            free(value);
        }

        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"inserted\":%d,\"size\":%zu}", count, table.count);
        return strdup(buf);
    }

    /* --- 未知 action --- */
    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"error\":\"unknown hash_table action: %s\"}", action);
    return strdup(buf);
}
