#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "linked_list.h"

/* ========== 内部 JSON 辅助函数 ========== */

/* 简易 JSON 字符串转义（仅处理 " \ \n \r \t） */
static char* json_escape(const char *src) {
    if (!src) return NULL;
    size_t len = strlen(src);
    size_t cap = len * 2 + 4;
    char *dst = (char*) malloc(cap);
    if (!dst) return NULL;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        char c = src[i];
        switch (c) {
            case '"':  dst[j++] = '\\'; dst[j++] = '"';  break;
            case '\\': dst[j++] = '\\'; dst[j++] = '\\'; break;
            case '\n': dst[j++] = '\\'; dst[j++] = 'n';  break;
            case '\r': dst[j++] = '\\'; dst[j++] = 'r';  break;
            case '\t': dst[j++] = '\\'; dst[j++] = 't';  break;
            default:   dst[j++] = c; break;
        }
    }
    dst[j] = '\0';
    return dst;
}

/* 从 JSON 字符串中提取指定 key 的字符串值（简单版，仅支持 "key":"value"） */
static char* json_extract_string(const char *json, const char *key) {
    if (!json || !key) return NULL;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return NULL;
    pos += strlen(search);
    /* 跳过 : 和空白与引号 */
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    if (*pos != '"') return NULL;
    pos++;
    /* 找到结束引号 */
    const char *end = pos;
    while (*end && *end != '"') {
        if (*end == '\\' && *(end + 1)) end++; /* 跳过转义 */
        end++;
    }
    if (*end != '"') return NULL;
    size_t len = end - pos;
    /* 分配并拷贝（处理转义） */
    char *result = (char*) malloc(len + 1);
    if (!result) return NULL;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        if (pos[i] == '\\' && i + 1 < len) {
            i++;
            switch (pos[i]) {
                case 'n':  result[j++] = '\n'; break;
                case 'r':  result[j++] = '\r'; break;
                case 't':  result[j++] = '\t'; break;
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

/* 从 JSON 中提取整数 */
static int json_extract_int(const char *json, const char *key, int default_val) {
    if (!json || !key) return default_val;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return default_val;
    pos += strlen(search);
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    return atoi(pos);
}

/* 从 JSON 中提取长整数 */
static long long json_extract_long(const char *json, const char *key, long long default_val) {
    if (!json || !key) return default_val;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return default_val;
    pos += strlen(search);
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    return atoll(pos);
}

/* 提取嵌套的 data 对象字符串（返回 { ... } 部分） */
static char* json_extract_data_object(const char *json) {
    if (!json) return NULL;
    const char *pos = strstr(json, "\"data\"");
    if (!pos) return NULL;
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
    return NULL;
}

/* 拼接到动态字符串 */
static char* str_append(char *dst, size_t *cap, size_t *len, const char *src) {
    if (!src) return dst;
    size_t slen = strlen(src);
    if (*len + slen + 1 > *cap) {
        *cap = (*len + slen) * 2 + 64;
        char *tmp = (char*) realloc(dst, *cap);
        if (!tmp) { free(dst); return NULL; }
        dst = tmp;
    }
    memcpy(dst + *len, src, slen);
    *len += slen;
    dst[*len] = '\0';
    return dst;
}

static char* str_append_char(char *dst, size_t *cap, size_t *len, char c) {
    if (*len + 2 > *cap) {
        *cap = (*cap) * 2 + 16;
        char *tmp = (char*) realloc(dst, *cap);
        if (!tmp) { free(dst); return NULL; }
        dst = tmp;
    }
    dst[*len] = c;
    (*len)++;
    dst[*len] = '\0';
    return dst;
}

/* ========== 双向链表实现 ========== */

ChatList* chat_list_create(void) {
    ChatList *list = (ChatList*) malloc(sizeof(ChatList));
    if (!list) return NULL;
    list->head = NULL;
    list->tail = NULL;
    list->size = 0;
    list->next_id = 1;
    return list;
}

void chat_list_destroy(ChatList *list) {
    if (!list) return;
    chat_list_clear(list);
    free(list);
}

void chat_list_clear(ChatList *list) {
    if (!list) return;
    ChatNode *cur = list->head;
    while (cur) {
        ChatNode *next = cur->next;
        free(cur->content);
        free(cur);
        cur = next;
    }
    list->head = NULL;
    list->tail = NULL;
    list->size = 0;
}

int chat_list_append(ChatList *list, const char *role, const char *content, long long timestamp) {
    if (!list || !role || !content) return -1;
    ChatNode *node = (ChatNode*) malloc(sizeof(ChatNode));
    if (!node) return -1;
    node->id = list->next_id++;
    strncpy(node->role, role, sizeof(node->role) - 1);
    node->role[sizeof(node->role) - 1] = '\0';
    node->content = strdup(content);
    node->timestamp = timestamp;
    node->prev = list->tail;
    node->next = NULL;
    if (list->tail) {
        list->tail->next = node;
    } else {
        list->head = node;
    }
    list->tail = node;
    list->size++;
    return node->id;
}

int chat_list_prepend(ChatList *list, const char *role, const char *content, long long timestamp) {
    if (!list || !role || !content) return -1;
    ChatNode *node = (ChatNode*) malloc(sizeof(ChatNode));
    if (!node) return -1;
    node->id = list->next_id++;
    strncpy(node->role, role, sizeof(node->role) - 1);
    node->role[sizeof(node->role) - 1] = '\0';
    node->content = strdup(content);
    node->timestamp = timestamp;
    node->prev = NULL;
    node->next = list->head;
    if (list->head) {
        list->head->prev = node;
    } else {
        list->tail = node;
    }
    list->head = node;
    list->size++;
    return node->id;
}

int chat_list_delete_by_id(ChatList *list, int id) {
    if (!list) return 0;
    ChatNode *cur = list->head;
    while (cur) {
        if (cur->id == id) {
            if (cur->prev) cur->prev->next = cur->next;
            else list->head = cur->next;
            if (cur->next) cur->next->prev = cur->prev;
            else list->tail = cur->prev;
            free(cur->content);
            free(cur);
            list->size--;
            return 1;
        }
        cur = cur->next;
    }
    return 0;
}

ChatNode* chat_list_find_by_id(ChatList *list, int id) {
    if (!list) return NULL;
    ChatNode *cur = list->head;
    while (cur) {
        if (cur->id == id) return cur;
        cur = cur->next;
    }
    return NULL;
}

int chat_list_size(const ChatList *list) {
    return list ? list->size : 0;
}

char* chat_list_to_json(const ChatList *list) {
    if (!list) return strdup("[]");
    size_t cap = 4096;
    size_t len = 0;
    char *json = (char*) malloc(cap);
    if (!json) return NULL;
    json[0] = '\0';

    json = str_append_char(json, &cap, &len, '[');
    if (!json) return NULL;

    ChatNode *cur = list->head;
    int first = 1;
    while (cur) {
        char buf[1024];
        char *esc = json_escape(cur->content);
        if (!esc) { free(json); return NULL; }
        snprintf(buf, sizeof(buf),
            "%s{\"id\":%d,\"role\":\"%s\",\"content\":\"%s\",\"timestamp\":%lld}",
            first ? "" : ",", cur->id, cur->role, esc, cur->timestamp);
        free(esc);
        json = str_append(json, &cap, &len, buf);
        if (!json) return NULL;
        first = 0;
        cur = cur->next;
    }
    json = str_append_char(json, &cap, &len, ']');
    return json;
}

int chat_list_from_json(ChatList *list, const char *json) {
    if (!list || !json) return 0;
    chat_list_clear(list);

    /* 找到数组起始 */
    const char *arr = strchr(json, '[');
    if (!arr) return 0;
    arr++;

    int count = 0;
    const char *p = arr;
    while (*p) {
        /* 跳到下一个对象 */
        while (*p && *p != '{' && *p != ']') p++;
        if (*p == ']' || *p == '\0') break;

        /* 提取这个对象 */
        const char *obj_start = p;
        int depth = 0;
        while (*p) {
            if (*p == '{') depth++;
            else if (*p == '}') {
                depth--;
                if (depth == 0) { p++; break; }
            } else if (*p == '"') {
                p++;
                while (*p && *p != '"') {
                    if (*p == '\\') p++;
                    if (*p) p++;
                }
            }
            p++;
        }

        /* 解析对象字段 */
        char *role = json_extract_string(obj_start, "role");
        char *content = json_extract_string(obj_start, "content");
        long long ts = json_extract_long(obj_start, "timestamp", 0);

        if (role && content) {
            chat_list_append(list, role, content, ts);
            count++;
        }
        free(role);
        free(content);
    }
    return count;
}

/* ========== main.c 路由入口 ========== */

char* linked_list_handle(const char *action, const char *data_json) {
    /* 全局单例 —— 保存对话历史 */
    static ChatList *list = NULL;
    if (!list) list = chat_list_create();

    if (!action) {
        return strdup("{\"error\":\"missing action\"}");
    }

    if (strcmp(action, "append") == 0) {
        char *role = json_extract_string(data_json, "role");
        char *content = json_extract_string(data_json, "content");
        long long ts = json_extract_long(data_json, "timestamp", (long long) time(NULL));
        if (!role || !content) {
            free(role); free(content);
            return strdup("{\"error\":\"role and content required\"}");
        }
        int id = chat_list_append(list, role, content, ts);
        free(role); free(content);
        char buf[256];
        snprintf(buf, sizeof(buf),
            "{\"id\":%d,\"size\":%d,\"message\":\"message appended\"}", id, list->size);
        return strdup(buf);
    }

    if (strcmp(action, "prepend") == 0) {
        char *role = json_extract_string(data_json, "role");
        char *content = json_extract_string(data_json, "content");
        long long ts = json_extract_long(data_json, "timestamp", (long long) time(NULL));
        if (!role || !content) {
            free(role); free(content);
            return strdup("{\"error\":\"role and content required\"}");
        }
        int id = chat_list_prepend(list, role, content, ts);
        free(role); free(content);
        char buf[256];
        snprintf(buf, sizeof(buf),
            "{\"id\":%d,\"size\":%d,\"message\":\"message prepended\"}", id, list->size);
        return strdup(buf);
    }

    if (strcmp(action, "delete") == 0) {
        int id = json_extract_int(data_json, "id", -1);
        int ok = chat_list_delete_by_id(list, id);
        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"deleted\":%s,\"id\":%d,\"size\":%d}",
            ok ? "true" : "false", id, list->size);
        return strdup(buf);
    }

    if (strcmp(action, "find") == 0) {
        int id = json_extract_int(data_json, "id", -1);
        ChatNode *node = chat_list_find_by_id(list, id);
        if (!node) return strdup("{\"found\":false}");
        char *esc = json_escape(node->content);
        char buf[2048];
        snprintf(buf, sizeof(buf),
            "{\"found\":true,\"id\":%d,\"role\":\"%s\",\"content\":\"%s\",\"timestamp\":%lld}",
            node->id, node->role, esc ? esc : "", node->timestamp);
        free(esc);
        return strdup(buf);
    }

    if (strcmp(action, "to_array") == 0) {
        return chat_list_to_json(list);
    }

    if (strcmp(action, "from_array") == 0) {
        int count = chat_list_from_json(list, data_json);
        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"imported\":%d,\"size\":%d}", count, list->size);
        return strdup(buf);
    }

    if (strcmp(action, "clear") == 0) {
        chat_list_clear(list);
        return strdup("{\"cleared\":true,\"size\":0}");
    }

    if (strcmp(action, "size") == 0) {
        char buf[64];
        snprintf(buf, sizeof(buf), "{\"size\":%d}", list->size);
        return strdup(buf);
    }

    /* 未知操作 */
    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"error\":\"unknown action: %s\"}", action);
    return strdup(buf);
}
