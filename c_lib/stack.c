/* stack.c —— 时间记录撤销/重做栈
 * 👤 陈+丁超轶 负责实现
 *
 * 支持操作：
 *   push      - 将记录压入撤销栈
 *   pop       - 从撤销栈弹出（执行撤销），自动压入重做栈
 *   redo_pop  - 从重做栈弹出（执行重做），自动压回撤销栈
 *   undo_size - 查看撤销栈大小
 *   redo_size - 查看重做栈大小
 *   clear     - 清空两个栈
 *
 * 协议：stdin/stdout JSON，由 main.c 统一路由
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "stack.h"

/* ========== 栈节点 ========== */
typedef struct StackNode {
    char *data;              /* 存储的 JSON 字符串 */
    struct StackNode *next;  /* 指向下一个节点 */
} StackNode;

/* ========== 双栈结构（撤销栈 + 重做栈）========== */
typedef struct {
    StackNode *undo_top;     /* 撤销栈顶 */
    StackNode *redo_top;     /* 重做栈顶 */
    int undo_size;           /* 撤销栈大小 */
    int redo_size;           /* 重做栈大小 */
} UndoRedoStack;

/* 全局单例 */
static UndoRedoStack g_stack = {NULL, NULL, 0, 0};

/* ========== 内部 JSON 辅助 ========== */

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

/* 提取嵌套的 data 对象 */
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
    return strdup(json);
}

/* ========== 栈操作 ========== */

/* 压入撤销栈 */
static int stack_push(const char *record_json) {
    if (!record_json) return -1;

    StackNode *node = (StackNode*) malloc(sizeof(StackNode));
    if (!node) return -1;

    node->data = strdup(record_json);
    if (!node->data) {
        free(node);
        return -1;
    }

    node->next = g_stack.undo_top;
    g_stack.undo_top = node;
    g_stack.undo_size++;

    /* 每次新操作后清空重做栈（符合标准 undo/redo 语义） */
    while (g_stack.redo_top) {
        StackNode *tmp = g_stack.redo_top;
        g_stack.redo_top = g_stack.redo_top->next;
        free(tmp->data);
        free(tmp);
    }
    g_stack.redo_size = 0;

    return g_stack.undo_size;
}

/* 从撤销栈弹出（执行撤销），返回弹出的 JSON */
static char* stack_pop(void) {
    if (!g_stack.undo_top) return NULL;

    StackNode *node = g_stack.undo_top;
    g_stack.undo_top = node->next;
    g_stack.undo_size--;

    /* 压入重做栈 */
    node->next = g_stack.redo_top;
    g_stack.redo_top = node;
    g_stack.redo_size++;

    /* 返回数据的副本（调用者负责释放） */
    return strdup(node->data);
}

/* 从重做栈弹出（执行重做），返回弹出的 JSON */
static char* stack_redo_pop(void) {
    if (!g_stack.redo_top) return NULL;

    StackNode *node = g_stack.redo_top;
    g_stack.redo_top = node->next;
    g_stack.redo_size--;

    /* 压回撤销栈 */
    node->next = g_stack.undo_top;
    g_stack.undo_top = node;
    g_stack.undo_size++;

    /* 返回数据的副本 */
    return strdup(node->data);
}

/* 查看撤销栈顶（不弹出） */
static char* stack_peek_undo(void) {
    if (!g_stack.undo_top) return NULL;
    return strdup(g_stack.undo_top->data);
}

/* 查看重做栈顶（不弹出） */
static char* stack_peek_redo(void) {
    if (!g_stack.redo_top) return NULL;
    return strdup(g_stack.redo_top->data);
}

/* 清空两个栈 */
static void stack_clear(void) {
    while (g_stack.undo_top) {
        StackNode *tmp = g_stack.undo_top;
        g_stack.undo_top = g_stack.undo_top->next;
        free(tmp->data);
        free(tmp);
    }
    while (g_stack.redo_top) {
        StackNode *tmp = g_stack.redo_top;
        g_stack.redo_top = g_stack.redo_top->next;
        free(tmp->data);
        free(tmp);
    }
    g_stack.undo_size = 0;
    g_stack.redo_size = 0;
}

/* ========== main.c 路由入口 ========== */

char* stack_handle(const char *action, const char *data_json) {
    if (!action) {
        return strdup("{\"error\":\"missing action\"}");
    }

    /* ---- push ---- */
    if (strcmp(action, "push") == 0) {
        char *record_data = json_extract_data_object(data_json);
        char *category = json_extract_string(record_data ? record_data : data_json, "category");
        char *description = json_extract_string(record_data ? record_data : data_json, "description");

        if (!category && !description) {
            /* 直接存储整个数据 */
            char *full_data = record_data ? record_data : (data_json ? strdup(data_json) : NULL);
            if (!full_data) {
                free(record_data);
                free(category);
                free(description);
                return strdup("{\"error\":\"no data to push\"}");
            }
            int size = stack_push(full_data);
            free(full_data);
            free(record_data);
            free(category);
            free(description);

            char buf[256];
            snprintf(buf, sizeof(buf),
                "{\"pushed\":true,\"undo_size\":%d,\"message\":\"record pushed to undo stack\"}", size);
            return strdup(buf);
        }

        /* 构建记录的 JSON */
        size_t len = 512;
        if (record_data) len += strlen(record_data);
        char *record_json = (char*) malloc(len);
        if (!record_json) {
            free(record_data); free(category); free(description);
            return strdup("{\"error\":\"memory allocation failed\"}");
        }

        if (record_data && category && description) {
            snprintf(record_json, len,
                "{\"category\":\"%s\",\"description\":\"%s\",\"full_data\":%s}",
                category, description, record_data);
        } else if (record_data) {
            snprintf(record_json, len, "%s", record_data);
        } else {
            snprintf(record_json, len,
                "{\"category\":\"%s\",\"description\":\"%s\"}",
                category ? category : "", description ? description : "");
        }

        int size = stack_push(record_json);
        free(record_json);
        free(record_data);
        free(category);
        free(description);

        char buf[256];
        snprintf(buf, sizeof(buf),
            "{\"pushed\":true,\"undo_size\":%d,\"redo_size\":%d,\"message\":\"record pushed to undo stack\"}",
            size, g_stack.redo_size);
        return strdup(buf);
    }

    /* ---- pop (undo) ---- */
    if (strcmp(action, "pop") == 0) {
        char *popped = stack_pop();
        if (!popped) {
            return strdup("{\"status\":\"ok\",\"result\":{\"undone\":false,\"error\":\"undo stack is empty\",\"undo_size\":0,\"redo_size\":0}}");
        }

        size_t len = strlen(popped) + 256;
        char *result = (char*) malloc(len);
        if (!result) {
            free(popped);
            return strdup("{\"error\":\"memory allocation failed\"}");
        }
        snprintf(result, len,
            "{\"undone\":true,\"record\":%s,\"undo_size\":%d,\"redo_size\":%d,\"message\":\"undo successful\"}",
            popped, g_stack.undo_size, g_stack.redo_size);
        free(popped);
        return result;
    }

    /* ---- redo_pop (redo) ---- */
    if (strcmp(action, "redo_pop") == 0) {
        char *redone = stack_redo_pop();
        if (!redone) {
            return strdup("{\"redone\":false,\"error\":\"redo stack is empty\",\"undo_size\":0,\"redo_size\":0}");
        }

        size_t len = strlen(redone) + 256;
        char *result = (char*) malloc(len);
        if (!result) {
            free(redone);
            return strdup("{\"error\":\"memory allocation failed\"}");
        }
        snprintf(result, len,
            "{\"redone\":true,\"record\":%s,\"undo_size\":%d,\"redo_size\":%d,\"message\":\"redo successful\"}",
            redone, g_stack.undo_size, g_stack.redo_size);
        free(redone);
        return result;
    }

    /* ---- peek_undo ---- */
    if (strcmp(action, "peek_undo") == 0) {
        char *top = stack_peek_undo();
        if (!top) {
            return strdup("{\"found\":false,\"undo_size\":0,\"redo_size\":0}");
        }
        size_t len = strlen(top) + 128;
        char *result = (char*) malloc(len);
        snprintf(result, len,
            "{\"found\":true,\"record\":%s,\"undo_size\":%d,\"redo_size\":%d}", top,
            g_stack.undo_size, g_stack.redo_size);
        free(top);
        return result;
    }

    /* ---- peek_redo ---- */
    if (strcmp(action, "peek_redo") == 0) {
        char *top = stack_peek_redo();
        if (!top) {
            return strdup("{\"found\":false,\"undo_size\":0,\"redo_size\":0}");
        }
        size_t len = strlen(top) + 128;
        char *result = (char*) malloc(len);
        snprintf(result, len,
            "{\"found\":true,\"record\":%s,\"undo_size\":%d,\"redo_size\":%d}", top,
            g_stack.undo_size, g_stack.redo_size);
        free(top);
        return result;
    }

    /* ---- undo_size ---- */
    if (strcmp(action, "undo_size") == 0 || strcmp(action, "size") == 0) {
        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"undo_size\":%d,\"redo_size\":%d}", g_stack.undo_size, g_stack.redo_size);
        return strdup(buf);
    }

    /* ---- clear ---- */
    if (strcmp(action, "clear") == 0) {
        int old_undo = g_stack.undo_size;
        int old_redo = g_stack.redo_size;
        stack_clear();
        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"cleared\":true,\"removed_undo\":%d,\"removed_redo\":%d,\"undo_size\":0,\"redo_size\":0}",
            old_undo, old_redo);
        return strdup(buf);
    }

    /* 未知操作 */
    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"error\":\"unknown stack action: %s\"}", action);
    return strdup(buf);
}
